import argparse
from pathlib import Path

from faster_whisper import WhisperModel


# =========================
# Configuration
# =========================

AUDIO_FILE = Path(__file__).resolve().parent / "test.mp3"

MODEL_SIZE = "base"

# Chạy local trên CPU.
# int8 giúp giảm tài nguyên so với fp32.
DEVICE = "cpu"
COMPUTE_TYPE = "int8"


# =========================
# Main
# =========================

def main():
    parser = argparse.ArgumentParser(description="Transcribe a Vietnamese audio file locally.")
    parser.add_argument(
        "audio_file",
        nargs="?",
        type=Path,
        default=AUDIO_FILE,
        help=f"Audio file to transcribe (default: {AUDIO_FILE})",
    )
    audio_file = parser.parse_args().audio_file.expanduser().resolve()

    if not audio_file.is_file():
        print(f"Không tìm thấy file audio: {audio_file}")
        print("Đặt file audio cạnh stt_local.py hoặc truyền đường dẫn file khi chạy.")
        return 1

    print("Loading Whisper model...")

    model = WhisperModel(
        MODEL_SIZE,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
    )

    print("Transcribing...")

    segments, info = model.transcribe(
        str(audio_file),
        language="vi",
        beam_size=5,
        vad_filter=True,
    )

    print()
    print("=== STT RESULT ===")
    print(f"Detected language: {info.language}")
    print(f"Language probability: {info.language_probability:.2f}")
    print()

    full_text = []

    for segment in segments:
        text = segment.text.strip()

        if text:
            print(
                f"[{segment.start:.2f}s -> {segment.end:.2f}s] {text}"
            )
            full_text.append(text)

    print()
    print("=== FINAL TEXT ===")
    print(" ".join(full_text))


if __name__ == "__main__":
    raise SystemExit(main())