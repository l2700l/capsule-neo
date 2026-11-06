
import json
import re
import uuid

from datetime import datetime, timezone
from functools import partial

from starlette.concurrency import run_in_threadpool
from fastapi import APIRouter, Request
from fastapi.responses import Response, JSONResponse

from config import (
    UPSTREAM_HOST,
    UPSTREAM_IP,
    CAPTURE_DIR,
    LOCAL_RADIO_URL,
    RADIO_URL_PATTERN,
)
from utils.logging_utils import safe_headers
from utils.upstream import DirectHTTPSConnection, filtered_headers


router = APIRouter()


HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "proxy-connection",
    "content-length",
    "host",
    "expect",
}

RADIO_URL_RE = re.compile(RADIO_URL_PATTERN)


def replace_radio_urls(value):
    if isinstance(value, dict):
        return {
            key: replace_radio_urls(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            replace_radio_urls(item)
            for item in value
        ]

    if isinstance(value, str):
        return RADIO_URL_RE.sub(LOCAL_RADIO_URL, value)

    return value


def create_capture_dir():
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S.%fZ"
    )

    path = CAPTURE_DIR / f"{timestamp}_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)

    return path


def get_client_ip(request: Request):
    return request.client.host if request.client else None


def get_upstream_path(request: Request):
    path = request.url.path

    if request.url.query:
        path += f"?{request.url.query}"

    return path


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


def proxy_phrase_create_sync(
    method,
    path,
    body,
    headers,
    client_ip,
    capture_dir,
):
    request_id = capture_dir.name.rsplit("_", 1)[-1]

    (capture_dir / "request_body.bin").write_bytes(body)

    write_json(
        capture_dir / "request.json",
        {
            "id": request_id,
            "time": datetime.now(timezone.utc).isoformat(),
            "client_ip": client_ip,
            "method": method,
            "url": f"https://{UPSTREAM_HOST}{path}",
            "headers": safe_headers(headers),
            "body_bytes": len(body),
        },
    )

    request_headers = filtered_headers(
        headers,
        HOP_BY_HOP,
    )

    conn = DirectHTTPSConnection(
        UPSTREAM_HOST,
        UPSTREAM_IP,
        timeout=90,
    )

    try:
        conn.request(
            method,
            path,
            body=body,
            headers=request_headers,
        )

        upstream = conn.getresponse()
        response_body = upstream.read()
        response_headers = upstream.getheaders()

        (capture_dir / "response_body.bin").write_bytes(
            response_body
        )

        content_type = next(
            (
                value
                for name, value in response_headers
                if name.lower() == "content-type"
            ),
            "",
        )

        text_body = None

        if any(
            kind in content_type.lower()
            for kind in ("text/", "json", "xml")
        ):
            text_body = response_body.decode(
                "utf-8",
                errors="replace",
            )

        write_json(
            capture_dir / "response.json",
            {
                "id": request_id,
                "status": upstream.status,
                "reason": upstream.reason,
                "headers": response_headers,
                "body_bytes": len(response_body),
                "body_text": text_body,
            },
        )

        response_headers = [
            (name, value)
            for name, value in response_headers
            if name.lower() not in HOP_BY_HOP
        ]

        return Response(
            content=response_body,
            status_code=upstream.status,
            headers=dict(response_headers),
        )

    except Exception as exc:
        write_json(
            capture_dir / "error.json",
            {
                "id": request_id,
                "error": repr(exc),
            },
        )

        print(
            f"[PHRASE PROXY ERROR] {path}: {exc!r}"
        )

        return JSONResponse(
            content={"error": "upstream_proxy_error"},
            status_code=502,
        )

    finally:
        conn.close()


def proxy_phrase_result_sync(
    path,
    headers,
    capture_dir,
):
    request_id = capture_dir.name.rsplit("_", 1)[-1]

    request_headers = filtered_headers(
        headers,
        HOP_BY_HOP,
    )

    conn = DirectHTTPSConnection(
        UPSTREAM_HOST,
        UPSTREAM_IP,
        timeout=90,
    )

    try:
        conn.request(
            "GET",
            path,
            headers=request_headers,
        )

        upstream = conn.getresponse()
        original_body = upstream.read()
        response_headers = upstream.getheaders()

        (capture_dir / "response_original.bin").write_bytes(
            original_body
        )

        content_type = next(
            (
                value
                for name, value in response_headers
                if name.lower() == "content-type"
            ),
            "application/json",
        )

        payload = json.loads(original_body)

        # Оставлено для последующей подмены ссылок,
        # если она понадобится в оригинальном режиме.
        # payload = replace_radio_urls(payload)

        print(payload)

        response_body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        (capture_dir / "response_body.bin").write_bytes(
            response_body
        )

        write_json(
            capture_dir / "response.json",
            {
                "id": request_id,
                "status": upstream.status,
                "reason": upstream.reason,
                "headers": response_headers,
                "body_bytes": len(response_body),
            },
        )

        response_headers = [
            (name, value)
            for name, value in response_headers
            if name.lower() not in HOP_BY_HOP
            and name.lower() != "content-encoding"
        ]

        response_headers.append(
            ("Content-Type", content_type)
        )

        return Response(
            content=response_body,
            status_code=upstream.status,
            headers=dict(response_headers),
        )

    except Exception as exc:
        write_json(
            capture_dir / "error.json",
            {
                "id": request_id,
                "error": repr(exc),
            },
        )

        print(
            f"[PHRASE RESULT ERROR] {path}: {exc!r}"
        )

        return JSONResponse(
            content={"error": "phrase_result_proxy_error"},
            status_code=502,
        )

    finally:
        conn.close()


@router.post("/phrase/create")
@router.post("/phrase/create/{path:path}")
@router.post("/phrase/add")
@router.post("/phrase/add/{path:path}")
async def proxy_phrase_create(request: Request, path: str = ""):
    capture_dir = create_capture_dir()

    body = await request.body()
    upstream_path = get_upstream_path(request)

    return await run_in_threadpool(
        partial(
            proxy_phrase_create_sync,
            request.method,
            upstream_path,
            body,
            request.headers,
            get_client_ip(request),
            capture_dir,
        )
    )


@router.get("/phrase/result")
async def proxy_phrase_result(request: Request):
    capture_dir = create_capture_dir()

    upstream_path = get_upstream_path(request)

    return await run_in_threadpool(
        partial(
            proxy_phrase_result_sync,
            upstream_path,
            request.headers,
            capture_dir,
        )
    )
