"""Uno transport — bọc SerialBridge cho HostRouter."""

from __future__ import annotations

from typing import Any


class UnoSerialTransport:
    name = "uno"

    def __init__(self, bridge: Any | None = None) -> None:
        from serial_bridge import SerialBridge

        self._own = bridge is None
        self.bridge = bridge or SerialBridge()
        if self._own:
            self.bridge.open()

    def send(self, msg: dict[str, Any]) -> dict[str, Any]:
        return self.bridge.request(msg)

    def close(self) -> None:
        if self._own:
            self.bridge.close()
