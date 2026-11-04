"""Transport thật: Uno Serial + ESP32 HTTP (plan-soft B4)."""

from __future__ import annotations

import json
import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

ESP32_URL = os.getenv("ESP32_URL", "http://192.168.4.1").rstrip("/")
ESP32_TIMEOUT = float(os.getenv("ESP32_TIMEOUT", "20"))
ESP32_PORT = os.getenv("ESP32_PORT", "/dev/cu.usbserial-2120")
ESP32_BAUD = int(os.getenv("ESP32_BAUD", "115200"))
ESP32_TRANSPORT = os.getenv("ESP32_TRANSPORT", "http").strip().lower()  # http|serial


class SerialUnoTransport:
    """Uno qua serial_bridge — giữ cổng, DTR/RTS false (B3)."""

    name = "uno"

    def __init__(self, bridge: Any | None = None) -> None:
        from serial_bridge import SerialBridge

        self._own = bridge is None
        self.bridge = bridge or SerialBridge()
        if self._own:
            self.bridge.open()

    def send(self, msg: dict[str, Any]) -> dict[str, Any]:
        return self.bridge.request(dict(msg))

    def close(self) -> None:
        if self._own:
            self.bridge.close()


class SerialEsp32Transport:
    """ESP32 qua USB Serial (debug / khi chưa có Wi‑Fi). Không dùng cho Uno."""

    name = "esp32"

    def __init__(
        self,
        port: str | None = None,
        baud: int | None = None,
        open_delay: float = 2.0,
        timeout: float = 8.0,
    ) -> None:
        import serial

        self.port = port or ESP32_PORT
        self.baud = baud if baud is not None else ESP32_BAUD
        self.open_delay = open_delay
        self.timeout = timeout
        self._ser: Any = None
        self._serial_mod = serial

    def open(self) -> None:
        if self._ser and self._ser.is_open:
            return
        ser = self._serial_mod.Serial()
        ser.port = self.port
        ser.baudrate = self.baud
        ser.timeout = self.timeout
        ser.dsrdtr = False
        ser.rtscts = False
        ser.dtr = False
        ser.rts = False
        ser.open()
        try:
            ser.dtr = False
            ser.rts = False
        except (OSError, ValueError, self._serial_mod.SerialException):
            pass
        import time

        time.sleep(self.open_delay)
        ser.reset_input_buffer()
        self._ser = ser

    def close(self) -> None:
        if self._ser and self._ser.is_open:
            self._ser.close()
        self._ser = None

    def send(self, msg: dict[str, Any]) -> dict[str, Any]:
        self.open()
        assert self._ser is not None
        line = json.dumps(msg, separators=(",", ":")) + "\n"
        self._ser.write(line.encode("utf-8"))
        self._ser.flush()
        # Bỏ dòng log non-JSON (face=…, event spam) đến khi gặp ACK
        import time

        deadline = time.time() + self.timeout
        while time.time() < deadline:
            raw = self._ser.readline()
            if not raw:
                continue
            text = raw.decode("utf-8", errors="replace").strip()
            if not text.startswith("{"):
                continue
            data = json.loads(text)
            # event không phải ACK lệnh
            if data.get("cmd") == "event":
                continue
            return data
        raise TimeoutError(f"timeout ESP32 Serial trên {self.port}")


class HttpEsp32Transport:
    """ESP32 qua Wi‑Fi HTTP POST /cmd (PROTOCOL §2 A / B1).

    Body = một dòng JSON (WebServer đọc `plain`).
    """

    name = "esp32"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or ESP32_URL).rstrip("/")
        self.timeout = ESP32_TIMEOUT if timeout is None else timeout

    def send(self, msg: dict[str, Any]) -> dict[str, Any]:
        line = json.dumps(msg, separators=(",", ":"))
        r = requests.post(
            f"{self.base_url}/cmd",
            data=line.encode("utf-8"),
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
        )
        r.raise_for_status()
        try:
            return r.json()
        except ValueError as e:
            raise TimeoutError(
                f"ESP32 non-JSON ({r.status_code}): {r.text[:120]}"
            ) from e

    def poll_events(self) -> list[str]:
        r = requests.get(
            f"{self.base_url}/events", timeout=min(5.0, self.timeout)
        )
        r.raise_for_status()
        data = r.json()
        return [str(x) for x in (data.get("events") or [])]

    def ping(self) -> dict[str, Any]:
        return self.send({"v": 1, "id": "0", "to": "esp32", "cmd": "ping"})
