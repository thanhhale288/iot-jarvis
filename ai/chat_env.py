"""AI Tuần 2: Ollama + tools get_environment / set_relay / set_pump.

A3: backend mock (không Serial). AI_BACKEND=serial khi có Uno.
A4: system prompt Jarvis chỉnh được (AI_SYSTEM_PROMPT); cần Ollama sống.
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from collections.abc import Iterator
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
    "Bạn là Jarvis trên bàn học — nói chuyện bằng tiếng Việt, một câu ngắn.\n"
    "Câu trả lời sẽ được đọc thành tiếng (TTS): viết đúng như sẽ nói, không markdown, "
    "không ký hiệu (°C viết thành 'độ C', % thành 'phần trăm'), không tiếng Anh thừa.\n"
    "Luôn dùng tool khi cần số liệu hoặc điều khiển; không bịa số cảm biến, không bịa ACK.\n"
    "- Hỏi nhiệt/ẩm/sáng/đất/môi trường → get_environment, rồi nói đúng số từ JSON.\n"
    "- Bật/tắt đèn → set_relay name=light; quạt → name=fan; on true/false.\n"
    "- Tưới/bơm → set_pump on=true, seconds 1–5 (mặc định 2); không tưới vô hạn.\n"
    "Ví dụ giọng: 'Nhiệt độ hai mươi tám phẩy bốn độ C, độ ẩm sáu mốt phần trăm.' "
    "hoặc 'Đã bật đèn.'"
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
    """B5 / có board: bọc SerialBridge (chỉ Uno)."""

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


class RouterBoardBackend:
    """B4/B5: tools → HostRouter (mock / serial / real)."""

    def __init__(self, router: Any | None = None) -> None:
        from host.router import make_router_from_env

        self.router = router or make_router_from_env()
        self._uno_close = getattr(self.router.uno, "close", None)

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
        if callable(self._uno_close):
            self._uno_close()


def make_backend(kind: str | None = None) -> BoardBackend:
    mode = (kind or AI_BACKEND or "mock").strip().lower()
    if mode in ("serial", "uno", "bridge"):
        return SerialBoardBackend()
    if mode in ("real", "board", "hw", "router"):
        return RouterBoardBackend()
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


def _chat_token_stream(
    messages: list[dict[str, Any]],
) -> Iterator[str]:
    """A6b: Ollama stream=True — yield từng mảnh content (không tools)."""
    body: dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
    }
    with requests.post(
        f"{OLLAMA_HOST}/api/chat", json=body, timeout=120, stream=True
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            part = ((chunk.get("message") or {}).get("content")) or ""
            if part:
                yield part


_SENTENCE_END = re.compile(r"(?<=[.!?…。！？\n])\s+")


def iter_sentences_from_tokens(tokens: Iterator[str]) -> Iterator[str]:
    """Gom token → cắt câu để TTS sớm (A6b)."""
    buf = ""
    for tok in tokens:
        buf += tok
        while True:
            m = _SENTENCE_END.search(buf)
            if not m:
                # Câu ngắn không dấu: cắt khi đủ dài + khoảng trắng
                if len(buf) >= 48 and " " in buf[20:]:
                    cut = buf.rfind(" ", 0, 64)
                    if cut > 12:
                        yield buf[:cut].strip()
                        buf = buf[cut + 1 :]
                        continue
                break
            sentence = buf[: m.start()].strip()
            buf = buf[m.end() :]
            if sentence:
                yield sentence
    tail = buf.strip()
    if tail:
        yield tail


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
        from ai.fast_path import get_environment_cached

        data, hit = get_environment_cached(backend.get_env)
        if hit:
            print("[tool] get_environment (cache hit)", flush=True)
        # B8: đất khô → tưới có hạn (SOIL_AUTO_WATER=1)
        auto = os.getenv("SOIL_AUTO_WATER", "0").strip().lower() not in (
            "0",
            "false",
            "no",
            "",
        )
        if auto and data.get("ok"):
            router = getattr(backend, "router", None)
            if router is not None:
                from host.soil import maybe_water_if_dry

                water = maybe_water_if_dry(router, data)
                if water.get("action") == "pump":
                    data = {**data, "auto_water": water}
                    print(f"[soil] auto pump {water.get('seconds')}s", flush=True)
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


def _prepare_messages(
    user_text: str, backend: BoardBackend
) -> tuple[list[dict[str, Any]], str | None]:
    """Chạy tool rounds (blocking). Trả (messages sẵn stream, content sớm nếu có)."""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": user_text},
    ]
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
        return messages, None

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
            return messages, None

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
        return messages, None

    early = (msg.get("content") or "").strip()
    return messages, early or None


def ask(user_text: str, backend: BoardBackend | None = None) -> str:
    """Hỏi AI; tool → mock hoặc Serial tùy backend. A4: style qua system_prompt()."""
    return " ".join(ask_sentences(user_text, backend=backend)).strip()


def ask_sentences(
    user_text: str, backend: BoardBackend | None = None
) -> Iterator[str]:
    """A6b: sau tool (nếu có), stream câu trả lời — TTS overlap được."""
    import time

    from ai.fast_path import LAST_ASK_STATS, reset_stats, try_fast_reply

    own = backend is None
    if own:
        backend = make_backend()
    assert backend is not None

    stats = reset_stats()
    t0 = time.time()
    try:
        # Fast path: lệnh cứng / env — không Ollama
        fast = try_fast_reply(
            user_text,
            set_relay=backend.set_relay,
            set_pump=backend.set_pump,
            get_env=backend.get_env,
        )
        if fast:
            stats.path = "fast"
            stats.cache_hit = LAST_ASK_STATS.cache_hit
            stats.tool_s = time.time() - t0
            stats.first_token_s = stats.tool_s
            print(
                f"[ask] path=fast tool_s={stats.tool_s:.3f}s "
                f"cache_hit={stats.cache_hit}",
                flush=True,
            )
            yield fast
            return

        stats.path = "llm"
        t_tools = time.time()
        messages, early = _prepare_messages(user_text, backend)
        stats.tool_s = time.time() - t_tools

        def _mark_first() -> Iterator[str]:
            first = True
            # Lượt đầu đã có chữ, không tool → không gọi model lần nữa
            src: Iterator[str]
            if early and len(messages) == 2:
                src = iter_sentences_from_tokens(iter([early]))
            else:
                src = iter_sentences_from_tokens(_chat_token_stream(messages))
            for sent in src:
                if first:
                    stats.first_token_s = time.time() - t0
                    print(
                        f"[ask] path=llm tool_s={stats.tool_s:.3f}s "
                        f"first_token_s={stats.first_token_s:.3f}s",
                        flush=True,
                    )
                    first = False
                yield sent

        yield from _mark_first()
    finally:
        stats.total_s = time.time() - t0
        LAST_ASK_STATS.path = stats.path
        LAST_ASK_STATS.tool_s = stats.tool_s
        LAST_ASK_STATS.first_token_s = stats.first_token_s
        LAST_ASK_STATS.total_s = stats.total_s
        LAST_ASK_STATS.cache_hit = stats.cache_hit
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
