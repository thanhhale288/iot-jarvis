# serial_bridge — USB → Uno JSON (quy định C)

Mở cổng **một lần**. Mặc định **tắt DTR/RTS** (chống reset Uno khi open), rồi delay settle (~2s).

## Chạy smoke

**Đóng** `arduino-cli monitor` trước (chỉ 1 chương trình dùng cổng).

```bash
source .venv/bin/activate
python -m serial_bridge
python -m serial_bridge --cmd relay --name light --on
python -m serial_bridge --cmd relay --name light --off
python -m serial_bridge --cmd pump --on --seconds 2
python -m serial_bridge --test-cooldown
```

## Text (T07 DoD)

```bash
python -m serial_bridge --text
# > light on
# > fan off
# > env
# > quit
```

Port: `.env` → `UNO_PORT`. Tắt chống reset (debug): `--allow-reset` hoặc `UNO_PREVENT_RESET=0`.
