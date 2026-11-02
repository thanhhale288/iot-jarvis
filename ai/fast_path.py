"""Shortcut lệnh cứng + cache get_env — giảm TTFT khi không cần LLM."""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import Any, Callable

FAST_PATH = os.getenv("AI_FAST_PATH", "1").strip() not in ("0", "false", "no")
ENV_CACHE_TTL = float(os.getenv("AI_ENV_CACHE_TTL", "2.0"))

_env_cache: dict[str, Any] = {"at": 0.0, "data": None}


@dataclass
class AskStats:
    path: str = "llm"  # fast | llm
    tool_s: float = 0.0
    first_token_s: float = 0.0
    total_s: float = 0.0
    cache_hit: bool = False


LAST_ASK_STATS = AskStats()


def reset_stats() -> AskStats:
    global LAST_ASK_STATS
    LAST_ASK_STATS = AskStats()
    return LAST_ASK_STATS


def get_environment_cached(get_env: Callable[[], dict[str, Any]]) -> tuple[dict[str, Any], bool]:
    """TTL cache cho get_env (mock/serial đều dùng)."""
    now = time.time()
    if (
        _env_cache["data"] is not None
        and (now - float(_env_cache["at"])) < ENV_CACHE_TTL
    ):
        return _env_cache["data"], True
    data = get_env()
    _env_cache["at"] = now
    _env_cache["data"] = data
    return data, False


def _speak_temp_hum(env: dict[str, Any]) -> str:
    temp = env.get("temp")
    hum = env.get("hum")
    # Số đọc TTS-friendly (pipeline còn for_speech thêm lần nữa — giữ đơn giản)
    return (
        f"Nhiệt độ {temp} độ C, độ ẩm {hum} phần trăm."
        if temp is not None and hum is not None
        else "Đã đọc cảm biến môi trường."
    )


def try_fast_reply(
    user_text: str,
    *,
    set_relay: Callable[[str, bool], dict[str, Any]],
    set_pump: Callable[[bool, int], dict[str, Any]],
    get_env: Callable[[], dict[str, Any]],
) -> str | None:
    """Nếu khớp lệnh rõ → chạy tool + câu trả lời mẫu, không gọi Ollama."""
    if not FAST_PATH:
        return None
    t = (user_text or "").casefold().strip()
    if not t:
        return None

    # Đèn / quạt
    if re.search(r"\b(bật|mở)\s+đèn\b", t) or t in {"bật đèn", "mở đèn"}:
        set_relay("light", True)
        return "Đã bật đèn."
    if re.search(r"\b(tắt|tắt hết)\s+đèn\b", t) or t == "tắt đèn":
        set_relay("light", False)
        return "Đã tắt đèn."
    if re.search(r"\b(bật|mở)\s+quạt\b", t) or t == "bật quạt":
        set_relay("fan", True)
        return "Đã bật quạt."
    if re.search(r"\btắt\s+quạt\b", t) or t == "tắt quạt":
        set_relay("fan", False)
        return "Đã tắt quạt."

    # Tưới N giây
    m = re.search(r"tưới(?:\s+nước)?\s*(\d+)\s*giây", t)
    if m:
        sec = max(1, min(5, int(m.group(1))))
        set_pump(True, sec)
        return f"Đã tưới {sec} giây."
    if re.search(r"\b(tưới|bơm)\b", t) and not re.search(r"tắt", t):
        set_pump(True, 2)
        return "Đã tưới 2 giây."

    # Môi trường
    if any(
        k in t
        for k in (
            "nhiệt",
            "độ ẩm",
            "ẩm",
            "môi trường",
            "đất",
            "ánh sáng",
            "sáng",
        )
    ):
        env, hit = get_environment_cached(get_env)
        LAST_ASK_STATS.cache_hit = hit
        return _speak_temp_hum(env)

    return None
