"""Host router — đọc `to`, gửi đúng đường (plan-soft A2 / A7 / PROTOCOL §5).

  to:uno    → transport Uno (Serial thật hoặc mock)
  to:esp32  → transport ESP32 (Serial Otto / Wi‑Fi sau / mock)
  to:host   → speak_and_act (A7)

Không bao giờ đưa JSON `to:esp32` vào Serial Uno.
"""

from __future__ import annotations

import json
import os
from typing import Any, Protocol

from dotenv import load_dotenv

from host.mock_boards import MockEsp32, MockUno, _err
from host.speak_act import SpeakFn, handle_host_speak_and_act

load_dotenv()

def _esp32_transport_env() -> str:
    return os.getenv("ESP32_TRANSPORT", "auto").strip().lower()


def _esp32_port_env() -> str:
    return os.getenv("ESP32_PORT", "/dev/cu.usbserial-2120").strip()


# Alias đọc lúc import — test / log cũ có thể patch
ESP32_TRANSPORT = _esp32_transport_env()
ESP32_PORT = _esp32_port_env()


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

    def close(self) -> None:
        return None


class MockEsp32Transport:
    """ESP32 qua mock (A1/A2 offline) — không đụng Serial."""

    name = "esp32"

    def __init__(self, board: MockEsp32 | None = None) -> None:
        self.board = board or MockEsp32()

    def send(self, msg: dict[str, Any]) -> dict[str, Any]:
        return self.board.handle(msg)

    def close(self) -> None:
        return None


class HostRouter:
    def __init__(
        self,
        uno: Transport,
        esp32: Transport,
        speak_fn: SpeakFn | None = None,
    ) -> None:
        self.uno = uno
        self.esp32 = esp32
        self.speak_fn = speak_fn

    def set_speak_fn(self, speak_fn: SpeakFn | None) -> None:
        self.speak_fn = speak_fn

    def dispatch(self, msg: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(msg, dict):
            return {"v": 1, "from": "host", "ok": False, "error": "bad_args"}
        to = msg.get("to")
        if to == "uno":
            return self.uno.send(msg)
        if to == "esp32":
            return self.esp32.send(msg)
        if to == "host":
            cmd = msg.get("cmd")
            if cmd == "speak_and_act":
                return handle_host_speak_and_act(self, msg, self.speak_fn)
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

    def close(self) -> None:
        for t in (self.uno, self.esp32):
            close = getattr(t, "close", None)
            if callable(close):
                close()


def make_mock_router(speak_fn: SpeakFn | None = None) -> HostRouter:
    """Router offline mặc định (A2 + nền A3/A7)."""
    return HostRouter(
        uno=MockUnoTransport(),
        esp32=MockEsp32Transport(),
        speak_fn=speak_fn,
    )


def _esp32_mode() -> str:
    transport = _esp32_transport_env()
    if transport in ("serial", "mock", "wifi", "http"):
        return "http" if transport == "wifi" else transport
    # auto: URL → http; cổng USB → serial; không → mock
    url = os.getenv("ESP32_URL", "").strip()
    if url:
        return "http"
    port = _esp32_port_env()
    if port and os.path.exists(port):
        return "serial"
    return "mock"


def _open_uno_live() -> Transport:
    """Uno Serial; thiếu cổng / mở lỗi → mock (demo soft không cần board)."""
    from host.uno_serial import UnoSerialTransport

    port = os.getenv("UNO_PORT", "/dev/cu.usbserial-2120").strip()
    if port and not os.path.exists(port):
        print(f"[host] Uno {port} không có → mock", flush=True)
        return MockUnoTransport()
    try:
        uno = UnoSerialTransport()
        print(f"[host] Uno Serial {port or '(default)'}", flush=True)
        return uno
    except Exception as exc:
        print(f"[host] Uno Serial lỗi → mock: {exc}", flush=True)
        return MockUnoTransport()


def _open_esp32_live() -> Transport:
    """ESP32 HTTP/Serial; lỗi hoặc thiếu cổng → mock."""
    mode = _esp32_mode()
    port = _esp32_port_env()
    if mode == "http":
        from host.esp32_http import Esp32HttpTransport

        base = os.getenv("ESP32_URL", "http://192.168.15.165").rstrip("/")
        print(f"[host] ESP32 HTTP {base}/cmd", flush=True)
        return Esp32HttpTransport(base_url=base)
    if mode == "serial":
        if port and not os.path.exists(port):
            print(f"[host] ESP32 {port} không có → mock", flush=True)
            return MockEsp32Transport()
        try:
            from host.esp32_serial import Esp32SerialTransport

            esp32 = Esp32SerialTransport(port=port)
            print(f"[host] ESP32 Serial {port}", flush=True)
            return esp32
        except Exception as exc:
            print(f"[host] ESP32 Serial lỗi → mock: {exc}", flush=True)
            return MockEsp32Transport()
    print(f"[host] ESP32 transport={mode} (mock ACK)", flush=True)
    return MockEsp32Transport()


def make_live_router(speak_fn: SpeakFn | None = None) -> HostRouter:
    """Uno Serial + ESP32 HTTP/Serial/mock (B4/B7). Soft-fallback mock nếu thiếu board."""
    return HostRouter(uno=_open_uno_live(), esp32=_open_esp32_live(), speak_fn=speak_fn)


def make_router(
    kind: str | None = None, speak_fn: SpeakFn | None = None
) -> HostRouter:
    """kind: mock | serial | real | live — mặc định theo AI_BACKEND."""
    mode = (kind or os.getenv("AI_BACKEND", "mock")).strip().lower()
    if mode in ("serial", "uno", "bridge", "real", "live"):
        return make_live_router(speak_fn=speak_fn)
    return make_mock_router(speak_fn=speak_fn)


# Alias main / `python -m host --real`
make_real_router = make_live_router

