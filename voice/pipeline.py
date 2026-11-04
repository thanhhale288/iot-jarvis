"""Record → STT → LLM → TTS: text UI và audio cùng một chuỗi."""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.chat_env import ask_sentences
from ai.fast_path import LAST_ASK_STATS
from voice.record import record_until_silence
from voice.stt import FasterWhisperSTT
from voice.tts import StreamingSpeaker, for_speech, speak

# full = đợi cả câu rồi nói 1 lần (khớp text↔audio); chunk = overlap nhanh hơn
TTS_MODE = os.getenv("TTS_MODE", "full").strip().lower()


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

    def summary(self) -> str:
        ttfs = (
            f"{self.tts_first_audio_s:.2f}s"
            if self.tts_first_audio_s is not None
            else "n/a"
        )
        return (
            f"path={self.ask_path} tool={self.tool_s:.2f}s "
            f"first_token={self.first_token_s:.2f}s | "
            f"record {self.record_s:.2f}s | stt {self.stt_s:.2f}s | "
            f"llm→câu1 {self.llm_first_sentence_s:.2f}s | "
            f"time-to-first-speech {ttfs} | total {self.total_s:.2f}s | "
            f"tts_mode={TTS_MODE}"
        )


_stt: FasterWhisperSTT | None = None


def _stt_engine() -> FasterWhisperSTT:
    global _stt
    if _stt is None:
        _stt = FasterWhisperSTT()
    return _stt


def run_voice_turn(
    *,
    user_text: str | None = None,
    speak_out: bool = True,
) -> PipelineTimings:
    """Một lượt mic/text → Jarvis. `assistant_text` == nội dung đưa TTS."""
    t0 = time.time()
    timings = PipelineTimings()

    if user_text is None:
        t_rec = time.time()
        audio = record_until_silence()
        timings.record_s = time.time() - t_rec
        t_stt = time.time()
        user_text = _stt_engine().transcribe(audio)
        timings.stt_s = time.time() - t_stt
    timings.user_text = (user_text or "").strip()
    if not timings.user_text:
        timings.total_s = time.time() - t0
        return timings

    parts: list[str] = []
    first_sent_at: float | None = None
    speaker: StreamingSpeaker | None = None

    if speak_out and TTS_MODE == "chunk":
        speaker = StreamingSpeaker()
        speaker.start(t0_wall=t0)

    try:
        for sent in ask_sentences(timings.user_text):
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
    timings.assistant_text = for_speech(raw)  # cùng chuẩn với TTS
    timings.ask_path = LAST_ASK_STATS.path
    timings.tool_s = LAST_ASK_STATS.tool_s
    timings.first_token_s = LAST_ASK_STATS.first_token_s

    # B7: STT→…→TTS + led/motion Otto khi AI_BACKEND=real|serial
    act_on = os.getenv("VOICE_ACT", "1").strip().lower() not in ("0", "false", "no")
    backend = os.getenv("AI_BACKEND", "mock").strip().lower()
    if act_on and backend in ("real", "board", "hw", "serial", "uno", "bridge"):
        try:
            from host.router import make_router_from_env
            from host.speak_act import guess_emotion_motion, speak_and_act

            emotion, motion = guess_emotion_motion(
                timings.user_text, timings.assistant_text
            )
            router = make_router_from_env()
            speak_and_act(
                router,
                text=timings.assistant_text,
                emotion=emotion,
                motion=motion,
            )
            close = getattr(router.uno, "close", None)
            if callable(close):
                close()
        except Exception as e:
            print(f"[voice] speak_and_act skip: {e}", flush=True)

    if speak_out and TTS_MODE != "chunk" and timings.assistant_text:
        t_tts = time.time()
        timings.spoken_text = speak(timings.assistant_text)
        timings.tts_first_audio_s = t_tts - t0
    elif not timings.spoken_text:
        timings.spoken_text = timings.assistant_text

    timings.total_s = time.time() - t0
    return timings


def main() -> int:
    no_tts = "--no-tts" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--no-tts"]
    text = args[0] if args else None
    print("pipeline: record→stt→ask→tts" if text is None else f"text: {text}")
    try:
        t = run_voice_turn(user_text=text, speak_out=not no_tts)
    except Exception as e:
        print(f"Lỗi pipeline: {e}", file=sys.stderr)
        return 1
    print(f"user: {t.user_text}")
    print(f"assistant: {t.assistant_text}")
    print(f"spoken:  {t.spoken_text}")
    print(t.summary())
    return 0 if t.assistant_text else 2


if __name__ == "__main__":
    raise SystemExit(main())
