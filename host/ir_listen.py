"""C1 — lắng nghe `event` IR từ Uno, map code → lệnh.

Chạy: python -m host.ir_listen
In code khi nhấn remote lần đầu → thêm vào IR_MAP / .env IR_MAP_JSON.
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from typing import Any

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serial_bridge import SerialBridge  # noqa: E402

# Mặc định: remote NEC kit thường gặp — đổi sau khi xem log
_DEFAULT_MAP = {
    "FFA25D": {"cmd": "pump", "on": True, "seconds": 2},  # power / CH−
    "FF629D": {"cmd": "relay", "name": "light", "on": True},
    "FFE21D": {"cmd": "relay", "name": "light", "on": False},
    "FF22DD": {"cmd": "relay", "name": "fan", "on": True},
    "FF02FD": {"cmd": "relay", "name": "fan", "on": False},
}


def _load_map() -> dict[str, dict[str, Any]]:
    raw = os.getenv("IR_MAP_JSON", "").strip()
    if raw:
        data = json.loads(raw)
        return {str(k).upper(): v for k, v in data.items()}
    return dict(_DEFAULT_MAP)


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


def main() -> int:
    code_map = _load_map()
    print(f"IR map codes: {', '.join(sorted(code_map)) or '(empty — log only)'}")
    bridge = SerialBridge()
    bridge.open()
    assert bridge._ser is not None
    ser = bridge._ser
    print(f"listening {bridge.port} for IR events… (Ctrl+C stop)")
    try:
        while True:
            raw = ser.readline()
            if not raw:
                continue
            text = raw.decode("utf-8", errors="replace").strip()
            if not text.startswith("{"):
                continue
            try:
                msg = json.loads(text)
            except json.JSONDecodeError:
                continue
            if msg.get("cmd") != "event" or msg.get("name") != "ir":
                continue
            code = str(msg.get("code", "")).upper()
            print(f"IR code={code}")
            action = code_map.get(code)
            if not action:
                print("  (chưa map — thêm vào IR_MAP_JSON)")
                continue
            payload = {
                "v": 1,
                "id": _new_id(),
                "to": "uno",
                **action,
            }
            line = json.dumps(payload, separators=(",", ":")) + "\n"
            ser.write(line.encode("utf-8"))
            ser.flush()
            deadline = time.time() + 3.0
            while time.time() < deadline:
                ack_raw = ser.readline()
                if not ack_raw:
                    continue
                ack_text = ack_raw.decode("utf-8", errors="replace").strip()
                if not ack_text.startswith("{"):
                    continue
                try:
                    ack = json.loads(ack_text)
                except json.JSONDecodeError:
                    continue
                if ack.get("cmd") == "event":
                    continue
                print(f"  → {ack}")
                break
            else:
                print("  → no ACK")
    except KeyboardInterrupt:
        print("\nstop")
    finally:
        bridge.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
