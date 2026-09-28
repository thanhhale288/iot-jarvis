"""USB Serial bridge → Uno JSON (quy định C).

Mở cổng một lần rồi giữ. Tắt DTR/RTS để chống reset Uno khi open;
vẫn delay settle (PROTOCOL C / fallback nếu driver vẫn pulse).
Tuần 2+: luôn gửi id; set_relay / set_pump; CLI --text.
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
PREVENT_RESET = os.getenv("UNO_PREVENT_RESET", "1").strip() not in (
    "0",
    "false",
    "False",
    "no",
)


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


class SerialBridge:
    def __init__(
        self,
        port: str = DEFAULT_PORT,
        baud: int = DEFAULT_BAUD,
        open_delay: float = OPEN_DELAY_S,
        timeout: float = READ_TIMEOUT_S,
        prevent_reset: bool = PREVENT_RESET,
    ) -> None:
        self.port = port
        self.baud = baud
        self.open_delay = open_delay
        self.timeout = timeout
        self.prevent_reset = prevent_reset
        self._ser: serial.Serial | None = None

    def open(self) -> None:
        if self._ser and self._ser.is_open:
            return

        ser = serial.Serial()
        ser.port = self.port
        ser.baudrate = self.baud
        ser.timeout = self.timeout
        ser.bytesize = serial.EIGHTBITS
        ser.parity = serial.PARITY_NONE
        ser.stopbits = serial.STOPBITS_ONE

        if self.prevent_reset:
            # T07 / quy định C: không để DTR/RTS kéo RESET khi open
            ser.dsrdtr = False
            ser.rtscts = False
            ser.dtr = False
            ser.rts = False

        ser.open()

        if self.prevent_reset:
            try:
                ser.dtr = False
                ser.rts = False
            except (OSError, ValueError, serial.SerialException):
                pass

        # Settle + fallback nếu board/driver vẫn pulse DTR
        time.sleep(self.open_delay)
        ser.reset_input_buffer()
        self._ser = ser

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


def _parse_text_line(line: str) -> tuple[str, dict[str, Any]] | None:
    """Parse 'light on' / 'fan off' / 'env' / 'pump on 2' → (action, kwargs)."""
    parts = line.strip().lower().split()
    if not parts:
        return None
    if parts[0] in ("quit", "exit", "q"):
        return ("quit", {})
    if parts[0] in ("env", "get_env"):
        return ("get_env", {})
    if parts[0] in ("help", "?"):
        return ("help", {})
    if parts[0] in ("light", "fan"):
        if len(parts) < 2 or parts[1] not in ("on", "off"):
            raise ValueError("dùng: light on|off  hoặc  fan on|off")
        return ("relay", {"name": parts[0], "on": parts[1] == "on"})
    if parts[0] == "pump":
        if len(parts) < 2 or parts[1] not in ("on", "off"):
            raise ValueError("dùng: pump on [1-5]  hoặc  pump off")
        seconds = 2
        if parts[1] == "on" and len(parts) >= 3:
            seconds = int(parts[2])
        return ("pump", {"on": parts[1] == "on", "seconds": seconds})
    raise ValueError(f"lệnh lạ: {line!r} — gõ help")


def run_text_repl(bridge: SerialBridge) -> int:
    print(
        "Text → Uno (mở cổng 1 lần). Lệnh: light on|off, fan on|off, "
        "env, pump on [sec], quit",
        flush=True,
    )
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print(flush=True)
            return 0
        if not line:
            continue
        try:
            parsed = _parse_text_line(line)
        except ValueError as e:
            print(f"! {e}", file=sys.stderr, flush=True)
            continue
        if parsed is None:
            continue
        action, kwargs = parsed
        if action == "quit":
            return 0
        if action == "help":
            print(
                "light on|off | fan on|off | env | pump on [1-5] | pump off | quit",
                flush=True,
            )
            continue
        try:
            if action == "get_env":
                resp = bridge.get_env()
            elif action == "relay":
                resp = bridge.set_relay(kwargs["name"], kwargs["on"])
            else:
                resp = bridge.set_pump(kwargs["on"], kwargs.get("seconds", 2))
        except (TimeoutError, json.JSONDecodeError, serial.SerialException) as e:
            print(f"! {e}", file=sys.stderr, flush=True)
            continue
        print(json.dumps(resp, ensure_ascii=False), flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke serial_bridge → Uno")
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    parser.add_argument(
        "--allow-reset",
        action="store_true",
        help="Cho phép DTR reset Uno (tắt chống reset T07)",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="REPL text: light on|off, fan on|off, env, …",
    )
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

    prevent = PREVENT_RESET and not args.allow_reset
    print(
        f"port={args.port} baud={args.baud} prevent_reset={prevent}",
        flush=True,
    )
    try:
        with SerialBridge(
            port=args.port,
            baud=args.baud,
            prevent_reset=prevent,
        ) as bridge:
            if args.text:
                return run_text_repl(bridge)

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
