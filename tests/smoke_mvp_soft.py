"""Smoke soft (không cần board): DeepSeek + tools mock/fallback + TTS synth.

Chạy:
  source .venv/bin/activate
  python -m tests.smoke_mvp_soft
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.chdir(ROOT)


def _ok(label: str, detail: str = "") -> None:
    print(f"OK  {label}" + (f" — {detail}" if detail else ""))


def _fail(label: str, detail: str) -> None:
    print(f"FAIL {label} — {detail}")


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")

    fails = 0
    print("=== MVP soft smoke (no board) ===")

    # 1) unit
    import unittest

    suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if result.wasSuccessful():
        _ok("unittest", f"{result.testsRun} tests")
    else:
        _fail("unittest", f"failures={len(result.failures)} errors={len(result.errors)}")
        fails += 1

    # 2) live soft-fallback
    from host.router import make_live_router

    os.environ["UNO_PORT"] = "/dev/cu.usbserial-DOES-NOT-EXIST"
    os.environ["ESP32_PORT"] = "/dev/cu.usbserial-ALSO-MISSING"
    os.environ["ESP32_TRANSPORT"] = "serial"
    router = make_live_router()
    ack = router.dispatch({"v": 1, "id": "s1", "to": "uno", "cmd": "get_env"})
    if ack.get("ok"):
        _ok("serial→mock fallback", f"temp={ack.get('temp')}")
    else:
        _fail("serial→mock fallback", str(ack))
        fails += 1

    # 3) DeepSeek
    from ai.chat_env import LLM_PROVIDER, ask, make_backend

    if LLM_PROVIDER != "deepseek":
        _fail("deepseek provider", f"LLM_PROVIDER={LLM_PROVIDER} (cần deepseek)")
        fails += 1
    else:
        backend = make_backend("mock")
        t0 = time.time()
        try:
            reply = ask("Trả lời đúng 1 câu tiếng Việt: bạn là ai?", backend=backend)
            _ok("deepseek chat", f"{time.time() - t0:.1f}s | {reply[:80]}")
        except Exception as exc:
            _fail("deepseek chat", f"{type(exc).__name__}: {exc}")
            fails += 1
        t1 = time.time()
        try:
            reply2 = ask("Nhiệt độ và độ ẩm hiện tại?", backend=backend)
            _ok("deepseek tool", f"{time.time() - t1:.1f}s | {reply2[:80]}")
        except Exception as exc:
            _fail("deepseek tool", f"{type(exc).__name__}: {exc}")
            fails += 1

    # 4) TTS synth (không bắt buộc phát loa)
    from voice.tts import synthesize

    t2 = time.time()
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            path = Path(tmp.name)
        synthesize("Xin chào, kiểm tra TTS Jarvis.", path)
        size = path.stat().st_size
        path.unlink(missing_ok=True)
        if size > 500:
            _ok("tts synth", f"{time.time() - t2:.1f}s | {size} bytes")
        else:
            _fail("tts synth", f"file quá nhỏ: {size}")
            fails += 1
    except Exception as exc:
        _fail("tts synth", f"{type(exc).__name__}: {exc}")
        fails += 1

    print("===", "PASS" if fails == 0 else f"{fails} FAIL", "===")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
