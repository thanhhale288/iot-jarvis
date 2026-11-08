"""A7/B7 speak_and_act + B8 soil rule (mock)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import host.soil as soil_mod
from host.mock_boards import MockUno
from host.router import HostRouter, MockEsp32Transport, MockUnoTransport, make_mock_router
from host.soil import maybe_water_if_dry
from host.speak_act import speak_and_act


class TestSpeakAndAct(unittest.TestCase):
    def test_speak_and_act_led(self) -> None:
        router = make_mock_router()
        out = speak_and_act(
            router, text="Xin chào", emotion="happy", motion="happy"
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["text"], "Xin chào")
        self.assertEqual(out["emotion"], "happy")
        self.assertEqual(out["motion"], "happy")
        # ESP32_LED_FACE_ONLY=0 → một lệnh motion; led có thể None
        if out.get("led") is not None:
            self.assertEqual(out["led"].get("state"), "happy")
        else:
            self.assertTrue((out.get("motion_ack") or {}).get("ok"))

    def test_host_cmd_speak_and_act(self) -> None:
        router = make_mock_router()
        out = router.dispatch(
            {
                "v": 1,
                "id": "9",
                "to": "host",
                "cmd": "speak_and_act",
                "text": "Đất khô, mình tưới 2 giây.",
                "emotion": "alert",
                "motion": "nod",
            }
        )
        self.assertTrue(out.get("ok"))
        self.assertEqual(out.get("id"), "9")
        self.assertEqual(out.get("emotion"), "alert")


class TestSoilRule(unittest.TestCase):
    def setUp(self) -> None:
        soil_mod._last_water_at = 0.0
        soil_mod._dry_streak = 0
        soil_mod._pump_on = False

    def test_moist_skip(self) -> None:
        uno = MockUno(env={"temp": 28.0, "hum": 60.0, "light": 400, "soil": 500})
        router = HostRouter(uno=MockUnoTransport(uno), esp32=MockEsp32Transport())
        with patch.object(soil_mod, "SOIL_TRIGGER", "dry"):
            out = maybe_water_if_dry(router, force=True)
        self.assertEqual(out["action"], "skip")
        self.assertEqual(out["reason"], "moist_enough")

    def test_dry_pumps(self) -> None:
        uno = MockUno(env={"temp": 28.0, "hum": 60.0, "light": 400, "soil": 950})
        router = HostRouter(uno=MockUnoTransport(uno), esp32=MockEsp32Transport())
        with patch.object(soil_mod, "SOIL_TRIGGER", "dry"):
            with patch.object(soil_mod, "SOIL_PUMP_SECONDS", 2):
                out = maybe_water_if_dry(router, force=True)
        self.assertEqual(out["action"], "pump")
        self.assertTrue(out["pump"].get("ok"))
        self.assertEqual(out["pump"].get("seconds"), 2)


if __name__ == "__main__":
    unittest.main()
