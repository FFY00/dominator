from __future__ import annotations

import json
import os.path
import random
import threading
import time
import typing
import uuid

from typing import Any, Awaitable, Dict, List, Optional, Union

import tornado.web
import tornado.websocket


# over-engineered because of tornado API limitations :/
# tornado isn't the best tool for this


class _DominatorSocket(tornado.websocket.WebSocketHandler):
    owner: Optional[Dominator] = None

    def check_origin(self, origin: str) -> bool:
        return True

    def on_message(self, message: Union[str, bytes]) -> Optional[Awaitable[None]]:
        for pool in self.recv_pools.values():
            pool.append(message)
        return None

    def open(self, *args: Any, **kwargs: Any) -> Optional[Awaitable[None]]:
        if self.owner:
            self.owner._handler = self
        self.recv_pools = getattr(self, 'recv_pools', {})
        return None


class JavascriptProxy():
    def __init__(
        self,
        origin_operation: str,
        origin_value: str,
        path: Optional[List[str]] = None,
        *,
        dom: Dominator,
    ) -> None:
        self._origin_operation = origin_operation
        self._origin_value = origin_value
        self._path = path or []
        self._dom = dom

    @property
    def _dominator_object(self) -> Dict[str, Any]:
        return {
            'origin_operation': self._origin_operation,
            'origin_value': self._origin_value,
            'path': self._path,
        }

    def _child(self, *args: str) -> JavascriptProxy:
        return self.__class__(
            self._origin_operation,
            self._origin_value,
            self._path + list(args),
            dom=self._dom,
        )

    def __repr__(self) -> str:
        args = [
            self._origin_operation,
            self._origin_value,
        ]
        if self._path:
            args.append('.'.join(self._path))
        return 'JavascriptProxy({})'.format(', '.join(args))

    def __getitem__(self, name: str) -> Any:
        if name in self._dom._get_properties(self):
            return self._child(name)
        raise IndexError(f'Unknown property: {name}')

    @property
    def value(self) -> Any:
        return self._dom._get_value(self)

    @value.setter
    def value(self, val: Any) -> None:
        self._dom._set_value(self, val)


class Dominator():
    def __init__(self, port: Optional[int] = None) -> None:
        self._js_file = os.path.abspath(os.path.join(__file__, '..', 'dominator.js'))

        self._handler: Optional[_DominatorSocket] = None
        self._address = '127.0.0.1'

        if port:
            self._port = port
            self._start_server()
        else:
            # try to find a port we can bind to
            while True:
                self._port = port or random.randint(9000, 60000)
                try:
                    self._start_server()
                except OSError:
                    pass
                else:
                    break

    def _start_server(self) -> None:
        _DominatorSocket.owner = self
        application = tornado.web.Application([
            (r'/', _DominatorSocket),
        ])
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(self._port)
        self._server_thread = threading.Thread(target=tornado.ioloop.IOLoop.current().start)
        self._server_thread.start()

    @property
    def uri(self) -> str:
        return f'ws://{self._address}:{self._port}'

    @property
    def javascript(self) -> str:
        with open(self._js_file) as f:
            return f.read().replace('@DOMINATOR-URI@', self.uri)

    def wait_for_connection(self) -> None:
        while not self._handler:
            time.sleep(0.05)

    def _receive(self, timeout: int = 3) -> Union[str, bytes]:
        pool: List[Union[str, bytes]] = []

        assert self._handler
        pid = uuid.uuid4().int
        self._handler.recv_pools[pid] = pool

        end_time = time.time() + timeout
        while not pool:
            time.sleep(0.05)
            if time.time() >= end_time:
                raise RuntimeError('timeout')

        del self._handler.recv_pools[pid]
        return pool.pop()

    def _send(self, data: Dict[str, Any], _count: int = 1) -> Any:
        assert self._handler
        if _count > 10:
            raise RuntimeError('Lost connection to the DOM!')
        # send data, try resending if there are any issues
        try:
            self._handler.write_message(json.dumps(data))
        except tornado.websocket.WebSocketClosedError:
            return self._send(data, _count)

    def _exchange(self, data: Dict[str, Any], _count: int = 1) -> Any:
        assert self._handler
        if _count > 10:
            raise RuntimeError('Lost connection to the DOM!')
        # send data, try resending if there are any issues
        try:
            self._handler.write_message(json.dumps(data))
        except tornado.websocket.WebSocketClosedError:
            return self._exchange(data, _count)
        # receive data, restart the exchange if there are any issues
        try:
            return json.loads(self._receive())
        except RuntimeError:
            return self._exchange(data, _count)

    def _get_value(self, obj: JavascriptProxy) -> Any:
        return self._exchange({
            'operation': 'get_value',
            'object': obj._dominator_object,
        })

    def _set_value(self, obj: JavascriptProxy, val: Any) -> None:
        obj_desc = obj._dominator_object
        name = obj_desc['path'].pop()
        self._send({
            'operation': 'set_value',
            'object': obj_desc,
            'name': name,
            'value': val,
        })

    def _get_properties(self, obj: JavascriptProxy) -> List[str]:
        return typing.cast(List[str], self._exchange({
            'operation': 'get_properties',
            'object': obj._dominator_object,
        }))

    def get_element_by_id(self, id: str) -> JavascriptProxy:
        return JavascriptProxy('get_element_by_id', id, dom=self)
