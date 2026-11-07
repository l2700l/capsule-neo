from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import device, logs, timezone, settings, websocket, phrase, stream
from state import DeviceState
from config import TIMEZONE_NAME
from web_socket.server import websocket_server


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.device_state = DeviceState(
        TIMEZONE_NAME,
        storage_path="device_state.json",
    )

    app.state.websocket_server = websocket_server

    await websocket_server.start()

    yield

    try:
        app.state.device_state.save()
    finally:
        await websocket_server.stop()


app = FastAPI(lifespan=lifespan)

app.include_router(device.router)
app.include_router(logs.router)
app.include_router(timezone.router)
app.include_router(settings.router)
app.include_router(websocket.router)
app.include_router(phrase.router)
app.include_router(stream.router)