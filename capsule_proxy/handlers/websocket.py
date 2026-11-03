from .. import websocket


def send_websocket_ping(handler, body):
    result = websocket.send_ping_from_api()

    if result["ok"]:
        return 200, result, "json"

    if result.get("error") == "no_connected_clients":
        return 409, result, "json"

    return 503, result, "json"