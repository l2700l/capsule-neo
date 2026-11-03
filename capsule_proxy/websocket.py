
import asyncio
import json
import logging
import threading
import uuid

from concurrent.futures import TimeoutError as FutureTimeout
from datetime import datetime, timezone

from websockets.asyncio.server import serve

from .config import HOST, WEBSOCKET_PORT, WEBSOCKET_MAX_MESSAGE


logger = logging.getLogger(__name__)


# Подключённые колонки
clients = set()

# События и состояние фонового сервера
event_loop = None
stop_event = None
server_ready = threading.Event()
server_thread = None
server_error = None

# Первые 16 байт исследованного пакета
PING_PREFIX = bytes.fromhex(
    "00000008000000000000000000000000"
)


def log_event(event, **data):
    """Записывает событие в JSON-формате."""
    record = {
        "time": datetime.now(timezone.utc).isoformat(),
        "protocol": "websocket",
        "event": event,
        **data,
    }

    logger.info(
        json.dumps(record, ensure_ascii=False, default=str)
    )


async def handler(ws):
    """Обрабатывает WebSocket-подключение колонки."""
    client = str(ws.remote_address)

    clients.add(ws)

    log_event(
        "client_connected",
        client=client,
        clients=len(clients),
        path=getattr(ws, "path", None),
    )

    try:
        async for message in ws:
            if isinstance(message, bytes):
                log_event(
                    "message_received",
                    client=client,
                    message_type="binary",
                    length=len(message),
                    hex=message.hex(),
                )
            else:
                log_event(
                    "message_received",
                    client=client,
                    message_type="text",
                    length=len(message),
                    data=message,
                )

    except Exception as exc:
        log_event(
            "client_error",
            client=client,
            error=repr(exc),
        )

    finally:
        clients.discard(ws)

        log_event(
            "client_disconnected",
            client=client,
            clients=len(clients),
        )


async def send_ping():
    """
    Отправляет колонкам бинарный пакет-триггер.

    UUID передаётся в бинарном виде, а не как текст.
    """
    active_clients = [
        ws for ws in clients if not ws.closed
    ]

    if not active_clients:
        return {
            "ok": False,
            "error": "no_connected_clients",
            "clients": 0,
            "sent": 0,
            "failed": 0,
        }

    generated_uuid = uuid.uuid4()
    payload = PING_PREFIX + generated_uuid.bytes

    results = await asyncio.gather(
        *(
            ws.send(payload)
            for ws in active_clients
        ),
        return_exceptions=True,
    )

    sent = sum(
        not isinstance(result, Exception)
        for result in results
    )

    failed = len(results) - sent

    response = {
        "ok": failed == 0,
        "uuid": str(generated_uuid),
        "payload_hex": payload.hex(),
        "payload_length": len(payload),
        "clients": len(active_clients),
        "sent": sent,
        "failed": failed,
    }

    log_event("ping_sent", **response)

    return response


def send_ping_from_api():
    """
    Синхронный интерфейс для HTTP-обработчика.

    HTTP-сервер работает в другом потоке, поэтому отправку
    пакета передаём в event loop WebSocket-сервера.
    """
    loop = event_loop

    if loop is None or not loop.is_running():
        return {
            "ok": False,
            "error": "websocket_server_not_running",
        }

    try:
        future = asyncio.run_coroutine_threadsafe(
            send_ping(),
            loop,
        )

        return future.result(timeout=5)

    except FutureTimeout:
        logger.exception("Timed out while sending WebSocket packet")

        return {
            "ok": False,
            "error": "send_timeout",
        }

    except Exception as exc:
        logger.exception("Failed to send WebSocket packet")

        return {
            "ok": False,
            "error": "send_failed",
            "details": str(exc),
        }


async def _run_server():
    """Запускает WebSocket-сервер и ждёт остановки."""
    global event_loop, stop_event, server_error

    event_loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    try:
        async with serve(
            handler,
            HOST,
            WEBSOCKET_PORT,
            ping_interval=None,
            compression=None,
            max_size=WEBSOCKET_MAX_MESSAGE,
        ):
            log_event(
                "server_started",
                host=HOST,
                port=WEBSOCKET_PORT,
            )

            server_ready.set()

            await stop_event.wait()

    except Exception as exc:
        server_error = exc
        logger.exception("WebSocket server failed")
        raise

    finally:
        server_ready.set()
        event_loop = None
        stop_event = None

        log_event("server_stopped")


def _background_main():
    """Точка входа для фонового потока."""
    global server_error

    try:
        asyncio.run(_run_server())
    except Exception as exc:
        server_error = exc
        logger.exception("WebSocket background thread stopped")


def start_background():
    """Запускает WebSocket-сервер в фоновом потоке."""
    global server_thread, server_error

    if server_thread is not None and server_thread.is_alive():
        return

    server_ready.clear()
    server_error = None

    server_thread = threading.Thread(
        target=_background_main,
        name="websocket-server",
        daemon=True,
    )
    server_thread.start()

    if not server_ready.wait(timeout=5):
        raise RuntimeError(
            "WebSocket server did not start within 5 seconds"
        )

    if server_error is not None:
        raise RuntimeError(
            f"WebSocket server failed to start: {server_error}"
        )


async def _stop_server():
    """Просит фоновый сервер завершиться."""
    if stop_event is not None:
        stop_event.set()


def stop_background():
    """Останавливает фоновый WebSocket-сервер."""
    loop = event_loop
    thread = server_thread

    if loop is not None and loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(
                _stop_server(),
                loop,
            ).result(timeout=5)
        except Exception:
            logger.exception("Error while stopping WebSocket server")

    if thread is not None and thread.is_alive():
        thread.join(timeout=5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(_run_server())
    except KeyboardInterrupt:
        pass
