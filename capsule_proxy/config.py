import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_DIR / ".env"

load_dotenv(ENV_FILE)

HOST = os.getenv("CAPSULE_HOST", "0.0.0.0")
PORT = int(os.getenv("CAPSULE_PORT", "8082"))
UPSTREAM_HOST = os.getenv("CAPSULE_UPSTREAM_HOST", "vc.go.mail.ru")
UPSTREAM_IP = os.getenv("CAPSULE_UPSTREAM_IP", "vc.go.mail.ru")
MAX_BODY = int(os.getenv("CAPSULE_MAX_BODY", str(64 * 1024)))

KNOWN_LOG = Path(os.getenv("CAPSULE_KNOWN_LOG", "capsule_known_requests.jsonl"))
UNKNOWN_LOG = Path(os.getenv("CAPSULE_UNKNOWN_LOG", "capsule_unknown_requests.jsonl"))
CAPTURE_DIR = Path(os.getenv("CAPSULE_CAPTURE_DIR", "captures"))
STREAM_CAPTURE_DIR = Path(os.getenv("CAPSULE_STREAM_CAPTURE_DIR", "captures_stream"))
PROJECT_DIR = Path(__file__).resolve().parent.parent
MP3_DIR = Path(str(PROJECT_DIR / os.getenv("CAPSULE_MP3_DIR", "radio")))
TIMEZONE_NAME = Path(os.getenv("TIMEZONE_NAME", "Europe/Moscow"))

# для отображения кредов - установить в значении 0
REDACT_SENSITIVE_HEADERS = os.getenv(
    "CAPSULE_REDACT_SENSITIVE_HEADERS", "1"
).strip().lower() not in {"0", "false", "no", "off"}

SENSITIVE_HEADERS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-csrf-protection",
    "x-super-token",
}

LOCAL_RADIO_URL = os.getenv(
    "CAPSULE_LOCAL_RADIO_URL",
    "https://vc.go.mail.ru/radio.mp3",
)
RADIO_URL_PATTERN = (
    r"https?://rusradio\.hostingradio\.ru/rusradio128\.mp3"
    r"(?:\\?radiostatistica=VKMarusya)?"
)
