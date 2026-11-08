"""ESP32 transport qua Wi‑Fi HTTP POST /cmd (PROTOCOL quy định A)."""

from __future__ import annotations

import os
import uuid
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_URL = os.getenv("ESP32_URL", "http://192.168.15.165").rstrip("/")
# motion có thể chậm
TIMEOUT_S = float(os.getenv("ESP32_TIMEOUT", "20"))


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


class Esp32HttpTransport:
    """to:esp32 → POST {ESP32_URL}/cmd."""

    name = "esp32"

    def __init__(
        self,
        base_url: str = DEFAULT_URL,
        timeout: float = TIMEOUT_S,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.cmd_url = f"{self.base_url}/cmd"

    def send(self, msg: dict[str, Any]) -> dict[str, Any]:
        if not msg.get("id"):
            msg = {**msg, "id": _new_id()}
        try:
            res = requests.post(self.cmd_url, json=msg, timeout=self.timeout)
            res.raise_for_status()
            data = res.json()
            if isinstance(data, dict):
                return data
            return {
                "v": 1,
                "id": msg.get("id"),
                "from": "esp32",
                "ok": False,
                "error": "bad_args",
            }
        except requests.Timeout:
            return {
                "v": 1,
                "id": msg.get("id"),
                "from": "esp32",
                "ok": False,
                "error": "timeout",
            }
        except (requests.RequestException, ValueError) as exc:
            return {
                "v": 1,
                "id": msg.get("id"),
                "from": "esp32",
                "ok": False,
                "error": "timeout",
                "detail": str(exc),
            }

    def close(self) -> None:
        return None
