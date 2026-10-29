"""A2 DoD: to:uno ≠ to:esp32; JSON ESP32 không đi qua Serial."""

from __future__ import annotations

import json
import unittest
from typing import Any

from host.mock_boards import MockEsp32, MockUno
from host.router import HostRouter, MockEsp32Transport, MockUnoTransport, make_mock_router


class RecordingTransport:
    """Ghi lại mọi msg đã nhận — dùng assert đường đi."""

    def __init__(self, name: str, inner: Any) -> None:
        self.name = name
        self.inner = inner
        self.received: list[dict[str, Any]] = []

    def send(self, msg: dict[str, Any]) -> dict[str, Any]:
        self.received.append(msg)
        return self.inner.handle(msg)


class FakeSerial:
    """Giả Serial: nếu router lỡ gửi ESP32 qua đây → test fail."""

    def __init__(self) -> None:
        self.writes: list[str] = []

    def write_json(self, msg: dict[str, Any]) -> None:
        self.writes.append(json.dumps(msg, separators=(",", ":")))


class SerialGuardedUnoTransport:
    """Transport Uno gắn FakeSerial — chứng minh chỉ Uno mới ghi Serial."""

    name = "uno"

    def __init__(self, serial: FakeSerial, board: MockUno | None = None) -> None:
        self.serial = serial
        self.board = board or MockUno()

    def send(self, msg: dict[str, Any]) -> dict[str, Any]:
        self.serial.write_json(msg)
        return self.board.handle(msg)


class TestHostRouterA2(unittest.TestCase):
    def test_uno_and_esp32_use_different_transports(self) -> None:
        uno_rec = RecordingTransport("uno", MockUno())
        esp_rec = RecordingTransport("esp32", MockEsp32())
        router = HostRouter(uno=uno_rec, esp32=esp_rec)

        router.dispatch(
            {"v": 1, "id": "u1", "to": "uno", "cmd": "get_env"}
        )
        router.dispatch(
            {
                "v": 1,
                "id": "e1",
                "to": "esp32",
                "cmd": "led",
                "state": "listening",
            }
        )

        self.assertEqual(len(uno_rec.received), 1)
        self.assertEqual(uno_rec.received[0]["to"], "uno")
        self.assertEqual(uno_rec.received[0]["cmd"], "get_env")

        self.assertEqual(len(esp_rec.received), 1)
        self.assertEqual(esp_rec.received[0]["to"], "esp32")
        self.assertEqual(esp_rec.received[0]["cmd"], "led")

        # Không lẫn đường
        self.assertTrue(all(m["to"] == "uno" for m in uno_rec.received))
        self.assertTrue(all(m["to"] == "esp32" for m in esp_rec.received))

    def test_esp32_never_writes_serial(self) -> None:
        fake = FakeSerial()
        router = HostRouter(
            uno=SerialGuardedUnoTransport(fake),
            esp32=MockEsp32Transport(),
        )

        out = router.dispatch(
            {
                "v": 1,
                "id": "1",
                "to": "esp32",
                "cmd": "motion",
                "name": "nod",
            }
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["from"], "esp32")
        self.assertEqual(fake.writes, [], "JSON ESP32 không được ghi Serial")

        # Uno vẫn được phép ghi Serial
        router.dispatch({"v": 1, "id": "3", "to": "uno", "cmd": "get_env"})
        self.assertEqual(len(fake.writes), 1)
        self.assertIn('"to":"uno"', fake.writes[0])
        self.assertNotIn('"to":"esp32"', fake.writes[0])

    def test_make_mock_router_get_env_and_led(self) -> None:
        router = make_mock_router()
        env = router.dispatch(
            {"v": 1, "id": "3", "to": "uno", "cmd": "get_env"}
        )
        self.assertTrue(env["ok"])
        self.assertEqual(env["from"], "uno")
        self.assertIn("temp", env)

        led = router.dispatch(
            {
                "v": 1,
                "id": "1",
                "to": "esp32",
                "cmd": "led",
                "state": "happy",
            }
        )
        self.assertEqual(
            led,
            {
                "v": 1,
                "id": "1",
                "from": "esp32",
                "ok": True,
                "state": "happy",
            },
        )

    def test_bad_to_rejected_by_host(self) -> None:
        router = make_mock_router()
        out = router.dispatch({"v": 1, "id": "x", "to": "serial", "cmd": "led"})
        self.assertFalse(out["ok"])
        self.assertEqual(out["from"], "host")
        self.assertEqual(out["error"], "bad_args")


if __name__ == "__main__":
    unittest.main()
