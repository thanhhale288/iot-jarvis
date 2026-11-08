"""Chat UI: static + API, không LLM và không loa."""

from __future__ import annotations

import json
import threading
import time
import unittest
import urllib.error
import urllib.request

import frontend.server as server


class TestFrontendChat(unittest.TestCase):
    def setUp(self) -> None:
        self.spoken: list[str] = []
        self._turn = server.execute_turn
        self._speak = server.speak_text

        def fake_turn(user_text: str | None) -> dict:
            heard = "nhiệt độ" if user_text is None else user_text
            return {
                "ok": True,
                "user_text": heard,
                "assistant_text": "Đã bật đèn.",
                "summary": "test",
            }

        def fake_speak(text: str) -> None:
            self.spoken.append(text)
            time.sleep(0.3)

        server.execute_turn = fake_turn
        server.speak_text = fake_speak
        self.httpd = server.Server(("127.0.0.1", 0), server.Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        server.execute_turn = self._turn
        server.speak_text = self._speak

    def _url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def _post(self, path: str, payload: dict) -> tuple[int, dict]:
        req = urllib.request.Request(
            self._url(path),
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as res:
                return res.status, json.loads(res.read().decode())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode())

    def test_index_has_composer(self) -> None:
        with urllib.request.urlopen(self._url("/"), timeout=5) as res:
            html = res.read().decode()
        self.assertEqual(res.status, 200)
        self.assertIn('id="input"', html)
        self.assertIn("Hỏi Jarvis", html)
        self.assertIn("/app.js", html)

    def test_chat_returns_text_then_speaks(self) -> None:
        t0 = time.time()
        code, data = self._post("/api/chat", {"text": "Bật đèn"})
        elapsed = time.time() - t0
        self.assertEqual(code, 200)
        self.assertEqual(data["user_text"], "Bật đèn")
        self.assertEqual(data["assistant_text"], "Đã bật đèn.")
        self.assertLess(elapsed, 0.25)
        deadline = time.time() + 2
        while "Đã bật đèn." not in self.spoken and time.time() < deadline:
            time.sleep(0.05)
        self.assertEqual(self.spoken, ["Đã bật đèn."])

    def test_empty_chat_rejected(self) -> None:
        code, data = self._post("/api/chat", {"text": "  "})
        self.assertEqual(code, 400)
        self.assertIn("error", data)
        self.assertEqual(self.spoken, [])

    def test_listen_uses_mic_turn(self) -> None:
        code, data = self._post("/api/listen", {})
        self.assertEqual(code, 200)
        self.assertEqual(data["user_text"], "nhiệt độ")

    def test_unknown_path_not_a_file(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(self._url("/voice/ui.py"), timeout=5)
        self.assertEqual(ctx.exception.code, 404)
