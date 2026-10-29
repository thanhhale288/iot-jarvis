"""Mock Uno + ESP32 — NDJSON đúng docs/PROTOCOL.md (plan-soft A1).

Không cần Serial/Wi‑Fi. Một dòng JSON vào → một dòng JSON ra.
"""

from __future__ import annotations

import json
import sys
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
RELAY_IDS = frozenset({"light", "fan"})

# Sample get_env (PROTOCOL §4) — số cố định để test ổn định
SAMPLE_ENV = {
    "temp": 28.4,
    "hum": 61.0,
    "light": 420,
    "soil": 610,
}


def _base(msg: dict[str, Any], board: str, ok: bool, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"v": 1, "from": board, "ok": ok}
    if "id" in msg and msg["id"] is not None:
        out["id"] = msg["id"]
    out.update(extra)
    return out


def _err(msg: dict[str, Any], board: str, error: str) -> dict[str, Any]:
    return _base(msg, board, False, error=error)


class MockEsp32:
    """ACK led / motion / ping; lệnh lạ → unknown_cmd; args sai → bad_args."""

    def handle(self, msg: dict[str, Any]) -> dict[str, Any]:
        cmd = msg.get("cmd")
        if cmd == "ping":
            return _base(msg, "esp32", True)
        if cmd == "led":
            state = msg.get("state")
            if state not in LED_STATES:
                return _err(msg, "esp32", "bad_args")
            return _base(msg, "esp32", True, state=state)
        if cmd == "motion":
            name = msg.get("name")
            if name not in MOTION_NAMES:
                return _err(msg, "esp32", "bad_args")
            return _base(msg, "esp32", True, name=name)
        return _err(msg, "esp32", "unknown_cmd")


class MockUno:
    """get_env mẫu; relay/pump khóa tên; lệnh lạ → unknown_cmd."""

    def __init__(self, env: dict[str, Any] | None = None) -> None:
        self.env = dict(env or SAMPLE_ENV)

    def handle(self, msg: dict[str, Any]) -> dict[str, Any]:
        cmd = msg.get("cmd")
        if cmd == "get_env":
            return _base(msg, "uno", True, **self.env)
        if cmd == "relay":
            # PROTOCOL ví dụ trùng key `id`; tool/Serial dùng `name` = light|fan
            rid = msg.get("name")
            if rid not in RELAY_IDS:
                cand = msg.get("id")
                rid = cand if cand in RELAY_IDS else rid
            on = msg.get("on")
            if rid not in RELAY_IDS or not isinstance(on, bool):
                return _err(msg, "uno", "bad_args")
            return _base(msg, "uno", True, id=rid, on=on)
        if cmd == "pump":
            on = msg.get("on")
            if not isinstance(on, bool):
                return _err(msg, "uno", "bad_args")
            seconds = msg.get("seconds", 2)
            if not isinstance(seconds, int) or seconds < 1 or seconds > 5:
                return _err(msg, "uno", "bad_args")
            return _base(msg, "uno", True, on=on, seconds=seconds)
        return _err(msg, "uno", "unknown_cmd")


class MockBoards:
    """Router mỏng A1. Production path: `host.router.HostRouter` (A2)."""

    def __init__(
        self,
        esp32: MockEsp32 | None = None,
        uno: MockUno | None = None,
    ) -> None:
        self.esp32 = esp32 or MockEsp32()
        self.uno = uno or MockUno()

    def handle_msg(self, msg: dict[str, Any]) -> dict[str, Any]:
        to = msg.get("to")
        if to == "esp32":
            return self.esp32.handle(msg)
        if to == "uno":
            return self.uno.handle(msg)
        # Không biết đích → lỗi từ host (vẫn đúng phong bì)
        return _err(msg, "host", "bad_args")

    def handle_line(self, line: str) -> str:
        """Một dòng NDJSON vào → một dòng NDJSON ra (không pretty-print)."""
        line = line.strip()
        if not line:
            return json.dumps(
                {"v": 1, "from": "host", "ok": False, "error": "bad_args"},
                separators=(",", ":"),
            )
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            return json.dumps(
                {"v": 1, "from": "host", "ok": False, "error": "bad_args"},
                separators=(",", ":"),
            )
        if not isinstance(msg, dict):
            return json.dumps(
                {"v": 1, "from": "host", "ok": False, "error": "bad_args"},
                separators=(",", ":"),
            )
        return json.dumps(self.handle_msg(msg), separators=(",", ":"))


def main(argv: list[str] | None = None) -> int:
    """CLI: mỗi dòng stdin → một dòng stdout (demo A1)."""
    boards = MockBoards()
    args = argv if argv is not None else sys.argv[1:]
    if args:
        for raw in args:
            print(boards.handle_line(raw), flush=True)
        return 0
    for line in sys.stdin:
        print(boards.handle_line(line), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
