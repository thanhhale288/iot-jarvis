"""speak_and_act — emotion→led, motion→motion, text→TTS phía caller (A7/B7)."""

from __future__ import annotations

from typing import Any

LED_STATES = frozenset(
    {"idle", "listening", "thinking", "speaking", "happy", "alert"}
)
MOTION_NAMES = frozenset(
    {
        "idle",
        "nod",
        "shake",
        "think",
        "happy",
        "alert",
        "turn_left",
        "turn_right",
        "step_forward",
    }
)

# emotion → motion mặc định (MOTION_EMOTION_MAP)
EMOTION_MOTION = {
    "idle": "idle",
    "listening": "idle",
    "thinking": "think",
    "speaking": "nod",
    "happy": "happy",
    "alert": "alert",
}


def speak_and_act(
    router: Any,
    *,
    text: str,
    emotion: str = "speaking",
    motion: str | None = None,
    cmd_id: str = "sa1",
    speak_text: bool = False,
) -> dict[str, Any]:
    """emotion→led, motion→motion; text→TTS nếu `speak_text` (A7)."""
    if emotion not in LED_STATES:
        emotion = "speaking"
    if motion is None:
        motion = EMOTION_MOTION.get(emotion, "nod")
    if motion not in MOTION_NAMES:
        motion = "nod"

    led = router.dispatch(
        {
            "v": 1,
            "id": f"{cmd_id}l",
            "to": "esp32",
            "cmd": "led",
            "state": emotion,
        }
    )
    # led đã chạy motion mặc định trên sketch; gửi motion riêng nếu khác
    mot: dict[str, Any] | None = None
    mapped = EMOTION_MOTION.get(emotion)
    if motion != mapped:
        mot = router.dispatch(
            {
                "v": 1,
                "id": f"{cmd_id}m",
                "to": "esp32",
                "cmd": "motion",
                "name": motion,
            }
        )

    spoken = ""
    if speak_text and text.strip():
        from voice.tts import speak

        spoken = speak(text)

    return {
        "v": 1,
        "from": "host",
        "ok": bool(led.get("ok")),
        "text": text,
        "emotion": emotion,
        "motion": motion,
        "led": led,
        "motion_ack": mot,
        "spoken": spoken or text,
    }


def guess_emotion_motion(user_text: str, assistant_text: str) -> tuple[str, str]:
    """Heuristic ngắn cho pipeline giọng (B7)."""
    blob = f"{user_text} {assistant_text}".casefold()
    if any(k in blob for k in ("cảnh báo", "khô", "tưới", "alert")):
        return "alert", "alert"
    if any(k in blob for k in ("vui", "happy", "xin chào", "chào")):
        return "happy", "happy"
    if any(k in blob for k in ("nghĩ", "thinking")):
        return "thinking", "think"
    if any(k in blob for k in ("nghe", "listening")):
        return "listening", "idle"
    return "speaking", "nod"
