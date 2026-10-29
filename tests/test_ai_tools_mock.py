"""A3 DoD: get_environment / set_relay / set_pump qua mock, không Serial."""

from __future__ import annotations

import json
import unittest

from ai.chat_env import MockBoardBackend, make_backend, run_tool
from host.mock_boards import SAMPLE_ENV


class TestAiToolsMockA3(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = MockBoardBackend()

    def test_get_environment_no_serial(self) -> None:
        raw = run_tool("get_environment", {}, self.backend)
        data = json.loads(raw)
        self.assertTrue(data["ok"])
        self.assertEqual(data["from"], "uno")
        self.assertEqual(data["temp"], SAMPLE_ENV["temp"])
        self.assertEqual(data["hum"], SAMPLE_ENV["hum"])

    def test_set_relay_light_on(self) -> None:
        raw = run_tool("set_relay", {"name": "light", "on": True}, self.backend)
        data = json.loads(raw)
        self.assertTrue(data["ok"])
        self.assertEqual(data["id"], "light")
        self.assertTrue(data["on"])

    def test_set_pump(self) -> None:
        raw = run_tool("set_pump", {"on": True, "seconds": 3}, self.backend)
        data = json.loads(raw)
        self.assertTrue(data["ok"])
        self.assertTrue(data["on"])
        self.assertEqual(data["seconds"], 3)

    def test_make_backend_default_is_mock(self) -> None:
        b = make_backend("mock")
        self.assertIsInstance(b, MockBoardBackend)
        self.assertTrue(b.get_env()["ok"])
        b.close()

    def test_unknown_tool(self) -> None:
        data = json.loads(run_tool("nope", {}, self.backend))
        self.assertFalse(data["ok"])
        self.assertIn("unknown_tool", data["error"])


if __name__ == "__main__":
    unittest.main()
