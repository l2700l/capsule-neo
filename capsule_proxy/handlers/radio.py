
import threading
import time

from ..config import MP3_DIR


_RADIO_DIR = MP3_DIR
_LOCK = threading.Lock()
_FILES = None


def get_files():
    """Возвращает отсортированный список MP3-файлов."""
    global _FILES

    with _LOCK:
        if _FILES is None:
            _FILES = sorted(
                (
                    path
                    for path in _RADIO_DIR.iterdir()
                    if path.is_file() and path.suffix.lower() == ".mp3"
                ),
                key=lambda path: path.name.lower(),
            ) if _RADIO_DIR.is_dir() else []

        return list(_FILES)


def serve_test_radio(handler):
    """Передаёт MP3-файлы по кругу в одном HTTP-соединении."""
    files = get_files()

    if not files:
        handler.send_error(404, "No MP3 files found in radio directory")
        return

    handler.send_response(200)
    handler.send_header("Content-Type", "audio/mpeg")
    handler.send_header("Transfer-Encoding", "chunked")
    handler.send_header("Accept-Ranges", "none")
    handler.send_header("Connection", "close")
    handler.end_headers()

    handler.close_connection = True

    index = 0
    total_bytes = 0

    try:
        while True:
            path = files[index]
            index = (index + 1) % len(files)
            file_bytes = 0

            with path.open("rb") as stream:
                while True:
                    chunk = stream.read(16 * 1024)
                    if not chunk:
                        break

                    # Формат HTTP chunked:
                    # размер блока в hex + CRLF + данные + CRLF
                    handler.wfile.write(f"{len(chunk):X}\r\n".encode("ascii"))
                    handler.wfile.write(chunk)
                    handler.wfile.write(b"\r\n")
                    handler.wfile.flush()

                    file_bytes += len(chunk)
                    total_bytes += len(chunk)

    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as exc:
        print(f"client disconnected: {exc}")
