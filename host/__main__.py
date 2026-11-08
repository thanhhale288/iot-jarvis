"""python -m host — A7 speak_and_act smoke (mock mặc định)."""

from __future__ import annotations

import argparse
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Host speak_and_act (A7)")
    p.add_argument("text", nargs="?", default="Xin chào, mình là Jarvis.")
    p.add_argument("--emotion", default="speaking")
    p.add_argument("--motion", default=None)
    p.add_argument("--tts", action="store_true", help="Phát TTS")
    p.add_argument(
        "--real",
        action="store_true",
        help="AI_BACKEND/real router (board)",
    )
    args = p.parse_args(argv)

    if args.real:
        from host.router import make_real_router

        router = make_real_router()
    else:
        from host.router import make_mock_router

        router = make_mock_router()

    from host.speak_act import speak_and_act

    out = speak_and_act(
        router,
        text=args.text,
        emotion=args.emotion,
        motion=args.motion,
        speak_text=args.tts,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    close_u = getattr(router.uno, "close", None)
    close_e = getattr(router.esp32, "close", None)
    if callable(close_u):
        close_u()
    if callable(close_e):
        close_e()
    return 0 if out.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
