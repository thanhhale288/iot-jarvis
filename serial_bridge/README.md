# serial_bridge — USB → Uno JSON (quy định C)

## Chạy smoke

**Đóng** `arduino-cli monitor` trước (chỉ 1 chương trình dùng cổng).

```bash
source .venv/bin/activate
python -m serial_bridge
python -m serial_bridge --cmd relay --name light --on
python -m serial_bridge --cmd pump --on --seconds 2
python -m serial_bridge --test-cooldown
```

Port mặc định: `.env` → `UNO_PORT` (vd. `/dev/cu.usbserial-2110`).
