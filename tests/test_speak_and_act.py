"""A7 DoD: speak_and_act → led + motion + TTS; không gửi esp32 qua Uno Serial."""

from __future__ import annotations

import json
import unittest

from ai.chat_env import HostBoardBackend, run_tool
from host.mock_boards import MockEsp32, MockUno
from host.router import HostRouter, MockEsp32Transport, make_mock_router
from host.speak_act import infer_emotion, speak_and_act
from tests.test_host_router import FakeSerial, RecordingTransport, SerialGuardedUnoTransport


class TestSpeakAndActA7(unittest.TestCase):
    def test_splits_emotion_motion_and_tts(self) -> None:
        spoken: list[str] = []
        uno = RecordingTransport("uno", MockUno())
        esp = RecordingTransport("esp32", MockEsp32())
        router = HostRouter(uno=uno, esp32=esp)

        out = speak_and_act(
            router,
            text="Đất khô, mình tưới 2 giây.",
            emotion="alert",
            motion="nod",
            speak_fn=lambda t: spoken.append(t) or t,
            cmd_id="9",
        )

        self.assertTrue(out["ok"])
        self.assertEqual(out["from"], "host")
        self.assertEqual(spoken, ["Đất khô, mình tưới 2 giây."])
        # Mặc định ESP32_LED_FACE_ONLY=0 → một lệnh motion (ổn định firmware cũ)
        self.assertEqual(len(esp.received), 1)
        self.assertEqual(esp.received[0]["cmd"], "motion")
        self.assertEqual(esp.received[0]["name"], "nod")
        self.assertEqual(uno.received, [])

    def test_face_only_sends_led_then_motion(self) -> None:
        import host.speak_act as sa

        prev = sa.LED_FACE_ONLY
        sa.LED_FACE_ONLY = True
        try:
            esp = RecordingTransport("esp32", MockEsp32())
            router = HostRouter(
                uno=RecordingTransport("uno", MockUno()), esp32=esp
            )
            out = speak_and_act(
                router,
                text="ok",
                emotion="alert",
                motion="nod",
                speak_fn=None,
            )
            self.assertTrue(out["ok"])
            self.assertEqual(
                [m["cmd"] for m in esp.received], ["led", "motion"]
            )
        finally:
            sa.LED_FACE_ONLY = prev

    def test_host_dispatch_speak_and_act(self) -> None:
        spoken: list[str] = []
        router = make_mock_router(speak_fn=lambda t: spoken.append(t) or t)
        out = router.dispatch(
            {
                "v": 1,
                "id": "9",
                "to": "host",
                "cmd": "speak_and_act",
                "text": "Đã bật đèn.",
                "emotion": "happy",
                "motion": "nod",
            }
        )
        self.assertTrue(out["ok"])
        self.assertEqual(spoken, ["Đã bật đèn."])
        self.assertEqual(out["emotion"], "happy")

    def test_esp32_still_not_on_uno_serial(self) -> None:
        fake = FakeSerial()
        router = HostRouter(
            uno=SerialGuardedUnoTransport(fake),
            esp32=MockEsp32Transport(),
        )
        router.dispatch(
            {
                "v": 1,
                "id": "9",
                "to": "host",
                "cmd": "speak_and_act",
                "text": "ok",
                "emotion": "listening",
            }
        )
        self.assertEqual(fake.writes, [])

    def test_bad_emotion_rejected(self) -> None:
        router = make_mock_router()
        out = speak_and_act(
            router, text="x", emotion="angry", motion="nod", speak_fn=None
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "bad_args")

    def test_infer_alert(self) -> None:
        self.assertEqual(infer_emotion("Cảnh báo đất khô"), "alert")
        self.assertEqual(infer_emotion("Mình vui quá"), "happy")


class TestOttoTool(unittest.TestCase):
    def test_otto_act_tool(self) -> None:
        backend = HostBoardBackend(kind="mock")
        raw = run_tool(
            "otto_act", {"emotion": "happy", "motion": "shake"}, backend
        )
        data = json.loads(raw)
        self.assertTrue(data["ok"])
        self.assertEqual(data["emotion"], "happy")
        backend.close()


if __name__ == "__main__":
    unittest.main()
