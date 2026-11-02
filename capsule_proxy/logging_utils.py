import json
import shlex
import threading
from pathlib import Path

from .config import REDACT_SENSITIVE_HEADERS, SENSITIVE_HEADERS

_LOG_LOCK = threading.Lock()


def append_jsonl(filename, record):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    with _LOG_LOCK, path.open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")


def safe_headers(headers):
    result = {}
    for key, value in headers.items():
        if REDACT_SENSITIVE_HEADERS and key.lower() in SENSITIVE_HEADERS:
            result[key] = "[REDACTED]"
        else:
            result[key] = str(value)[:1000]
    return result


def make_curl(method, url, headers, body_file=None):
    """Build a curl command using a saved request body file."""
    parts = ["curl", "-i", "-X", shlex.quote(method)]

    excluded = {
        "host", "content-length", "connection", "transfer-encoding",
        "keep-alive", "proxy-connection", "upgrade",
    }

    for name, value in headers.items():
        lower = name.lower()
        if lower in excluded:
            continue

        if REDACT_SENSITIVE_HEADERS and lower in SENSITIVE_HEADERS:
            value = "[REDACTED]"

        parts.extend(["-H", shlex.quote(f"{name}: {value}")])

    parts.extend(["--url", shlex.quote(url)])

    if body_file is not None:
        parts.extend(["--data-binary", shlex.quote(f"@{body_file}")])

    return " ".join(parts)