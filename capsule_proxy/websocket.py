
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import msgpack
from websockets.asyncio.server import serve
from websockets.http11 import Request

from .config import HOST


PORT = int(os.getenv("CAPSULE_WEBSOCKET_PORT", "8083"))
MAX_MESSAGE = 1024 * 1024
LOG_FILE = Path("capsule_websocket.jsonl")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return record.getMessage()


logger = logging.getLogger("capsule_proxy.websocket")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    formatter = JsonFormatter()

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def log_event(event, **fields):
    record = {
        "time": datetime.now(timezone.utc).isoformat(),
        "protocol": "websocket",
        "event": event,
        **fields,
    }
    logger.info(json.dumps(record, ensure_ascii=False, default=str))


def decode_message(message):
    if isinstance(message, str):
        try:
            return {"format": "json", "data": json.loads(message)}
        except json.JSONDecodeError:
            return {"format": "text", "data": message}

    try:
        return {
            "format": "msgpack",
            "data": msgpack.unpackb(
                message,
                raw=False,
                strict_map_key=False,
            ),
        }
    except Exception:
        try:
            return {
                "format": "json",
                "data": json.loads(message.decode("utf-8")),
            }
        except (ValueError, UnicodeDecodeError):
            return {
                "format": "binary",
                "raw_hex": message[:256].hex(),
                "length": len(message),
            }


async def process_request(connection, request: Request):
    # Не выводим все заголовки в открытый лог:
    # среди них могут оказаться токены и cookies.
    log_event(
        "handshake",
        client=str(connection.remote_address),
        path=request.path,
        headers={
            key: value
            for key, value in request.headers.items()
            if key.lower() not in {"authorization", "cookie", "set-cookie"}
        },
    )
    return None


async def handler(ws):
    remote = str(ws.remote_address)
    path = ws.request.path

    log_event(
        "connected",
        client=remote,
        path=path,
    )

    try:
        async for message in ws:
            size = (
                len(message.encode("utf-8"))
                if isinstance(message, str)
                else len(message)
            )

            log_event(
                "message",
                client=remote,
                path=path,
                direction="client_to_server",
                message_bytes=size,
                body=decode_message(message),
            )

            # Пока не отправляем фиктивные ответы:
            # формат ожидаемых серверных сообщений ещё не установлен.

    except asyncio.CancelledError:
        raise
    except Exception as exc:
        log_event(
            "error",
            client=remote,
            path=path,
            error=str(exc),
        )
    finally:
        log_event(
            "disconnected",
            client=remote,
            path=path,
            close_code=ws.close_code,
            close_reason=ws.close_reason,
        )


async def main():
    async with serve(
        handler,
        HOST,
        PORT,
        max_size=MAX_MESSAGE,
        process_request=process_request,
        ping_interval=20,
        ping_timeout=20,
    ):
        print(f"WebSocket listening on ws://{HOST}:{PORT}")
        print(f"Log file: {LOG_FILE.resolve()}")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping WebSocket server")
