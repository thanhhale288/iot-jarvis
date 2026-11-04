"""C3 — Wake “Hey Jarvis” rồi chạy pipeline.

Mặc định: ghi ngắn + Whisper (model nhỏ) tìm cụm jarvis.
Tuỳ chọn: WAKE_BACKEND=openwakeword + WAKE_MODEL=path nếu có model riêng.

Chạy: python -m voice.wake
"""

from __future__ import annotations

import os
import re
import sys
import time

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice.record import SAMPLE_RATE, record_seconds  # noqa: E402
from voice.stt import FasterWhisperSTT  # noqa: E402

WAKE_PHRASE_RE = re.compile(
    r"\b(hey\s+)?jarvis\b|\bhei\s+jarvis\b|\bjavis\b",
    re.IGNORECASE,
)
WAKE_CHUNK_S = float(os.getenv("WAKE_CHUNK_S", "2.0"))
WAKE_MODEL = os.getenv("WAKE_STT_MODEL", "tiny")
WAKE_BACKEND = os.getenv("WAKE_BACKEND", "stt").strip().lower()
WAKE_COOLDOWN_S = float(os.getenv("WAKE_COOLDOWN_S", "4"))


def _heard_wake(text: str) -> bool:
    return bool(WAKE_PHRASE_RE.search(text or ""))


def _wait_openwakeword() -> None:
    """Optional path — cần file model .onnx và package openwakeword."""
    import numpy as np
    import sounddevice as sd
    from openwakeword.model import Model

    model_path = os.getenv("WAKE_MODEL", "").strip()
    if not model_path:
        raise RuntimeError("WAKE_BACKEND=openwakeword cần WAKE_MODEL=/path/model.onnx")
    ow = Model(wakeword_models=[model_path], inference_framework="onnx")
    threshold = float(os.getenv("WAKE_OWW_THRESHOLD", "0.5"))
    block = int(0.08 * SAMPLE_RATE)
    print(f"[wake] openWakeWord model={model_path} thr={threshold}")
    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=block
    ) as stream:
        while True:
            data, _ = stream.read(block)
            mono = np.asarray(data[:, 0], dtype=np.float32)
            # openwakeword expects int16 PCM chunks
            pcm = (mono * 32767.0).astype(np.int16)
            preds = ow.predict(pcm)
            for _name, score in preds.items():
                if float(score) >= threshold:
                    print(f"[wake] detected score={score:.2f}")
                    return


def _wait_stt(stt: FasterWhisperSTT) -> str:
    print(f"[wake] listening for Hey Jarvis (chunk {WAKE_CHUNK_S:.1f}s)…")
    while True:
        samples = record_seconds(WAKE_CHUNK_S)
        # bỏ đoạn quá im
        if samples.size == 0 or float(abs(samples).mean()) < 0.001:
            continue
        text = stt.transcribe(samples, language="vi", beam_size=1, vad_filter=False)
        text = (text or "").strip()
        if text:
            print(f"[wake] heard: {text}")
        if _heard_wake(text):
            return text


def main(argv: list[str] | None = None) -> int:
    del argv
    once = os.getenv("WAKE_ONCE", "0").strip() in ("1", "true", "yes")
    print(f"WAKE_BACKEND={WAKE_BACKEND} once={once}")

    stt: FasterWhisperSTT | None = None
    if WAKE_BACKEND != "openwakeword":
        stt = FasterWhisperSTT(model_size=WAKE_MODEL, language="vi")

    while True:
        try:
            if WAKE_BACKEND == "openwakeword":
                _wait_openwakeword()
                heard = "hey jarvis"
            else:
                assert stt is not None
                heard = _wait_stt(stt)
        except KeyboardInterrupt:
            print("\nstop")
            return 0
        except Exception as e:
            print(f"[wake] error: {e}", file=sys.stderr)
            return 1

        print(f"[wake] → pipeline (from: {heard})")
        try:
            from voice.pipeline import run_pipeline

            # Sau wake: ghi lệnh đến im lặng
            timings = run_pipeline(text=None)
            print(timings.summary())
            if timings.assistant_text:
                print(f"assistant: {timings.assistant_text}")
        except Exception as e:
            print(f"[wake] pipeline error: {e}", file=sys.stderr)

        if once:
            return 0
        time.sleep(WAKE_COOLDOWN_S)


if __name__ == "__main__":
    raise SystemExit(main())
