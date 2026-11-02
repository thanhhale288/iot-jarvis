"""A6: TTS edge-tts → phát loa. Text hiển thị và audio dùng cùng một chuỗi đã chuẩn hóa."""

from __future__ import annotations

import asyncio
import os
import queue
import re
import subprocess
import tempfile
import threading
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

TTS_VOICE = os.getenv("TTS_VOICE", "vi-VN-HoaiMyNeural")
# +0% — khớp nhịp nói tự nhiên với câu Jarvis ngắn
TTS_RATE = os.getenv("TTS_RATE", "+0%")


def for_speech(text: str) -> str:
    """Chuẩn hóa để edge-tts đọc sát chữ trên UI (cùng nội dung)."""
    s = (text or "").strip()
    if not s:
        return ""
    s = s.replace("°C", " độ C").replace("℃", " độ C")
    s = s.replace("%", " phần trăm")
    # 28.4 → 28 phẩy 4 (tránh đọc kiểu Anh)
    s = re.sub(r"(\d+)\.(\d+)", r"\1 phẩy \2", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


async def _synth_to_file(text: str, path: Path, voice: str, rate: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(str(path))


def synthesize(
    text: str,
    path: str | Path,
    *,
    voice: str | None = None,
    rate: str | None = None,
    normalize: bool = True,
) -> Path:
    out = Path(path)
    spoken = for_speech(text) if normalize else (text or "").strip()
    if not spoken:
        raise ValueError("empty TTS text")
    asyncio.run(
        _synth_to_file(
            spoken,
            out,
            voice or TTS_VOICE,
            rate or TTS_RATE,
        )
    )
    return out


def play_file(path: str | Path) -> None:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)
    if Path("/usr/bin/afplay").exists():
        subprocess.run(["afplay", str(p)], check=False)
    else:
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(p)],
            check=False,
        )


def speak(text: str, *, voice: str | None = None, rate: str | None = None) -> str:
    """A6: text → synth → play. Trả về chuỗi đã nói (khớp audio)."""
    spoken = for_speech(text)
    if not spoken:
        return ""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        path = Path(tmp.name)
    try:
        synthesize(spoken, path, voice=voice, rate=rate, normalize=False)
        play_file(path)
    finally:
        path.unlink(missing_ok=True)
    return spoken


class StreamingSpeaker:
    """Hàng đợi câu TTS. Nên submit đúng chuỗi sẽ hiện trên UI."""

    def __init__(self, *, voice: str | None = None, rate: str | None = None) -> None:
        self.voice = voice or TTS_VOICE
        self.rate = rate or TTS_RATE
        self._q: queue.Queue[str | None] = queue.Queue()
        self._thread: threading.Thread | None = None
        self.first_audio_at: float | None = None
        self.spoken_parts: list[str] = []

    def start(self, t0_wall: float | None = None) -> None:
        import time

        del t0_wall
        self.first_audio_at = None
        self.spoken_parts = []
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def submit(self, sentence: str) -> None:
        s = for_speech(sentence)
        if s:
            self._q.put(s)

    def close(self) -> None:
        self._q.put(None)
        if self._thread:
            self._thread.join(timeout=120)

    def _worker(self) -> None:
        import time

        while True:
            item = self._q.get()
            if item is None:
                break
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                path = Path(tmp.name)
            try:
                synthesize(item, path, voice=self.voice, rate=self.rate, normalize=False)
                self.spoken_parts.append(item)
                if self.first_audio_at is None:
                    self.first_audio_at = time.time()
                play_file(path)
            except Exception as e:
                print(f"[tts] error: {e}", flush=True)
            finally:
                path.unlink(missing_ok=True)
