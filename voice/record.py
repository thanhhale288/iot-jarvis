"""Ghi mic mono 16 kHz — cố định giây hoặc cắt khi im lặng (giảm latency)."""

from __future__ import annotations

import os
import time

import numpy as np

SAMPLE_RATE = 16_000
SILENCE_RMS = float(os.getenv("STT_SILENCE_RMS", "0.012"))
SILENCE_MS = int(os.getenv("STT_SILENCE_MS", "600"))
MAX_SECONDS = float(os.getenv("STT_MAX_SECONDS", "8"))
MIN_SECONDS = float(os.getenv("STT_MIN_SECONDS", "0.6"))


def record_seconds(seconds: float = 4.0, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Ghi `seconds` từ mic mặc định → float32 mono [-1, 1]."""
    import sounddevice as sd

    if seconds <= 0:
        raise ValueError("seconds must be > 0")
    frames = int(seconds * sample_rate)
    print(f"[stt] recording {seconds:.1f}s @ {sample_rate} Hz …", flush=True)
    audio = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    print("[stt] recording done", flush=True)
    return np.asarray(audio, dtype=np.float32).reshape(-1)


def record_until_silence(
    *,
    sample_rate: int = SAMPLE_RATE,
    max_seconds: float = MAX_SECONDS,
    min_seconds: float = MIN_SECONDS,
    silence_rms: float = SILENCE_RMS,
    silence_ms: int = SILENCE_MS,
) -> np.ndarray:
    """Ghi đến khi im ~silence_ms (sau min_seconds) hoặc hết max_seconds."""
    import sounddevice as sd

    block = int(0.05 * sample_rate)
    need_silent = max(1, int(silence_ms / 50))
    chunks: list[np.ndarray] = []
    silent_run = 0
    started_voice = False
    t0 = time.time()
    print(
        f"[stt] recording until silence "
        f"(max {max_seconds:.0f}s, silence {silence_ms}ms)…",
        flush=True,
    )
    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        blocksize=block,
    ) as stream:
        while True:
            data, _overflowed = stream.read(block)
            mono = np.asarray(data[:, 0], dtype=np.float32)
            chunks.append(mono)
            rms = float(np.sqrt(np.mean(mono * mono)) if mono.size else 0.0)
            elapsed = time.time() - t0
            if rms >= silence_rms:
                started_voice = True
                silent_run = 0
            elif started_voice and elapsed >= min_seconds:
                silent_run += 1
                if silent_run >= need_silent:
                    break
            if elapsed >= max_seconds:
                break
    print(f"[stt] recording done ({time.time() - t0:.2f}s)", flush=True)
    if not chunks:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(chunks).astype(np.float32)
