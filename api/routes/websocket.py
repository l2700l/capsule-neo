
from fastapi import APIRouter, Request

from utils.responses import json_response


router = APIRouter()


@router.post("/websocket/ping")
async def send_websocket_ping(request: Request):
    websocket_server = request.app.state.websocket_server

    result = await websocket_server.send_ping()

    if result["ok"]:
        status_code = 200
    elif result.get("error") == "no_connected_clients":
        status_code = 409
    else:
        status_code = 503

    return json_response(
        result,
        status_code=status_code,
    )
