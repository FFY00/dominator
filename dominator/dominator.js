const uri = '@DOMINATOR-URI@';
var socket = new WebSocket(uri);

window.addEventListener('beforeunload', function(){
    socket.close();
});

socket.addEventListener('message', function (event) {
    var data = JSON.parse(event.data);
    switch (data.operation) {
        case 'get_value':
            socket.send(JSON.stringify(
                getObject(data.object),
            ));
            break;
        case 'set_value':
            console.log(data)
            console.log(getObject(data.object)[data.name])
            getObject(data.object)[data.name] = data.value;
            console.log(getObject(data.object)[data.name])
            break;
        case 'get_properties':
            socket.send(JSON.stringify(
                getObjectProperties(getObject(data.object))
            ));
            break;
    }
});

function getObject(details) {
    switch (details.origin_operation) {
        case 'get_element_by_id':
            return getChild(
                document.getElementById(details.origin_value),
                details.path,
            );
    }
}

function getObjectProperties(obj) {
    var properties = [];
    for (var prop in obj)
        properties.push(prop);
    return properties;
}

function getChild(obj, path) {
    var child = obj;
    for (var node in path) {
        child = child[path[node]];
    }
    return child;
}
