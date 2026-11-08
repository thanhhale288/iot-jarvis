"""A7: speak_and_act — text→TTS, emotion→led, motion→motion (PROTOCOL §7)."""

from __future__ import annotations

import os
import re
import uuid
from collections.abc import Callable
from typing import Any

from host.mock_boards import LED_STATES, MOTION_NAMES

# 1 = firmware led chỉ TFT (flash otto_motion mới). 0 = gửi 1 lệnh motion (ổn định hơn).
LED_FACE_ONLY = os.getenv("ESP32_LED_FACE_ONLY", "0").strip() not in (
    "0",
    "false",
    "no",
)

# emotion → motion mặc định (MOTION_EMOTION_MAP)
EMOTION_DEFAULT_MOTION: dict[str, str] = {
    "idle": "idle",
    "listening": "idle",
    "thinking": "think",
    "speaking": "nod",
    "happy": "happy",
    "alert": "alert",
}

SpeakFn = Callable[[str], str]


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


def normalize_emotion(value: str | None) -> str | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    return s if s in LED_STATES else None


def normalize_motion(value: str | None) -> str | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    return s if s in MOTION_NAMES else None


def infer_emotion(*texts: str) -> str:
    """Heuristic từ câu user/assistant → emotion enum."""
    blob = " ".join(t for t in texts if t).casefold()
    if not blob:
        return "speaking"
    if re.search(
        r"cảnh báo|nguy hiểm|khẩn|lỗi|alert|angry|tức|giận|khô|cháy", blob
    ):
        return "alert"
    if re.search(r"vui|happy|tuyệt|giỏi|yay|😊|haha|cảm ơn", blob):
        return "happy"
    if re.search(r"nghĩ|thinking|đợi|chờ một chút", blob):
        return "thinking"
    if re.search(r"nghe|listening|lắng nghe", blob):
        return "listening"
    return "speaking"


def infer_motion(emotion: str, explicit: str | None = None) -> str:
    m = normalize_motion(explicit)
    if m:
        return m
    return EMOTION_DEFAULT_MOTION.get(emotion, "nod")


def speak_and_act(
    router: Any,
    *,
    text: str,
    emotion: str | None = None,
    motion: str | None = None,
    speak_fn: SpeakFn | None = None,
    speak_text: bool = False,
    cmd_id: str | None = None,
) -> dict[str, Any]:
    """Tách speak_and_act → ESP32 led/motion + TTS.

    `speak_fn=None` → chỉ điều khiển Otto (pipeline/UI tự TTS).
    `speak_text=True` → alias main: tự dùng `voice.tts.speak`.
    """
    if speak_text and speak_fn is None:
        from voice.tts import speak as _speak

        speak_fn = _speak
    mid = cmd_id or _new_id()
    text = (text or "").strip()
    emo = normalize_emotion(emotion)
    mot = normalize_motion(motion)

    if emo is None and emotion:
        return {
            "v": 1,
            "id": mid,
            "from": "host",
            "ok": False,
            "error": "bad_args",
            "detail": f"emotion không hợp lệ: {emotion!r}",
        }
    if mot is None and motion:
        return {
            "v": 1,
            "id": mid,
            "from": "host",
            "ok": False,
            "error": "bad_args",
            "detail": f"motion không hợp lệ: {motion!r}",
        }

    if emo is None and mot is None and text:
        emo = infer_emotion(text)
        mot = infer_motion(emo)
    elif emo is None and mot is not None:
        emo = "speaking"
    elif emo is not None and mot is None:
        mot = infer_motion(emo)

    led_ack: dict[str, Any] | None = None
    motion_ack: dict[str, Any] | None = None

    # otto_motion cũ: led cũng chạy servo (chậm, dễ timeout nếu gửi 2 lệnh).
    # Mặc định: một lệnh motion. Sau khi flash face-only: ESP32_LED_FACE_ONLY=1.
    if LED_FACE_ONLY:
        if emo:
            led_ack = router.dispatch(
                {
                    "v": 1,
                    "id": f"{mid}l",
                    "to": "esp32",
                    "cmd": "led",
                    "state": emo,
                }
            )
        if mot:
            motion_ack = router.dispatch(
                {
                    "v": 1,
                    "id": f"{mid}m",
                    "to": "esp32",
                    "cmd": "motion",
                    "name": mot,
                }
            )
    else:
        name = mot or (EMOTION_DEFAULT_MOTION.get(emo) if emo else None)
        if name:
            motion_ack = router.dispatch(
                {
                    "v": 1,
                    "id": f"{mid}m",
                    "to": "esp32",
                    "cmd": "motion",
                    "name": name,
                }
            )
            mot = name
        elif emo:
            led_ack = router.dispatch(
                {
                    "v": 1,
                    "id": f"{mid}l",
                    "to": "esp32",
                    "cmd": "led",
                    "state": emo,
                }
            )

    spoken = ""
    if text and speak_fn is not None:
        spoken = speak_fn(text) or text

    led_ok = led_ack is None or bool(led_ack.get("ok"))
    motion_ok = motion_ack is None or bool(motion_ack.get("ok"))
    ok = led_ok and motion_ok
    out: dict[str, Any] = {
        "v": 1,
        "id": mid,
        "from": "host",
        "ok": ok,
        "cmd": "speak_and_act",
        "text": text,
        "emotion": emo,
        "motion": mot,
        "spoken": spoken,
        "led": led_ack,
        "motion_ack": motion_ack,
    }
    if not ok:
        out["error"] = "busy" if False else "bad_args"
        if led_ack and not led_ack.get("ok"):
            out["error"] = led_ack.get("error", "bad_args")
        if motion_ack and not motion_ack.get("ok"):
            out["error"] = motion_ack.get("error", "bad_args")
    return out


def handle_host_speak_and_act(
    router: Any, msg: dict[str, Any], speak_fn: SpeakFn | None
) -> dict[str, Any]:
    return speak_and_act(
        router,
        text=str(msg.get("text") or ""),
        emotion=msg.get("emotion"),
        motion=msg.get("motion"),
        speak_fn=speak_fn,
        cmd_id=str(msg["id"]) if msg.get("id") is not None else None,
    )
