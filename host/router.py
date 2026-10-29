"""Host router — đọc `to`, gửi đúng đường (plan-soft A2 / PROTOCOL §5).

  to:uno    → transport Uno (Serial thật hoặc mock)
  to:esp32  → transport ESP32 (Wi‑Fi thật hoặc mock)

Không bao giờ đưa JSON `to:esp32` vào Serial.
"""

from __future__ import annotations

import json
from typing import Any, Protocol

from host.mock_boards import MockEsp32, MockUno, _err


class Transport(Protocol):
    """Một đường tới một board. `send` nhận object JSON, trả object JSON."""

    name: str

    def send(self, msg: dict[str, Any]) -> dict[str, Any]: ...


class MockUnoTransport:
    """Uno qua mock (A1/A2 offline)."""

    name = "uno"

    def __init__(self, board: MockUno | None = None) -> None:
        self.board = board or MockUno()

    def send(self, msg: dict[str, Any]) -> dict[str, Any]:
        return self.board.handle(msg)


class MockEsp32Transport:
    """ESP32 qua mock (A1/A2 offline) — không đụng Serial."""

    name = "esp32"

    def __init__(self, board: MockEsp32 | None = None) -> None:
        self.board = board or MockEsp32()

    def send(self, msg: dict[str, Any]) -> dict[str, Any]:
        return self.board.handle(msg)


class HostRouter:
    def __init__(self, uno: Transport, esp32: Transport) -> None:
        self.uno = uno
        self.esp32 = esp32

    def dispatch(self, msg: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(msg, dict):
            return {"v": 1, "from": "host", "ok": False, "error": "bad_args"}
        to = msg.get("to")
        if to == "uno":
            return self.uno.send(msg)
        if to == "esp32":
            # Cấm Serial: chỉ gọi transport esp32
            return self.esp32.send(msg)
        if to == "host":
            return _err(msg, "host", "unknown_cmd")
        return _err(msg, "host", "bad_args")

    def dispatch_line(self, line: str) -> str:
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
        return json.dumps(self.dispatch(msg), separators=(",", ":"))


def make_mock_router() -> HostRouter:
    """Router offline mặc định (A2 + nền A3)."""
    return HostRouter(uno=MockUnoTransport(), esp32=MockEsp32Transport())
