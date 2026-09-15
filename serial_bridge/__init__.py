"""USB Serial bridge → Uno JSON (quy định C).

Mở cổng một lần, sau open đợi ~2s (Uno reset DTR), rồi gửi/nhận 1 dòng JSON.
Tuần 2: luôn gửi id; thêm set_relay / set_pump.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from typing import Any

import serial
from dotenv import load_dotenv

load_dotenv()

DEFAULT_PORT = os.getenv("UNO_PORT", "/dev/cu.usbserial-2110")
DEFAULT_BAUD = int(os.getenv("UNO_BAUD", "115200"))
OPEN_DELAY_S = float(os.getenv("UNO_OPEN_DELAY", "2.0"))
READ_TIMEOUT_S = float(os.getenv("UNO_TIMEOUT", "3.0"))


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


class SerialBridge:
    def __init__(
        self,
        port: str = DEFAULT_PORT,
        baud: int = DEFAULT_BAUD,
        open_delay: float = OPEN_DELAY_S,
        timeout: float = READ_TIMEOUT_S,
    ) -> None:
        self.port = port
        self.baud = baud
        self.open_delay = open_delay
        self.timeout = timeout
        self._ser: serial.Serial | None = None

    def open(self) -> None:
        if self._ser and self._ser.is_open:
            return
        self._ser = serial.Serial(
            port=self.port,
            baudrate=self.baud,
            timeout=self.timeout,
        )
        # Quy định C: Uno reset khi mở Serial — đợi rồi mới gửi
        time.sleep(self.open_delay)
        self._ser.reset_input_buffer()

    def close(self) -> None:
        if self._ser and self._ser.is_open:
            self._ser.close()
        self._ser = None

    def __enter__(self) -> SerialBridge:
        self.open()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not payload.get("id"):
            payload = {**payload, "id": _new_id()}
        self.open()
        assert self._ser is not None
        line = json.dumps(payload, separators=(",", ":")) + "\n"
        self._ser.write(line.encode("utf-8"))
        self._ser.flush()

        raw = self._ser.readline()
        if not raw:
            raise TimeoutError(
                f"timeout {self.timeout}s chờ phản hồi Uno trên {self.port}"
            )
        text = raw.decode("utf-8", errors="replace").strip()
        if not text:
            raise TimeoutError("nhận dòng trống từ Uno")
        return json.loads(text)

    def get_env(self, cmd_id: str | None = None) -> dict[str, Any]:
        return self.request(
            {
                "v": 1,
                "id": cmd_id or _new_id(),
                "to": "uno",
                "cmd": "get_env",
            }
        )

    def set_relay(
        self, name: str, on: bool, cmd_id: str | None = None
    ) -> dict[str, Any]:
        if name not in ("light", "fan"):
            raise ValueError("relay name phải là light|fan")
        return self.request(
            {
                "v": 1,
                "id": cmd_id or _new_id(),
                "to": "uno",
                "cmd": "relay",
                "name": name,
                "on": on,
            }
        )

    def set_pump(
        self,
        on: bool,
        seconds: int = 2,
        cmd_id: str | None = None,
    ) -> dict[str, Any]:
        sec = max(1, min(5, int(seconds)))
        return self.request(
            {
                "v": 1,
                "id": cmd_id or _new_id(),
                "to": "uno",
                "cmd": "pump",
                "on": on,
                "seconds": sec,
            }
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke serial_bridge → Uno")
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    parser.add_argument(
        "--cmd",
        choices=("get_env", "relay", "pump"),
        default="get_env",
    )
    parser.add_argument("--name", choices=("light", "fan"), default="light")
    parser.add_argument("--on", action="store_true", default=False)
    parser.add_argument("--off", action="store_true", default=False)
    parser.add_argument("--seconds", type=int, default=2)
    parser.add_argument(
        "--test-cooldown",
        action="store_true",
        help="Một lần mở cổng: pump on rồi on ngay (kỳ vọng lần 2 = busy)",
    )
    args = parser.parse_args(argv)

    on = True if args.on else False
    if args.off:
        on = False

    print(f"port={args.port} baud={args.baud} cmd={args.cmd}", flush=True)
    try:
        with SerialBridge(port=args.port, baud=args.baud) as bridge:
            if args.test_cooldown:
                r1 = bridge.set_pump(True, 1)
                print("1:", json.dumps(r1, ensure_ascii=False), flush=True)
                r2 = bridge.set_pump(True, 1)
                print("2:", json.dumps(r2, ensure_ascii=False), flush=True)
                if r1.get("ok") and r2.get("error") == "busy":
                    print("cooldown OK", flush=True)
                    return 0
                print("cooldown FAIL (cần lần 1 ok + lần 2 busy)", file=sys.stderr)
                return 2

            if args.cmd == "get_env":
                resp = bridge.get_env()
            elif args.cmd == "relay":
                resp = bridge.set_relay(args.name, on)
            else:
                resp = bridge.set_pump(on, args.seconds)
    except serial.SerialException as e:
        print(f"Lỗi Serial: {e}", file=sys.stderr)
        print(
            "Gợi ý: đóng arduino-cli monitor / Serial Monitor rồi chạy lại.",
            file=sys.stderr,
        )
        return 1
    except (TimeoutError, json.JSONDecodeError, ValueError) as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        return 1

    print(json.dumps(resp, ensure_ascii=False))
    if not resp.get("ok"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
