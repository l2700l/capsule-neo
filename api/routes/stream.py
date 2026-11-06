
import json
import uuid

from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from config import ASSISTANT_URL, STREAM_CAPTURE_DIR
from utils.logging_utils import safe_headers


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
    """Создаёт каталог для захвата аудиопотока."""
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S_%fZ"
    )

    path = STREAM_CAPTURE_DIR / (
        f"{timestamp}_{uuid.uuid4().hex[:8]}"
    )

    path.mkdir(parents=True, exist_ok=True)

    return path


def get_assistant_url(request: Request):
    """Формирует URL запроса к ассистенту."""
    target = urlsplit(ASSISTANT_URL)

    if not target.hostname:
        raise ValueError(
            f"Invalid ASSISTANT_URL: {ASSISTANT_URL}"
        )

    base_path = target.path.rstrip("/")
    path = base_path + request.url.path

    url = f"{target.scheme}://{target.netloc}{path}"

    if request.url.query:
        url += f"?{request.url.query}"

    return url


def filter_request_headers(headers):
    """Удаляет hop-by-hop заголовки."""
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in STREAM_HOP_BY_HOP
        and key.lower() != "content-length"
    }


@router.get("/stream")
async def proxy_stream(request: Request):
    """Проксирует аудиопоток с ассистента на колонку."""

    capture_dir = create_capture_dir()
    target_url = get_assistant_url(request)

    request_headers = filter_request_headers(
        request.headers
    )

    (capture_dir / "request.json").write_text(
        json.dumps(
            {
                "time": datetime.now(timezone.utc).isoformat(),
                "method": request.method,
                "path": request.url.path,
                "headers": safe_headers(request.headers),
                "upstream": target_url,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    record = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": None,
        "headers": [],
        "body_bytes": 0,
        "completed": False,
    }

    client = httpx.AsyncClient(
        timeout=httpx.Timeout(90),
    )

    try:
        upstream = await client.send(
            client.build_request(
                "GET",
                target_url,
                headers=request_headers,
            ),
            stream=True,
        )

    except Exception as exc:
        record["error"] = repr(exc)
        record["finished_at"] = datetime.now(timezone.utc).isoformat()

        (capture_dir / "response.json").write_text(
            json.dumps(
                record,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        await client.aclose()

        print(f"[STREAM PROXY ERROR] {exc!r}")

        return JSONResponse(
            content={
                "error": "stream_proxy_error",
                "qid": uuid.uuid4().hex,
            },
            status_code=502,
        )

    record["status"] = upstream.status_code
    record["reason"] = upstream.reason_phrase
    record["headers"] = list(upstream.headers.multi_items())

    async def stream_body():
        received = 0

        try:
            with (
                capture_dir / "response_body.bin"
            ).open("wb") as body_file:

                async for chunk in upstream.aiter_raw(
                    chunk_size=8192
                ):
                    body_file.write(chunk)
                    body_file.flush()

                    received += len(chunk)

                    yield chunk

            record["completed"] = True

        except Exception as exc:
            record["error"] = repr(exc)
            print(f"[STREAM PROXY ERROR] {exc!r}")

        finally:
            record["body_bytes"] = received
            record["finished_at"] = datetime.now(
                timezone.utc
            ).isoformat()

            (capture_dir / "response.json").write_text(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            await upstream.aclose()
            await client.aclose()

            print(
                f"[STREAM] {request.url.path} -> "
                f"{record['status']}, {received} bytes "
                f"captured in {capture_dir}"
            )

    response = StreamingResponse(
        stream_body(),
        status_code=upstream.status_code,
    )

    # Сохраняем исходные заголовки, включая повторяющиеся.
    # Не передаём hop-by-hop заголовки.
    response.raw_headers = [
        (name, value)
        for name, value in upstream.headers.raw
        if name.decode("latin-1").lower()
        not in STREAM_HOP_BY_HOP
    ]

    return response
