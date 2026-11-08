"""Live router soft-fallback → mock khi thiếu cổng USB (không cần board)."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from host.router import MockEsp32Transport, MockUnoTransport, make_live_router


class TestLiveSoftFallback(unittest.TestCase):
    def test_missing_ports_use_mock(self) -> None:
        env = {
            "UNO_PORT": "/dev/cu.usbserial-DOES-NOT-EXIST",
            "ESP32_PORT": "/dev/cu.usbserial-ALSO-MISSING",
            "ESP32_TRANSPORT": "serial",
            "ESP32_URL": "",
        }
        with patch.dict(os.environ, env, clear=False):
            router = make_live_router()
        self.assertIsInstance(router.uno, MockUnoTransport)
        self.assertIsInstance(router.esp32, MockEsp32Transport)
        env_ack = router.dispatch(
            {"v": 1, "id": "t1", "to": "uno", "cmd": "get_env"}
        )
        self.assertTrue(env_ack.get("ok"))
        led = router.dispatch(
            {
                "v": 1,
                "id": "t2",
                "to": "esp32",
                "cmd": "led",
                "state": "happy",
            }
        )
        self.assertTrue(led.get("ok"))


if __name__ == "__main__":
    unittest.main()
