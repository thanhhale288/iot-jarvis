"""A8: enum khớp PROTOCOL; pump 1–5s; cooldown 5s → busy."""

from __future__ import annotations

import unittest

from host.mock_boards import LED_STATES, MOTION_NAMES, RELAY_IDS, MockEsp32, MockUno
from host.router import HostRouter, MockEsp32Transport, MockUnoTransport
from host.speak_act import LED_STATES as SA_LED
from host.speak_act import MOTION_NAMES as SA_MOTION


# PROTOCOL §3–4 — nguồn sự thật cho enum
PROTOCOL_LED = frozenset(
    {"idle", "listening", "thinking", "speaking", "happy", "alert"}
)
PROTOCOL_MOTION = frozenset(
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
PROTOCOL_RELAY = frozenset({"light", "fan"})


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, s: float) -> None:
        self.t += s


class TestEnumsA8(unittest.TestCase):
    def test_led_motion_relay_match_protocol(self) -> None:
        self.assertEqual(LED_STATES, PROTOCOL_LED)
        self.assertEqual(MOTION_NAMES, PROTOCOL_MOTION)
        self.assertEqual(RELAY_IDS, PROTOCOL_RELAY)
        self.assertEqual(SA_LED, PROTOCOL_LED)
        self.assertEqual(SA_MOTION, PROTOCOL_MOTION)

    def test_led_bad_args(self) -> None:
        esp = MockEsp32()
        out = esp.handle(
            {"v": 1, "id": "1", "to": "esp32", "cmd": "led", "state": "rainbow"}
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "bad_args")

    def test_motion_bad_args(self) -> None:
        esp = MockEsp32()
        out = esp.handle(
            {"v": 1, "id": "2", "to": "esp32", "cmd": "motion", "name": "dance"}
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "bad_args")


class TestPumpCooldownA8(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.uno = MockUno(clock=self.clock, cooldown_s=5.0)
        self.router = HostRouter(
            uno=MockUnoTransport(self.uno), esp32=MockEsp32Transport()
        )

    def _pump(self, on: bool, seconds: int = 2) -> dict:
        return self.router.dispatch(
            {
                "v": 1,
                "id": "p",
                "to": "uno",
                "cmd": "pump",
                "on": on,
                "seconds": seconds,
            }
        )

    def test_seconds_range(self) -> None:
        bad0 = self._pump(True, 0)
        self.assertFalse(bad0["ok"])
        self.assertEqual(bad0["error"], "bad_args")
        bad6 = self._pump(True, 6)
        self.assertFalse(bad6["ok"])
        self.assertEqual(bad6["error"], "bad_args")
        ok = self._pump(True, 1)
        self.assertTrue(ok["ok"])
        self.assertEqual(ok["seconds"], 1)

    def test_busy_while_running(self) -> None:
        self.assertTrue(self._pump(True, 2)["ok"])
        again = self._pump(True, 2)
        self.assertFalse(again["ok"])
        self.assertEqual(again["error"], "busy")

    def test_cooldown_after_timeout(self) -> None:
        self.assertTrue(self._pump(True, 2)["ok"])
        self.clock.advance(2.0)
        # service on next cmd
        busy = self._pump(True, 1)
        self.assertFalse(busy["ok"])
        self.assertEqual(busy["error"], "busy")
        self.clock.advance(5.0)
        ok = self._pump(True, 1)
        self.assertTrue(ok["ok"])

    def test_off_always_accepted(self) -> None:
        self.assertTrue(self._pump(True, 3)["ok"])
        off = self._pump(False, 2)
        self.assertTrue(off["ok"])
        # sau off → cooldown
        busy = self._pump(True, 1)
        self.assertEqual(busy.get("error"), "busy")
        self.clock.advance(5.0)
        self.assertTrue(self._pump(True, 1)["ok"])


if __name__ == "__main__":
    unittest.main()
