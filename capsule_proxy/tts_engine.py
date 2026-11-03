
from __future__ import annotations

import subprocess
import tempfile
import threading
import wave
from pathlib import Path

import numpy as np
import torch

PROJECT_DIR = Path(__file__).resolve().parent.parent

SAMPLE_RATE = 48000
SPEAKER = "kseniya"
DEFAULT_SPEED = 1.2

torch.set_num_threads(4)

_model = None
_model_lock = threading.Lock()
_synthesis_lock = threading.Lock()


def _get_model():
    global _model

    if _model is None:
        with _model_lock:
            if _model is None:
                model, _ = torch.hub.load(
                    repo_or_dir="snakers4/silero-models",
                    model="silero_tts",
                    language="ru",
                    speaker="v5_6_ru",
                    trust_repo=True
                )
                model.to(torch.device("cpu"))
                _model = model

    return _model


def generate_audio(
    text: str,
    *,
    encoder: str = "opus",
    encoder_bitrate: int | None = None,
    encoder_frame_size: int | None = None,
    model_name: str | None = None,
    speed: float = DEFAULT_SPEED,
    normalize: bool = True,
) -> bytes:
    if not text.strip():
        raise ValueError("TTS text is empty")

    if not 0.5 <= speed <= 2.0:
        raise ValueError("speed must be between 0.5 and 2.0")

    model = _get_model()

    with _synthesis_lock:
        audio = model.apply_tts(
            text=text,
            speaker=SPEAKER,
            sample_rate=SAMPLE_RATE,
            put_accent=True,
            put_yo=True,
            put_stress_homo=True,
            put_yo_homo=True,
        )

    samples = audio.detach().cpu().numpy().reshape(-1).astype(np.float32)

    if normalize and samples.size:
        peak = float(np.max(np.abs(samples)))
        if peak > 1e-7:
            samples = samples / peak * 0.95

    pcm = (
        np.clip(samples, -1.0, 1.0) * 32767
    ).astype(np.int16)

    with tempfile.TemporaryDirectory(prefix="capsule-tts-") as tmp:
        tmp = Path(tmp)
        wav_path = tmp / "speech.wav"
        ogg_path = tmp / "speech.ogg"

        with wave.open(str(wav_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(pcm.tobytes())

        codec = "libopus" if encoder == "opus" else encoder
        bitrate = encoder_bitrate or 32

        ffmpeg_args = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(wav_path),
            "-c:a", codec,
            "-b:a", f"{bitrate}k",
            "-f", "ogg",
            str(ogg_path),
        ]

        if encoder == "opus":
            ffmpeg_args[ffmpeg_args.index("-f"):ffmpeg_args.index("-f")] = [
                "-application", "voip"
            ]

        subprocess.run(
            ffmpeg_args,
            check=True,
            capture_output=True,
        )

        return ogg_path.read_bytes()
