
import json
import uuid

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from fastapi import APIRouter, Request
from fastapi.responses import Response

from config import ASSISTANT_URL, CAPTURE_DIR
from utils.logging_utils import safe_headers
from utils.responses import json_response


router = APIRouter()


def create_capture_dir():
    """Создаёт каталог для захвата запроса."""
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S.%fZ"
    )

    path = CAPTURE_DIR / f"{timestamp}_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)

    return path


def get_assistant_url(request: Request):
    """Формирует URL запроса к собственному ассистенту."""
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


@router.api_route(
    "/phrase/{path:path}",
    methods=["GET", "POST"],
)
async def proxy_phrase(request: Request, path: str):
    """Проксирует запросы phrase на собственный ассистент."""

    capture_dir = create_capture_dir()
    request_id = capture_dir.name.rsplit("_", 1)[-1]

    body = await request.body()
    target_url = get_assistant_url(request)

    client_ip = (
        request.client.host
        if request.client
        else None
    )

    request_headers = dict(request.headers)

    # Заголовки, которые HTTP-клиент должен сформировать самостоятельно.
    for header in (
        "host",
        "content-length",
        "connection",
        "transfer-encoding",
    ):
        request_headers.pop(header, None)

    try:
        if body:
            (capture_dir / "request_body.bin").write_bytes(body)

        (capture_dir / "request.json").write_text(
            json.dumps(
                {
                    "id": request_id,
                    "time": datetime.now(timezone.utc).isoformat(),
                    "client_ip": client_ip,
                    "method": request.method,
                    "url": target_url,
                    "headers": safe_headers(request.headers),
                    "body_bytes": len(body),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        async with httpx.AsyncClient(timeout=90) as client:
            upstream = await client.request(
                method=request.method,
                url=target_url,
                content=body,
                headers=request_headers,
            )

        response_body = upstream.content

        content_type = upstream.headers.get(
            "content-type",
            "application/json",
        )

        # Обработка JSON-ответа phrase/result.
        if (
            request.method == "GET"
            and request.url.path == "/phrase/result"
            and "json" in content_type.lower()
        ):
            try:
                payload = json.loads(response_body)

                response_body = json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")

                (
                    capture_dir / "response_modified.json"
                ).write_text(
                    json.dumps(
                        payload,
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

            except (
                json.JSONDecodeError,
                UnicodeDecodeError,
            ):
                pass

        (capture_dir / "response_body.bin").write_bytes(
            response_body
        )

        response_headers = list(upstream.headers.multi_items())

        (capture_dir / "response.json").write_text(
            json.dumps(
                {
                    "id": request_id,
                    "status": upstream.status_code,
                    "reason": upstream.reason_phrase,
                    "headers": response_headers,
                    "body_bytes": len(response_body),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        # Не передаём hop-by-hop заголовки.
        excluded_headers = {
            "connection",
            "keep-alive",
            "transfer-encoding",
            "content-length",
            "content-encoding",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailers",
            "upgrade",
        }

        headers = {
            key: value
            for key, value in upstream.headers.items()
            if key.lower() not in excluded_headers
        }

        print(
            f"[ASSISTANT PROXY] {request.url.path} -> "
            f"{upstream.status_code}, capture={capture_dir}"
        )

        return Response(
            content=response_body,
            status_code=upstream.status_code,
            headers=headers,
        )

    except Exception as exc:
        (capture_dir / "error.json").write_text(
            json.dumps(
                {
                    "id": request_id,
                    "error": repr(exc),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            f"[ASSISTANT PROXY ERROR] "
            f"{request.url.path}: {exc!r}"
        )

        return json_response(
            {"error": "assistant_proxy_error"},
            status_code=502,
        )
