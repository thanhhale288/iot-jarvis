"""B8 — đất ↔ bơm có hạn.

dry: soil >= ngưỡng (khô) → tưới.
wet (demo): soil < ngưỡng (nhúng) → bơm 3s; khô → off một lần (không spam).
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any

from dotenv import load_dotenv

load_dotenv()

SOIL_DRY_THRESHOLD = int(os.getenv("SOIL_DRY_THRESHOLD", "650"))
SOIL_PUMP_SECONDS = max(1, min(5, int(os.getenv("SOIL_PUMP_SECONDS", "3"))))
SOIL_HOST_COOLDOWN_S = float(os.getenv("SOIL_HOST_COOLDOWN_S", "2"))
SOIL_TRIGGER = os.getenv("SOIL_TRIGGER", "dry").strip().lower()
_DRY_NEEDED = int(os.getenv("SOIL_DRY_STREAK", "3"))

_last_water_at = 0.0
_dry_streak = 0
_pump_on = False  # đã bật / chưa off — tránh spam pump_off


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


def _should_pump(soil: float) -> bool:
    if SOIL_TRIGGER == "wet":
        return soil < SOIL_DRY_THRESHOLD
    return soil >= SOIL_DRY_THRESHOLD


def maybe_water_if_dry(
    router: Any,
    env: dict[str, Any] | None = None,
    *,
    force: bool = False,
) -> dict[str, Any]:
    global _last_water_at, _dry_streak, _pump_on

    if env is None:
        env = router.dispatch(
            {"v": 1, "id": _new_id(), "to": "uno", "cmd": "get_env"}
        )
    if not env.get("ok"):
        return {"ok": False, "action": "skip", "reason": "get_env_failed", "env": env}

    soil = env.get("soil")
    if not isinstance(soil, (int, float)) or soil < 0:
        return {"ok": True, "action": "skip", "reason": "no_soil", "soil": soil}

    now = time.time()
    pumping = _pump_on and (now - _last_water_at) < float(SOIL_PUMP_SECONDS)

    if not _should_pump(float(soil)):
        reason = "not_wet" if SOIL_TRIGGER == "wet" else "moist_enough"
        _dry_streak += 1
        off_ack: dict[str, Any] | None = None
        # Chỉ off MỘT lần khi đang coi là bơm/on — không spam khi đã tắt
        if (
            SOIL_TRIGGER == "wet"
            and _pump_on
            and not pumping
            and _dry_streak >= _DRY_NEEDED
        ):
            off_ack = router.dispatch(
                {
                    "v": 1,
                    "id": _new_id(),
                    "to": "uno",
                    "cmd": "pump",
                    "on": False,
                    "seconds": 1,
                }
            )
            _pump_on = False
            _dry_streak = 0
        elif _dry_streak >= _DRY_NEEDED and not _pump_on:
            _dry_streak = _DRY_NEEDED  # giữ trần, không reset vòng spam
        return {
            "ok": True,
            "action": (
                "pump_off"
                if off_ack is not None
                else ("hold_pump" if pumping else "skip")
            ),
            "reason": reason,
            "soil": soil,
            "threshold": SOIL_DRY_THRESHOLD,
            "trigger": SOIL_TRIGGER,
            "dry_streak": _dry_streak,
            "pump": off_ack,
        }

    _dry_streak = 0

    if pumping:
        return {
            "ok": True,
            "action": "hold_pump",
            "reason": "still_running",
            "soil": soil,
            "trigger": SOIL_TRIGGER,
        }

    # Hết cửa sổ bơm → coi như đã tự tắt (firmware)
    if _pump_on and (now - _last_water_at) >= float(SOIL_PUMP_SECONDS):
        _pump_on = False

    if not force and _last_water_at > 0 and (now - _last_water_at) < SOIL_HOST_COOLDOWN_S:
        return {
            "ok": True,
            "action": "skip",
            "reason": "host_cooldown",
            "soil": soil,
            "wait_s": SOIL_HOST_COOLDOWN_S - (now - _last_water_at),
            "trigger": SOIL_TRIGGER,
        }

    pump = router.dispatch(
        {
            "v": 1,
            "id": _new_id(),
            "to": "uno",
            "cmd": "pump",
            "on": True,
            "seconds": SOIL_PUMP_SECONDS,
        }
    )
    if pump.get("ok"):
        _last_water_at = now
        _pump_on = True
        return {
            "ok": True,
            "action": "pump",
            "soil": soil,
            "seconds": SOIL_PUMP_SECONDS,
            "pump": pump,
            "trigger": SOIL_TRIGGER,
        }
    return {
        "ok": False,
        "action": "pump_failed",
        "soil": soil,
        "pump": pump,
        "trigger": SOIL_TRIGGER,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    p = argparse.ArgumentParser(description="B8 đất ↔ bơm")
    p.add_argument("--watch", action="store_true")
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--force", action="store_true")
    p.add_argument("--wet", action="store_true")
    args = p.parse_args(argv)

    global SOIL_TRIGGER
    if args.wet:
        SOIL_TRIGGER = "wet"
        os.environ["SOIL_TRIGGER"] = "wet"

    from host.router import make_real_router

    router = make_real_router()
    rule = (
        f"soil < {SOIL_DRY_THRESHOLD} (ướt) → bơm"
        if SOIL_TRIGGER == "wet"
        else f"soil >= {SOIL_DRY_THRESHOLD} (khô) → bơm"
    )
    print(
        f"trigger={SOIL_TRIGGER} {rule} pump={SOIL_PUMP_SECONDS}s cooldown={SOIL_HOST_COOLDOWN_S}s",
        flush=True,
    )
    try:
        while True:
            try:
                out = maybe_water_if_dry(router, force=args.force)
                print(json.dumps(out, ensure_ascii=False), flush=True)
            except Exception as e:
                print(f"! {type(e).__name__}: {e}", flush=True)
                if not args.watch:
                    return 1
                time.sleep(max(0.5, args.interval))
                continue
            if not args.watch:
                return 0 if out.get("ok") else 2
            time.sleep(max(0.5, args.interval))
    except KeyboardInterrupt:
        print(flush=True)
        return 0
    finally:
        close_u = getattr(router.uno, "close", None)
        close_e = getattr(router.esp32, "close", None)
        if callable(close_u):
            close_u()
        if callable(close_e):
            close_e()


if __name__ == "__main__":
    raise SystemExit(main())
