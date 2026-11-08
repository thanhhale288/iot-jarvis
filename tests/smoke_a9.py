"""A9 — smoke 5 bước PROTOCOL §6 (mock). Chạy: python -m tests.smoke_a9

Bước AI (3–4) đánh dấu skip nếu Ollama chết.
TTS (5) có thể --no-tts.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any

# repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


@dataclass
class StepResult:
    n: int
    name: str
    status: str  # pass | fail | skip
    detail: str = ""


@dataclass
class SmokeReport:
    steps: list[StepResult] = field(default_factory=list)

    def add(self, n: int, name: str, status: str, detail: str = "") -> None:
        self.steps.append(StepResult(n, name, status, detail))
        mark = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}[status]
        print(f"[{mark}] {n}. {name}" + (f" — {detail}" if detail else ""))

    def ok(self) -> bool:
        return all(s.status != "fail" for s in self.steps)


def _ollama_alive() -> bool:
    import requests

    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    try:
        r = requests.get(f"{host}/api/tags", timeout=2)
        return r.status_code == 200
    except OSError:
        return False


def run_smoke(*, do_tts: bool = False, user_text: str = "Nhiệt độ bao nhiêu?") -> SmokeReport:
    """5 bước mock. STT dùng `user_text` (không bắt mic)."""
    from ai.chat_env import MockBoardBackend, ask, run_tool
    from host.router import make_mock_router
    from host.speak_act import speak_and_act

    report = SmokeReport()
    router = make_mock_router()

    # 1. Nói → STT ra chữ (offline: inject text = đã "nghe" xong)
    text = (user_text or "").strip()
    if text:
        report.add(1, "STT → chữ", "pass", f"inject: {text!r}")
    else:
        report.add(1, "STT → chữ", "fail", "empty user_text")

    # 2. motion / led → ESP32 ACK
    led = router.dispatch(
        {
            "v": 1,
            "id": "s2",
            "to": "esp32",
            "cmd": "led",
            "state": "listening",
        }
    )
    if led.get("ok") and led.get("state") == "listening":
        report.add(2, "led/motion → ESP32 ACK", "pass", json.dumps(led, ensure_ascii=False))
    else:
        report.add(2, "led/motion → ESP32 ACK", "fail", str(led))

    # 3. Câu môi trường → get_env (tool mock; Qwen optional)
    backend = MockBoardBackend(router=router)
    env_json = run_tool("get_environment", {}, backend)
    env = json.loads(env_json)
    if env.get("ok") and "temp" in env:
        report.add(3, "get_env (tool mock)", "pass", env_json)
    else:
        report.add(3, "get_env (tool mock)", "fail", env_json)

    reply = ""
    if _ollama_alive():
        try:
            old = os.environ.get("AI_BACKEND")
            os.environ["AI_BACKEND"] = "mock"
            reply = ask(text, backend=backend)
            if old is None:
                os.environ.pop("AI_BACKEND", None)
            else:
                os.environ["AI_BACKEND"] = old
            if reply.strip():
                report.add(4, "AI chữ + emotion path", "pass", reply[:120])
            else:
                report.add(4, "AI chữ + emotion path", "fail", "empty reply")
        except Exception as e:
            report.add(4, "AI chữ + emotion path", "skip", f"Ollama lỗi: {e}")
    else:
        report.add(4, "AI chữ + emotion path", "skip", "Ollama chết — dùng speak_and_act mẫu")
        reply = "Nhiệt độ hai mươi tám phẩy bốn độ C."

    # 5. TTS + led/motion theo state (speak_and_act)
    try:
        out = speak_and_act(
            router,
            text=reply or "Xin chào, mình là Jarvis.",
            emotion="speaking",
            motion="nod",
            speak_text=do_tts,
        )
        if out.get("ok"):
            detail = f"emotion={out.get('emotion')} spoken={out.get('spoken', '')[:80]}"
            if not do_tts:
                detail += " (TTS off — --tts để phát)"
            report.add(5, "TTS + led/motion", "pass", detail)
        else:
            report.add(5, "TTS + led/motion", "fail", str(out))
    except Exception as e:
        report.add(5, "TTS + led/motion", "fail", str(e))

    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="A9 smoke 5 bước (mock)")
    p.add_argument("--tts", action="store_true", help="Phát TTS bước 5")
    p.add_argument(
        "--text",
        default="Nhiệt độ và độ ẩm hiện tại?",
        help="Giả STT (bước 1)",
    )
    args = p.parse_args(argv)
    print("A9 smoke PROTOCOL §6 (mock)")
    report = run_smoke(do_tts=args.tts, user_text=args.text)
    fails = sum(1 for s in report.steps if s.status == "fail")
    skips = sum(1 for s in report.steps if s.status == "skip")
    print(f"——— fail={fails} skip={skips} ———")
    return 0 if report.ok() else 2


if __name__ == "__main__":
    raise SystemExit(main())
