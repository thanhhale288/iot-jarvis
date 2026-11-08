"""A8 DoD: enum PROTOCOL + pump 1–5s + cooldown 5s → busy."""

from __future__ import annotations

import unittest
from unittest import mock

from host.mock_boards import LED_STATES, MOTION_NAMES, MockEsp32, MockUno
from host.router import make_mock_router


# Khớp docs/PROTOCOL.md §3
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


class TestProtocolEnumsA8(unittest.TestCase):
    def test_led_enum_matches_protocol(self) -> None:
        self.assertEqual(LED_STATES, PROTOCOL_LED)

    def test_motion_enum_matches_protocol(self) -> None:
        self.assertEqual(MOTION_NAMES, PROTOCOL_MOTION)

    def test_esp32_rejects_unknown_emotion(self) -> None:
        out = MockEsp32().handle(
            {"v": 1, "id": "1", "to": "esp32", "cmd": "led", "state": "angry"}
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "bad_args")

    def test_esp32_rejects_unknown_motion(self) -> None:
        out = MockEsp32().handle(
            {"v": 1, "id": "1", "to": "esp32", "cmd": "motion", "name": "fly"}
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "bad_args")


class TestPumpCooldownA8(unittest.TestCase):
    def test_seconds_out_of_range(self) -> None:
        uno = MockUno()
        bad = uno.handle(
            {"v": 1, "id": "p", "to": "uno", "cmd": "pump", "on": True, "seconds": 9}
        )
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["error"], "bad_args")

        zero = uno.handle(
            {"v": 1, "id": "p0", "to": "uno", "cmd": "pump", "on": True, "seconds": 0}
        )
        self.assertFalse(zero["ok"])

    def test_cooldown_second_on_is_busy(self) -> None:
        uno = MockUno()
        t0 = 1000.0
        with mock.patch.object(uno, "_time") as tm:
            tm.monotonic.return_value = t0
            r1 = uno.handle(
                {
                    "v": 1,
                    "id": "1",
                    "to": "uno",
                    "cmd": "pump",
                    "on": True,
                    "seconds": 2,
                }
            )
            self.assertTrue(r1["ok"])
            # Ngay sau đó vẫn trong cooldown 5s
            tm.monotonic.return_value = t0 + 1.0
            r2 = uno.handle(
                {
                    "v": 1,
                    "id": "2",
                    "to": "uno",
                    "cmd": "pump",
                    "on": True,
                    "seconds": 2,
                }
            )
            self.assertFalse(r2["ok"])
            self.assertEqual(r2["error"], "busy")
            # Sau 5s: được tưới lại
            tm.monotonic.return_value = t0 + 5.01
            r3 = uno.handle(
                {
                    "v": 1,
                    "id": "3",
                    "to": "uno",
                    "cmd": "pump",
                    "on": True,
                    "seconds": 1,
                }
            )
            self.assertTrue(r3["ok"])

    def test_router_pump_cooldown(self) -> None:
        router = make_mock_router()
        # Dùng cùng MockUno bên trong — thay board có cooldown
        from host.router import MockUnoTransport

        board = MockUno()
        router.uno = MockUnoTransport(board)
        with mock.patch.object(board, "_time") as tm:
            tm.monotonic.return_value = 50.0
            self.assertTrue(
                router.dispatch(
                    {
                        "v": 1,
                        "id": "a",
                        "to": "uno",
                        "cmd": "pump",
                        "on": True,
                        "seconds": 2,
                    }
                )["ok"]
            )
            tm.monotonic.return_value = 51.0
            busy = router.dispatch(
                {
                    "v": 1,
                    "id": "b",
                    "to": "uno",
                    "cmd": "pump",
                    "on": True,
                    "seconds": 2,
                }
            )
            self.assertEqual(busy.get("error"), "busy")


if __name__ == "__main__":
    unittest.main()
