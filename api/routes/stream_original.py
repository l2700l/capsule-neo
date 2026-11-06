
import asyncio
import json
import queue
import threading
import uuid

from datetime import datetime, timezone
from functools import partial

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool

from config import (
    UPSTREAM_HOST,
    UPSTREAM_IP,
    STREAM_CAPTURE_DIR,
)
from utils.logging_utils import safe_headers
from utils.upstream import (
    DirectHTTPSConnection,
    filtered_headers,
)


router = APIRouter()


STREAM_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
}


def create_capture_dir():
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S_%fZ"
    )

    path = STREAM_CAPTURE_DIR / (
        f"{timestamp}_{uuid.uuid4().hex[:8]}"
    )

    path.mkdir(parents=True, exist_ok=True)

    return path


def get_upstream_path(request: Request):
    path = request.url.path

    if request.url.query:
        path += f"?{request.url.query}"

    return path


def get_client_ip(request: Request):
    return request.client.host if request.client else None


def write_json(path, data):
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )


@router.get("/stream")
async def proxy_stream(request: Request):
    capture_dir = create_capture_dir()

    upstream_path = get_upstream_path(request)

    request_headers = filtered_headers(
        request.headers,
        STREAM_HOP_BY_HOP | {"content-length"},
    )

    write_json(
        capture_dir / "request.json",
        {
            "time": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": upstream_path,
            "client_ip": get_client_ip(request),
            "headers": safe_headers(request.headers),
            "upstream": f"https://{UPSTREAM_HOST}{upstream_path}",
        },
    )

    chunks = queue.Queue(maxsize=8)
    stop_event = threading.Event()

    record = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": None,
        "headers": [],
        "body_bytes": 0,
        "completed": False,
    }

    state = {
        "error": None,
        "response_headers": [],
    }

    def worker():
        conn = DirectHTTPSConnection(
            UPSTREAM_HOST,
            UPSTREAM_IP,
            timeout=60,
        )

        received = 0

        try:
            conn.request(
                "GET",
                upstream_path,
                headers=request_headers,
            )

            upstream = conn.getresponse()

            record["status"] = upstream.status
            record["reason"] = upstream.reason
            record["headers"] = upstream.getheaders()

            state["response_headers"] = upstream.getheaders()

            with (
                capture_dir / "response_body.bin"
            ).open("wb") as body_file:

                while not stop_event.is_set():
                    chunk = upstream.read1(8192)

                    if not chunk:
                        record["completed"] = True
                        break

                    body_file.write(chunk)
                    body_file.flush()

                    received += len(chunk)

                    # Ограниченная очередь обеспечивает backpressure.
                    while not stop_event.is_set():
                        try:
                            chunks.put(chunk, timeout=0.2)
                            break
                        except queue.Full:
                            continue

        except Exception as exc:
            state["error"] = repr(exc)
            print(f"[STREAM PROXY ERROR] {exc!r}")

        finally:
            record["body_bytes"] = received
            record["finished_at"] = datetime.now(
                timezone.utc
            ).isoformat()

            write_json(
                capture_dir / "response.json",
                record,
            )

            conn.close()

            # Сообщаем асинхронному генератору о завершении.
            while not stop_event.is_set():
                try:
                    chunks.put(None, timeout=0.2)
                    break
                except queue.Full:
                    continue

    worker_thread = threading.Thread(
        target=worker,
        daemon=True,
    )

    worker_thread.start()

    # Ждём только получения заголовков upstream.
    # Чтение тела уже выполняется параллельно.
    while (
        record["status"] is None
        and state["error"] is None
    ):
        await asyncio.sleep(0.01)

    if state["error"] is not None:
        stop_event.set()
        await run_in_threadpool(worker_thread.join)

        return JSONResponse(
            content={
                "error": "stream_proxy_error",
                "qid": uuid.uuid4().hex,
            },
            status_code=502,
        )

    response_headers = [
        (name, value)
        for name, value in state["response_headers"]
        if name.lower() not in STREAM_HOP_BY_HOP
    ]

    async def stream_body():
        try:
            while True:
                try:
                    chunk = await asyncio.to_thread(
                        chunks.get,
                        True,
                        0.2,
                    )
                except queue.Empty:
                    if not worker_thread.is_alive():
                        break
                    continue

                if chunk is None:
                    break

                yield chunk

        finally:
            stop_event.set()
            await asyncio.to_thread(worker_thread.join)

            print(
                f"[STREAM] {upstream_path} -> "
                f"{record['status']}, "
                f"{record['body_bytes']} bytes captured "
                f"in {capture_dir}"
            )

    response = StreamingResponse(
        stream_body(),
        status_code=record["status"],
    )

    response.raw_headers = [
        (name.encode("latin-1"), value.encode("latin-1"))
        for name, value in response_headers
    ]

    return response
