"""AI Tuần 2: Ollama + tools get_environment / set_relay / set_pump.

A3: backend mock (không Serial). AI_BACKEND=serial khi có Uno.
A4: system prompt Jarvis chỉnh được (AI_SYSTEM_PROMPT); cần Ollama sống.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from typing import Any, Protocol

import requests
from dotenv import load_dotenv

# Cho phép chạy từ repo root: python -m ai
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
AI_BACKEND = os.getenv("AI_BACKEND", "mock").strip().lower()

# A4: giọng Jarvis — override bằng AI_SYSTEM_PROMPT trong .env (một dòng hoặc \\n)
DEFAULT_SYSTEM_PROMPT = (
    "Bạn là Jarvis trên bàn học — trợ lý ngắn gọn, tiếng Việt.\n"
    "Luôn dùng tool khi cần số liệu hoặc điều khiển; không bịa số cảm biến, không bịa ACK.\n"
    "- Hỏi nhiệt/ẩm/sáng/đất/môi trường → gọi get_environment, rồi trả lời đúng số trong JSON tool.\n"
    "- Bật/tắt đèn → set_relay name=light; quạt → name=fan; on true/false.\n"
    "- Tưới/bơm → set_pump on=true, seconds 1–5 (mặc định 2); không tưới vô hạn.\n"
    "Một câu trả lời sau tool: ngắn, rõ việc đã làm hoặc số đo. Không giải thích dài."
)

_ENV_HINTS = (
    "nhiệt",
    "ẩm",
    "đất",
    "sáng",
    "môi trường",
    "temp",
    "hum",
    "soil",
    "light",
    "environment",
    "độ ẩm",
)
_ACTION_HINTS = (
    "bật",
    "tắt",
    "tưới",
    "bơm",
    "đèn",
    "quạt",
    "relay",
    "pump",
    "fan",
)


def system_prompt() -> str:
    raw = os.getenv("AI_SYSTEM_PROMPT", "").strip()
    if not raw:
        return DEFAULT_SYSTEM_PROMPT
    return raw.replace("\\n", "\n")


def _looks_like_env(text: str) -> bool:
    t = text.casefold()
    return any(h in t for h in _ENV_HINTS)


def _looks_like_action(text: str) -> bool:
    t = text.casefold()
    return any(h in t for h in _ACTION_HINTS)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_environment",
            "description": (
                "Đọc nhiệt độ (°C), độ ẩm không khí (%), ánh sáng (ADC 0–1023) "
                "và độ ẩm đất (ADC 0–1023; số lớn = khô hơn) từ Arduino Uno. "
                "Gọi khi hỏi môi trường / nhiệt / ẩm / sáng / đất. Không bịa số."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_relay",
            "description": (
                "Bật/tắt đèn (light) hoặc quạt (fan) qua relay/chân Uno. "
                "Gọi khi người dùng yêu cầu bật/tắt đèn hoặc quạt."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "enum": ["light", "fan"],
                        "description": "light = đèn, fan = quạt",
                    },
                    "on": {
                        "type": "boolean",
                        "description": "true = bật, false = tắt",
                    },
                },
                "required": ["name", "on"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_pump",
            "description": (
                "Bật/tắt bơm tưới. Khi bật, seconds từ 1 đến 5 (mặc định 2); "
                "hết giờ bơm tự tắt. Không tưới vô hạn."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "on": {"type": "boolean"},
                    "seconds": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Thời gian tưới khi on=true",
                    },
                },
                "required": ["on"],
            },
        },
    },
]


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


class BoardBackend(Protocol):
    """Uno actuators — mock hoặc Serial."""

    def get_env(self) -> dict[str, Any]: ...

    def set_relay(self, name: str, on: bool) -> dict[str, Any]: ...

    def set_pump(self, on: bool, seconds: int = 2) -> dict[str, Any]: ...

    def close(self) -> None: ...


class MockBoardBackend:
    """A3: tools → HostRouter mock, không mở Serial."""

    def __init__(self, router: Any | None = None) -> None:
        from host.router import make_mock_router

        self.router = router or make_mock_router()

    def get_env(self) -> dict[str, Any]:
        return self.router.dispatch(
            {"v": 1, "id": _new_id(), "to": "uno", "cmd": "get_env"}
        )

    def set_relay(self, name: str, on: bool) -> dict[str, Any]:
        return self.router.dispatch(
            {
                "v": 1,
                "id": _new_id(),
                "to": "uno",
                "cmd": "relay",
                "name": name,
                "on": on,
            }
        )

    def set_pump(self, on: bool, seconds: int = 2) -> dict[str, Any]:
        sec = max(1, min(5, int(seconds)))
        return self.router.dispatch(
            {
                "v": 1,
                "id": _new_id(),
                "to": "uno",
                "cmd": "pump",
                "on": on,
                "seconds": sec,
            }
        )

    def close(self) -> None:
        return None


class SerialBoardBackend:
    """B5 / có board: bọc SerialBridge."""

    def __init__(self, bridge: Any | None = None) -> None:
        from serial_bridge import SerialBridge

        self._own = bridge is None
        self.bridge = bridge or SerialBridge()
        if self._own:
            self.bridge.open()

    def get_env(self) -> dict[str, Any]:
        return self.bridge.get_env()

    def set_relay(self, name: str, on: bool) -> dict[str, Any]:
        return self.bridge.set_relay(name, on)

    def set_pump(self, on: bool, seconds: int = 2) -> dict[str, Any]:
        return self.bridge.set_pump(on, seconds)

    def close(self) -> None:
        if self._own:
            self.bridge.close()


def make_backend(kind: str | None = None) -> BoardBackend:
    mode = (kind or AI_BACKEND or "mock").strip().lower()
    if mode in ("serial", "uno", "bridge"):
        return SerialBoardBackend()
    return MockBoardBackend()


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


def _parse_args(fn: dict[str, Any]) -> dict[str, Any]:
    raw = fn.get("arguments")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def run_tool(name: str, args: dict[str, Any], backend: BoardBackend) -> str:
    if name == "get_environment":
        data = backend.get_env()
        return json.dumps(data, ensure_ascii=False)
    if name == "set_relay":
        channel = str(args.get("name") or "")
        on = bool(args.get("on"))
        data = backend.set_relay(channel, on)
        return json.dumps(data, ensure_ascii=False)
    if name == "set_pump":
        on = bool(args.get("on"))
        seconds = int(args.get("seconds") or 2)
        data = backend.set_pump(on, seconds)
        return json.dumps(data, ensure_ascii=False)
    return json.dumps({"ok": False, "error": f"unknown_tool:{name}"})


def _run_tool_round(
    messages: list[dict[str, Any]],
    tool_calls: list[dict[str, Any]],
    backend: BoardBackend,
) -> None:
    for call in tool_calls:
        fn = call.get("function") or {}
        name = fn.get("name") or ""
        args = _parse_args(fn)
        print(f"[tool] {name} {args}", flush=True)
        result = run_tool(name, args, backend)
        print(f"[tool_result] {result}", flush=True)
        messages.append(
            {
                "role": "tool",
                "tool_name": name,
                "content": result,
            }
        )


def ask(user_text: str, backend: BoardBackend | None = None) -> str:
    """Hỏi AI; tool → mock hoặc Serial tùy backend. A4: style qua system_prompt()."""
    own = backend is None
    if own:
        backend = make_backend()
    assert backend is not None

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": user_text},
    ]

    try:
        used_tools = False
        msg: dict[str, Any] = {}
        for _round in range(3):
            data = _chat(messages, use_tools=True)
            msg = data.get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                break
            used_tools = True
            messages.append(msg)
            _run_tool_round(messages, tool_calls, backend)

        if used_tools:
            data2 = _chat(messages, use_tools=False)
            return ((data2.get("message") or {}).get("content") or "").strip()

        # Không có tool_calls: nudge một lần nếu rõ là action/env
        if _looks_like_action(user_text) or _looks_like_env(user_text):
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Bắt buộc gọi đúng tool (get_environment / set_relay / set_pump). "
                        "Không chỉ trả lời chữ."
                    ),
                }
            )
            data_n = _chat(messages, use_tools=True)
            msg_n = data_n.get("message") or {}
            calls_n = msg_n.get("tool_calls") or []
            if calls_n:
                messages.append(msg_n)
                _run_tool_round(messages, calls_n, backend)
                data2 = _chat(messages, use_tools=False)
                return ((data2.get("message") or {}).get("content") or "").strip()

        # Fallback get_env chỉ khi câu hỏi môi trường
        if _looks_like_env(user_text):
            print("[tool] get_environment (fallback host)", flush=True)
            env = backend.get_env()
            print(f"[tool_result] {json.dumps(env, ensure_ascii=False)}", flush=True)
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Số liệu cảm biến thật (JSON): {json.dumps(env, ensure_ascii=False)}. "
                        "Trả lời câu hỏi trước bằng các số này, tiếng Việt, ngắn."
                    ),
                }
            )
            data3 = _chat(messages, use_tools=False)
            return ((data3.get("message") or {}).get("content") or "").strip()

        content = (msg.get("content") or "").strip()
        return content
    finally:
        if own:
            backend.close()


def main() -> int:
    prompt = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Nhiệt độ và độ ẩm hiện tại trên bàn là bao nhiêu?"
    )
    print(f"OLLAMA_HOST={OLLAMA_HOST}")
    print(f"OLLAMA_MODEL={OLLAMA_MODEL}")
    print(f"AI_BACKEND={AI_BACKEND}")
    style = os.getenv("AI_SYSTEM_PROMPT", "").strip()
    print(f"AI_SYSTEM_PROMPT={'custom' if style else 'default'}")
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
