
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_DIR / ".env")


# HTTP server

HOST = os.getenv("CAPSULE_HOST", "0.0.0.0")
PORT = int(os.getenv("CAPSULE_PORT", "8082"))


# Original VK server

UPSTREAM_HOST = os.getenv(
    "CAPSULE_UPSTREAM_HOST",
    "vc.go.mail.ru",
)

UPSTREAM_IP = os.getenv(
    "CAPSULE_UPSTREAM_IP",
    UPSTREAM_HOST,
)


# Assistant server

ASSISTANT_URL = os.getenv(
    "ASSISTANT_URL",
    "http://localhost:8090",
)


# WebSocket

WEBSOCKET_PORT = int(
    os.getenv("CAPSULE_WEBSOCKET_PORT", "8083")
)

WEBSOCKET_MAX_MESSAGE = int(
    os.getenv("CAPSULE_WEBSOCKET_MAX_MESSAGE", str(1024 * 1024))
)


# Device

TIMEZONE_NAME = os.getenv(
    "TIMEZONE_NAME",
    "Europe/Moscow",
)


# Captures

CAPTURE_DIR = Path(
    os.getenv("CAPSULE_CAPTURE_DIR", PROJECT_DIR / "captures")
)

STREAM_CAPTURE_DIR = Path(
    os.getenv(
        "CAPSULE_STREAM_CAPTURE_DIR",
        PROJECT_DIR / "captures_stream",
    )
)


# Logging

KNOWN_LOG = Path(
    os.getenv(
        "CAPSULE_KNOWN_LOG",
        PROJECT_DIR / "capsule_known_requests.jsonl",
    )
)

UNKNOWN_LOG = Path(
    os.getenv(
        "CAPSULE_UNKNOWN_LOG",
        PROJECT_DIR / "capsule_unknown_requests.jsonl",
    )
)


# Sensitive headers

REDACT_SENSITIVE_HEADERS = os.getenv(
    "CAPSULE_REDACT_SENSITIVE_HEADERS",
    "1",
).strip().lower() not in {"0", "false", "no", "off"}

SENSITIVE_HEADERS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-csrf-protection",
    "x-super-token",
}
