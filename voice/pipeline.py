"""Record → STT → LLM → Otto + TTS (A6b / A7 / B7)."""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.chat_env import ask_sentences, make_backend
from ai.fast_path import LAST_ASK_STATS
from host.speak_act import infer_emotion, infer_motion, speak_and_act
from voice.record import record_until_silence
from voice.stt import FasterWhisperSTT
from voice.tts import StreamingSpeaker, for_speech, speak

# full = đợi cả câu rồi nói 1 lần (khớp text↔audio); chunk = overlap nhanh hơn
TTS_MODE = os.getenv("TTS_MODE", "full").strip().lower()
OTTO_ACT = os.getenv("OTTO_ACT", "1").strip() not in ("0", "false", "no")


@dataclass
class PipelineTimings:
    record_s: float = 0.0
    stt_s: float = 0.0
    llm_first_sentence_s: float = 0.0
    tts_first_audio_s: float | None = None
    total_s: float = 0.0
    user_text: str = ""
    assistant_text: str = ""
    spoken_text: str = ""
    sentences: list[str] = field(default_factory=list)
    ask_path: str = ""
    tool_s: float = 0.0
    first_token_s: float = 0.0
    emotion: str = ""
    motion: str = ""
    otto_ok: bool | None = None

    def summary(self) -> str:
        ttfs = (
            f"{self.tts_first_audio_s:.2f}s"
            if self.tts_first_audio_s is not None
            else "n/a"
        )
        otto = (
            f" otto={self.emotion}/{self.motion} ok={self.otto_ok}"
            if self.emotion or self.motion
            else ""
        )
        return (
            f"path={self.ask_path} tool={self.tool_s:.2f}s "
            f"first_token={self.first_token_s:.2f}s | "
            f"record {self.record_s:.2f}s | stt {self.stt_s:.2f}s | "
            f"llm→câu1 {self.llm_first_sentence_s:.2f}s | "
            f"time-to-first-speech {ttfs} | total {self.total_s:.2f}s | "
            f"tts_mode={TTS_MODE}{otto}"
        )


_stt: FasterWhisperSTT | None = None
_backend: Any | None = None


def _stt_engine() -> FasterWhisperSTT:
    global _stt
    if _stt is None:
        _stt = FasterWhisperSTT()
    return _stt


def _board() -> Any:
    global _backend
    if _backend is None:
        _backend = make_backend()
    return _backend


def _safe_led(state: str) -> None:
    """Trạng thái nghe/nghĩ — tránh treo nếu firmware led còn chạy servo."""
    if not OTTO_ACT:
        return
    try:
        from host.speak_act import EMOTION_DEFAULT_MOTION, LED_FACE_ONLY

        if LED_FACE_ONLY:
            ack = _board().set_led(state)
        else:
            # Firmware cũ: dùng motion mặc định (listening→idle nhanh hơn happy)
            ack = _board().otto_act(
                emotion=None, motion=EMOTION_DEFAULT_MOTION.get(state, "idle")
            )
        if isinstance(ack, dict) and not ack.get("ok"):
            print(f"[otto] status {state} → {ack.get('error')}", flush=True)
    except Exception as exc:
        print(f"[otto] status {state} lỗi: {exc}", flush=True)


def _resolve_otto(
    user_text: str, assistant_text: str, backend: Any
) -> tuple[str, str]:
    """Ưu tiên emotion/motion từ tool otto_act; không có thì heuristic."""
    last = getattr(backend, "_last_otto", None) or {}
    emo = last.get("emotion") if isinstance(last, dict) else None
    mot = last.get("motion") if isinstance(last, dict) else None
    if emo or mot:
        emotion = str(emo or infer_emotion(user_text, assistant_text))
        motion = str(mot or infer_motion(emotion))
        return emotion, motion
    emotion = infer_emotion(user_text, assistant_text)
    return emotion, infer_motion(emotion)


def run_voice_turn(
    *,
    user_text: str | None = None,
    speak_out: bool = True,
) -> PipelineTimings:
    """Một lượt mic/text → Jarvis (+ Otto nếu OTTO_ACT=1)."""
    t0 = time.time()
    timings = PipelineTimings()
    # Tools luôn cần backend (mock/serial). OTTO_ACT chỉ bật led/motion/speak_and_act.
    backend = _board()

    if user_text is None:
        _safe_led("listening")
        t_rec = time.time()
        audio = record_until_silence()
        timings.record_s = time.time() - t_rec
        t_stt = time.time()
        user_text = _stt_engine().transcribe(audio)
        timings.stt_s = time.time() - t_stt
    timings.user_text = (user_text or "").strip()
    if not timings.user_text:
        timings.total_s = time.time() - t0
        _safe_led("idle")
        return timings

    _safe_led("thinking")

    parts: list[str] = []
    first_sent_at: float | None = None
    speaker: StreamingSpeaker | None = None

    if speak_out and TTS_MODE == "chunk":
        speaker = StreamingSpeaker()
        speaker.start(t0_wall=t0)

    try:
        for sent in ask_sentences(timings.user_text, backend=backend):
            if first_sent_at is None:
                first_sent_at = time.time()
                timings.llm_first_sentence_s = first_sent_at - t0
            parts.append(sent)
            timings.sentences.append(sent)
            if speaker:
                speaker.submit(sent)
    finally:
        if speaker:
            speaker.close()
            if speaker.first_audio_at is not None:
                timings.tts_first_audio_s = speaker.first_audio_at - t0
            timings.spoken_text = " ".join(speaker.spoken_parts).strip()

    raw = " ".join(parts).strip()
    timings.assistant_text = for_speech(raw)
    timings.ask_path = LAST_ASK_STATS.path
    timings.tool_s = LAST_ASK_STATS.tool_s
    timings.first_token_s = LAST_ASK_STATS.first_token_s

    # A7/B7: Otto (+ TTS full nếu speak_out). Chunk TTS đã nói ở trên.
    need_full_tts = bool(
        speak_out and TTS_MODE != "chunk" and timings.assistant_text
    )
    if OTTO_ACT and timings.assistant_text:
        emotion, motion = _resolve_otto(
            timings.user_text, timings.assistant_text, backend
        )
        timings.emotion = emotion
        timings.motion = motion
        try:
            speak_fn = None
            if need_full_tts:

                def _speak(t: str) -> str:
                    if timings.tts_first_audio_s is None:
                        timings.tts_first_audio_s = time.time() - t0
                    return speak(t)

                speak_fn = _speak
            out = speak_and_act(
                backend.router,
                text=timings.assistant_text,
                emotion=emotion,
                motion=motion,
                speak_fn=speak_fn,
            )
            timings.otto_ok = bool(out.get("ok"))
            if need_full_tts:
                timings.spoken_text = out.get("spoken") or timings.assistant_text
            elif not timings.spoken_text:
                timings.spoken_text = timings.assistant_text
            print(
                f"[otto] emotion={emotion} motion={motion} ok={timings.otto_ok}",
                flush=True,
            )
        except Exception as exc:
            print(f"[otto] lỗi: {exc}", flush=True)
            timings.otto_ok = False
            if need_full_tts:
                timings.tts_first_audio_s = time.time() - t0
                timings.spoken_text = speak(timings.assistant_text)
            elif not timings.spoken_text:
                timings.spoken_text = timings.assistant_text
    elif need_full_tts:
        timings.tts_first_audio_s = time.time() - t0
        timings.spoken_text = speak(timings.assistant_text)
    elif not timings.spoken_text:
        timings.spoken_text = timings.assistant_text

    timings.total_s = time.time() - t0
    return timings


def main() -> int:
    no_tts = "--no-tts" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--no-tts"]
    text = args[0] if args else None
    print("pipeline: record→stt→ask→otto+tts" if text is None else f"text: {text}")
    try:
        t = run_voice_turn(user_text=text, speak_out=not no_tts)
    except Exception as e:
        print(f"Lỗi pipeline: {e}", file=sys.stderr)
        return 1
    print(f"user: {t.user_text}")
    print(f"assistant: {t.assistant_text}")
    print(f"spoken: {t.spoken_text}")
    print(t.summary())
    return 0 if t.assistant_text else 2


if __name__ == "__main__":
    raise SystemExit(main())
