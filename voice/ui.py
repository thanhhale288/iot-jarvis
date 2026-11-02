"""UI Gradio — low-latency Jarvis: record → STT → LLM stream → TTS.

Chạy: python -m voice.ui
"""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Iterator

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice.pipeline import TTS_MODE, run_voice_turn
from voice.stt import STT_BEAM, STT_LANGUAGE, STT_MODEL, FasterWhisperSTT
from voice.tts import TTS_RATE, TTS_VOICE, speak


def _warmup() -> None:
    print("Loading Whisper…", flush=True)
    FasterWhisperSTT()
    print("Whisper ready.", flush=True)


def jarvis_from_mic() -> Iterator[str]:
    yield "● Đang ghi (im lặng ~0.6s là dừng)…"
    t = run_voice_turn(user_text=None, speak_out=True)
    if not t.user_text:
        yield "Không nhận ra chữ. Thử nói to hơn / gần mic."
        return
    yield (
        f"**Bạn:** {t.user_text}\n\n"
        f"**Jarvis (text = audio):** {t.assistant_text}\n\n"
        f"`{t.summary()}`"
    )


def jarvis_from_text(text: str) -> Iterator[str]:
    text = (text or "").strip()
    if not text:
        yield "Nhập câu hoặc bấm mic."
        return
    yield f"● LLM+TTS…\nBạn: {text}"
    t = run_voice_turn(user_text=text, speak_out=True)
    yield (
        f"**Bạn:** {t.user_text}\n\n"
        f"**Jarvis (text = audio):** {t.assistant_text}\n\n"
        f"`{t.summary()}`"
    )


def batch_stt_only() -> Iterator[str]:
    from voice.record import record_until_silence

    yield "● Ghi mic…"
    t0 = time.time()
    audio = record_until_silence()
    text = FasterWhisperSTT().transcribe(audio)
    dt = time.time() - t0
    yield f"text: {text or '(trống)'}\n`stt+record {dt:.2f}s`"


def tts_only(text: str) -> str:
    text = (text or "").strip() or "Xin chào, mình là Jarvis."
    speak(text)
    return f"Đã nói: {text}"


def build_ui():
    import gradio as gr

    with gr.Blocks(title="Jarvis low-latency") as demo:
        gr.Markdown(
            f"# Jarvis · STT→Ollama→TTS\n"
            f"STT `{STT_MODEL}` beam={STT_BEAM} `{STT_LANGUAGE}` · "
            f"TTS `{TTS_VOICE}` rate `{TTS_RATE}` · mode `{TTS_MODE}` "
            f"(full = text khớp audio).\n"
            f"Ollama đã gắn: sau STT gọi Qwen + tools, rồi đọc đúng câu trả lời."
        )
        out = gr.Markdown("Sẵn sàng.")
        with gr.Row():
            mic_btn = gr.Button("▶ Nói → Jarvis (mic)", variant="primary", size="lg")
        text_in = gr.Textbox(
            label="Hoặc gõ câu (bỏ qua STT — đo LLM+TTS)",
            placeholder="Bật đèn / Nhiệt độ bao nhiêu?",
        )
        text_btn = gr.Button("Gửi text → Jarvis")
        mic_btn.click(fn=jarvis_from_mic, outputs=out)
        text_btn.click(fn=jarvis_from_text, inputs=text_in, outputs=out)

        gr.Markdown("---\n### Debug")
        with gr.Row():
            stt_btn = gr.Button("Chỉ STT")
            tts_btn = gr.Button("Chỉ TTS mẫu")
        stt_btn.click(fn=batch_stt_only, outputs=out)
        tts_btn.click(fn=lambda: tts_only("Xin chào, mình là Jarvis trên bàn học."), outputs=out)

    return demo


def main() -> int:
    host = os.getenv("STT_UI_HOST", "127.0.0.1")
    port = int(os.getenv("STT_UI_PORT", "7860"))
    print(f"UI http://{host}:{port}")
    _warmup()
    demo = build_ui()
    demo.queue()
    demo.launch(server_name=host, server_port=port, show_error=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
