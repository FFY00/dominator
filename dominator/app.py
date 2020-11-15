#!/usr/bin/env python3

import os
import tempfile

import webruntime

import dominator


class DominatorApp():
    def __init__(self) -> None:
        self._dom = dominator.Dominator()
        self._runtime = None
        self.body = ''

    def __del__(self) -> None:
        self.close()

    @property
    def dom(self) -> dominator.Dominator:
        return self._dom

    def run(self) -> None:
        # put the application HTML in a temporary file
        self._html = tempfile.NamedTemporaryFile(
            mode='w+',
            prefix='my-app-',
            suffix='.html',
            delete=False,
        )
        self._html.write(self.body)
        self._html.close()
        # launch the application HTML file
        self._runtime = webruntime.launch(f'file://{self._html.name}', 'app')
        self._dom.wait_for_connection()

    def close(self) -> None:
        if self._runtime:
            self._runtime.close()
        os.unlink(self._html.name)
