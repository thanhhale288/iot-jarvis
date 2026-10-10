"""AI Tuần 1: Ollama trường + tool get_environment → serial_bridge → Uno."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import requests
from dotenv import load_dotenv

# Cho phép chạy từ repo root: python -m ai
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serial_bridge import SerialBridge  # noqa: E402

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://research.neu.edu.vn/ollama").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_environment",
            "description": (
                "Đọc nhiệt độ (°C) và độ ẩm không khí (%) tại bàn làm việc "
                "từ cảm biến DHT11 trên Arduino Uno. Luôn gọi tool này khi "
                "người dùng hỏi nhiệt độ, độ ẩm, hoặc môi trường hiện tại. "
                "Không được bịa số."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }
]


def _chat(messages: list[dict[str, Any]], use_tools: bool = True) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }
    if use_tools:
        body["tools"] = TOOLS
    r = requests.post(f"{OLLAMA_HOST}/api/chat", json=body, timeout=120)
    r.raise_for_status()
    return r.json()


def run_tool(name: str, bridge: SerialBridge) -> str:
    if name == "get_environment":
        data = bridge.get_env()
        return json.dumps(data, ensure_ascii=False)
    return json.dumps({"ok": False, "error": f"unknown_tool:{name}"})


def ask(user_text: str, bridge: SerialBridge | None = None) -> str:
    """Hỏi AI; nếu model gọi tool thì đọc cảm biến rồi trả lời bằng số thật."""
    own_bridge = bridge is None
    if own_bridge:
        bridge = SerialBridge()
        bridge.open()
    assert bridge is not None

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "Bạn là Jarvis trên bàn học. Khi cần số liệu môi trường, "
                "bắt buộc gọi tool get_environment. Trả lời tiếng Việt, ngắn gọn, "
                "dùng đúng số từ tool."
            ),
        },
        {"role": "user", "content": user_text},
    ]

    try:
        data = _chat(messages, use_tools=True)
        msg = data.get("message") or {}
        tool_calls = msg.get("tool_calls") or []

        if tool_calls:
            messages.append(msg)
            for call in tool_calls:
                fn = call.get("function") or {}
                name = fn.get("name") or ""
                print(f"[tool] {name}", flush=True)
                result = run_tool(name, bridge)
                print(f"[tool_result] {result}", flush=True)
                messages.append(
                    {
                        "role": "tool",
                        "tool_name": name,
                        "content": result,
                    }
                )
            data2 = _chat(messages, use_tools=False)
            final = (data2.get("message") or {}).get("content") or ""
            return final.strip()

        # Fallback: model không gọi tool — tự đọc cảm biến rồi hỏi lại
        print("[tool] get_environment (fallback host)", flush=True)
        env = bridge.get_env()
        print(f"[tool_result] {json.dumps(env, ensure_ascii=False)}", flush=True)
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Số liệu cảm biến thật (JSON): {json.dumps(env, ensure_ascii=False)}. "
                    "Hãy trả lời câu hỏi trước đó bằng các số này, tiếng Việt, ngắn."
                ),
            }
        )
        data3 = _chat(messages, use_tools=False)
        return ((data3.get("message") or {}).get("content") or "").strip()
    finally:
        if own_bridge:
            bridge.close()


def main() -> int:
    prompt = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Nhiệt độ và độ ẩm hiện tại trên bàn là bao nhiêu?"
    )
    print(f"OLLAMA_HOST={OLLAMA_HOST}")
    print(f"OLLAMA_MODEL={OLLAMA_MODEL}")
    print(f"user: {prompt}")
    try:
        answer = ask(prompt)
    except requests.RequestException as e:
        print(f"Lỗi Ollama: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        return 1
    print(f"assistant: {answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
