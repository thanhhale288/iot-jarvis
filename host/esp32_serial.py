"""ESP32 transport qua USB Serial (otto_motion) — cổng riêng, không phải Uno.

PROTOCOL ưu tiên Wi‑Fi; Serial dùng khi B1 chưa có / debug Otto.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any

import serial
from dotenv import load_dotenv

load_dotenv()

DEFAULT_PORT = os.getenv("ESP32_PORT", "/dev/cu.usbserial-2120")
DEFAULT_BAUD = int(os.getenv("ESP32_BAUD", "115200"))
OPEN_DELAY_S = float(os.getenv("ESP32_OPEN_DELAY", "0.5"))
# motion/led có thể chạy servo vài giây
READ_TIMEOUT_S = float(os.getenv("ESP32_TIMEOUT", "20.0"))


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


class Esp32SerialTransport:
    """to:esp32 → USB Serial ESP32 (không đụng UNO_PORT)."""

    name = "esp32"

    def __init__(
        self,
        port: str = DEFAULT_PORT,
        baud: int = DEFAULT_BAUD,
        open_delay: float = OPEN_DELAY_S,
        timeout: float = READ_TIMEOUT_S,
    ) -> None:
        self.port = port
        self.baud = baud
        self.open_delay = open_delay
        self.timeout = timeout
        self._ser: serial.Serial | None = None

    def open(self) -> None:
        if self._ser and self._ser.is_open:
            return
        ser = serial.Serial()
        ser.port = self.port
        ser.baudrate = self.baud
        ser.timeout = self.timeout
        ser.dsrdtr = False
        ser.rtscts = False
        ser.dtr = False
        ser.rts = False
        ser.open()
        time.sleep(self.open_delay)
        ser.reset_input_buffer()
        self._ser = ser

    def close(self) -> None:
        if self._ser and self._ser.is_open:
            self._ser.close()
        self._ser = None

    def send(self, msg: dict[str, Any]) -> dict[str, Any]:
        if not msg.get("id"):
            msg = {**msg, "id": _new_id()}
        want_id = str(msg["id"])
        self.open()
        assert self._ser is not None
        line = json.dumps(msg, separators=(",", ":")) + "\n"
        # Không reset buffer: ACK lệnh trước (led chậm vì servo) sẽ bị mất
        # rồi host báo timeout dù board đã ok.
        self._ser.write(line.encode("utf-8"))
        self._ser.flush()

        deadline = time.time() + self.timeout
        while time.time() < deadline:
            raw = self._ser.readline()
            if not raw:
                continue
            text = raw.decode("utf-8", errors="replace").strip()
            if not text or text[0] != "{":
                # log dòng debug firmware (face=… / ready …)
                continue
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            if not isinstance(data, dict) or data.get("from") != "esp32":
                continue
            # Bỏ ACK lệch id (ping trễ / dòng cũ)
            got = data.get("id")
            if got is not None and str(got) != want_id:
                continue
            return data
        return {
            "v": 1,
            "id": msg.get("id"),
            "from": "esp32",
            "ok": False,
            "error": "timeout",
        }
