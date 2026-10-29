"""A1 DoD: get_env, ACK led/motion, unknown_cmd đúng phong bì PROTOCOL."""

from __future__ import annotations

import json
import unittest

from host.mock_boards import MockBoards, SAMPLE_ENV


def _parse(line: str) -> dict:
    return json.loads(line)


class TestMockBoardsA1(unittest.TestCase):
    def setUp(self) -> None:
        self.boards = MockBoards()

    def test_get_env_envelope(self) -> None:
        out = _parse(
            self.boards.handle_line(
                '{"v":1,"id":"3","to":"uno","cmd":"get_env"}'
            )
        )
        self.assertEqual(out["v"], 1)
        self.assertEqual(out["id"], "3")
        self.assertEqual(out["from"], "uno")
        self.assertTrue(out["ok"])
        for key, val in SAMPLE_ENV.items():
            self.assertEqual(out[key], val)
        self.assertNotIn("error", out)

    def test_led_ack(self) -> None:
        out = _parse(
            self.boards.handle_line(
                '{"v":1,"id":"1","to":"esp32","cmd":"led","state":"listening"}'
            )
        )
        self.assertEqual(out, {
            "v": 1,
            "id": "1",
            "from": "esp32",
            "ok": True,
            "state": "listening",
        })

    def test_motion_ack(self) -> None:
        out = _parse(
            self.boards.handle_line(
                '{"v":1,"id":"2","to":"esp32","cmd":"motion","name":"nod"}'
            )
        )
        self.assertEqual(out, {
            "v": 1,
            "id": "2",
            "from": "esp32",
            "ok": True,
            "name": "nod",
        })

    def test_unknown_cmd_uno(self) -> None:
        out = _parse(
            self.boards.handle_line(
                '{"v":1,"id":"a1","to":"uno","cmd":"fly"}'
            )
        )
        self.assertEqual(out, {
            "v": 1,
            "id": "a1",
            "from": "uno",
            "ok": False,
            "error": "unknown_cmd",
        })

    def test_unknown_cmd_esp32(self) -> None:
        out = _parse(
            self.boards.handle_line(
                '{"v":1,"id":"a1","to":"esp32","cmd":"dance"}'
            )
        )
        self.assertEqual(out["ok"], False)
        self.assertEqual(out["error"], "unknown_cmd")
        self.assertEqual(out["from"], "esp32")
        self.assertEqual(out["id"], "a1")

    def test_ndjson_one_line_no_pretty(self) -> None:
        line = self.boards.handle_line(
            '{"v":1,"id":"3","to":"uno","cmd":"get_env"}'
        )
        self.assertNotIn("\n", line)
        self.assertNotIn(" ", line)  # separators compact


if __name__ == "__main__":
    unittest.main()
