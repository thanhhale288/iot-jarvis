"""Host router — đọc `to`, gửi đúng đường (plan-soft A2/B4 / PROTOCOL §5).

  to:uno    → transport Uno (Serial thật hoặc mock)
  to:esp32  → transport ESP32 (Wi‑Fi thật hoặc mock)
  to:host   → speak_and_act (A7/B7)

Không bao giờ đưa JSON `to:esp32` vào Serial.
"""

from __future__ import annotations

import json
import os
from typing import Any, Protocol

from dotenv import load_dotenv

from host.mock_boards import MockEsp32, MockUno, _err
from host.speak_act import speak_and_act

load_dotenv()


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
            return self._handle_host(msg)
        return _err(msg, "host", "bad_args")

    def _handle_host(self, msg: dict[str, Any]) -> dict[str, Any]:
        cmd = msg.get("cmd")
        if cmd == "speak_and_act":
            text = msg.get("text") or ""
            if not isinstance(text, str) or not text.strip():
                return _err(msg, "host", "bad_args")
            emotion = msg.get("emotion") or "speaking"
            motion = msg.get("motion")
            out = speak_and_act(
                self,
                text=text,
                emotion=str(emotion),
                motion=str(motion) if motion else None,
                cmd_id=str(msg.get("id") or "sa"),
            )
            if "id" in msg and msg["id"] is not None:
                out["id"] = msg["id"]
            return out
        return _err(msg, "host", "unknown_cmd")

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


def make_real_router() -> HostRouter:
    """B4: Uno Serial + ESP32 HTTP hoặc Serial (`ESP32_TRANSPORT`)."""
    from host.transports import (
        ESP32_TRANSPORT,
        HttpEsp32Transport,
        SerialEsp32Transport,
        SerialUnoTransport,
    )

    if ESP32_TRANSPORT == "serial":
        esp: Transport = SerialEsp32Transport()
    else:
        esp = HttpEsp32Transport()
    return HostRouter(uno=SerialUnoTransport(), esp32=esp)


def make_router_from_env() -> HostRouter:
    """AI_BACKEND=mock|serial|real — serial=Uno thật + ESP mock; real=cả hai thật."""
    mode = os.getenv("AI_BACKEND", "mock").strip().lower()
    if mode in ("real", "board", "hw"):
        return make_real_router()
    if mode in ("serial", "uno", "bridge"):
        from host.transports import SerialUnoTransport

        return HostRouter(uno=SerialUnoTransport(), esp32=MockEsp32Transport())
    return make_mock_router()
