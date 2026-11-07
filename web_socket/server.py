
import asyncio
import json
import logging
import uuid

from datetime import datetime, timezone

from websockets.asyncio.server import serve

from config import HOST, WEBSOCKET_PORT, WEBSOCKET_MAX_MESSAGE


logger = logging.getLogger(__name__)


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


class WebSocketServer:

    def __init__(self):
        self.clients = set()
        self.stop_event = None
        self.server_task = None
        self.server_ready = asyncio.Event()

    async def handler(self, ws):
        """Обрабатывает WebSocket-подключение колонки."""
        client = str(ws.remote_address)

        self.clients.add(ws)

        log_event(
            "client_connected",
            client=client,
            clients=len(self.clients),
            path=ws.request.path,
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
            self.clients.discard(ws)

            log_event(
                "client_disconnected",
                client=client,
                clients=len(self.clients),
            )

    async def send_ping(self):
        """Отправляет бинарный пакет всем подключённым колонкам."""
        active_clients = list(self.clients)

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
            *(ws.send(payload) for ws in active_clients),
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

    async def _run(self):
        """Основной цикл WebSocket-сервера."""
        try:
            async with serve(
                self.handler,
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

                self.server_ready.set()

                await self.stop_event.wait()

        except Exception:
            logger.exception("WebSocket server failed")
            raise

        finally:
            self.server_ready.set()
            log_event("server_stopped")

    async def start(self):
        """Запускает WebSocket-сервер."""
        if (
            self.server_task is not None
            and not self.server_task.done()
        ):
            return

        self.server_ready.clear()
        self.stop_event = asyncio.Event()

        self.server_task = asyncio.create_task(
            self._run(),
            name="websocket-server",
        )

        try:
            await asyncio.wait_for(
                self.server_ready.wait(),
                timeout=5,
            )

            if self.server_task.done():
                await self.server_task

        except asyncio.TimeoutError:
            await self.stop()
            raise RuntimeError(
                "WebSocket server did not start within 5 seconds"
            )

    async def stop(self):
        """Останавливает WebSocket-сервер."""
        if self.stop_event is not None:
            self.stop_event.set()

        if self.server_task is not None:
            try:
                await asyncio.wait_for(
                    self.server_task,
                    timeout=5,
                )
            except asyncio.TimeoutError:
                self.server_task.cancel()

                await asyncio.gather(
                    self.server_task,
                    return_exceptions=True,
                )

        self.server_task = None
        self.stop_event = None


websocket_server = WebSocketServer()
