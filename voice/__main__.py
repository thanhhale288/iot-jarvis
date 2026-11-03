"""python -m voice — A5 STT tiếng Việt.

Không arg: ghi mic rồi nhận dạng.
Arg đường dẫn: nhận dạng file audio (.wav/.mp3/…).
"""

from __future__ import annotations

import argparse
import os
import sys

# Cho phép chạy từ repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice.record import record_seconds, record_until_silence
from voice.stt import (
    STT_BEAM,
    STT_COMPUTE_TYPE,
    STT_DEVICE,
    STT_LANGUAGE,
    STT_MODEL,
    FasterWhisperSTT,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="A5 STT — faster-whisper, mặc định tiếng Việt")
    p.add_argument(
        "audio",
        nargs="?",
        help="File audio (bỏ trống = ghi mic đến im lặng)",
    )
    p.add_argument(
        "--seconds",
        type=float,
        default=None,
        help="Nếu set: ghi đúng N giây (không dùng cắt im lặng)",
    )
    p.add_argument(
        "--language",
        default=STT_LANGUAGE,
        help='Mã ngôn ngữ Whisper (mặc định "vi")',
    )
    p.add_argument("--model", default=STT_MODEL, help="Model size, vd base/small")
    args = p.parse_args(argv)

    print(f"STT_MODEL={args.model}")
    print(f"STT_LANGUAGE={args.language}")
    print(f"STT_BEAM={STT_BEAM}")
    print(f"STT_DEVICE={STT_DEVICE}")
    print(f"STT_COMPUTE_TYPE={STT_COMPUTE_TYPE}")

    try:
        stt = FasterWhisperSTT(
            model_size=args.model,
            language=args.language,
        )
        if args.audio:
            print(f"file: {args.audio}")
            text = stt.transcribe(args.audio, language=args.language)
        elif args.seconds is not None:
            samples = record_seconds(args.seconds)
            text = stt.transcribe(samples, language=args.language)
        else:
            samples = record_until_silence()
            text = stt.transcribe(samples, language=args.language)
    except Exception as e:
        print(f"Lỗi STT: {e}", file=sys.stderr)
        return 1

    print(f"text: {text}")
    return 0 if text else 2


if __name__ == "__main__":
    raise SystemExit(main())
