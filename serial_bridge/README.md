# serial_bridge — USB → Uno JSON (quy định C)

## Chạy smoke

**Đóng** `arduino-cli monitor` trước (chỉ 1 chương trình dùng cổng).

```bash
cd /Users/hale/Code/IOT
source .venv/bin/activate
cp -n .env.example .env   # nếu chưa có .env

python -m serial_bridge
# hoặc:
python -m serial_bridge --port /dev/cu.usbserial-2110
```

Kỳ vọng in 1 dòng JSON có `temp` / `hum`.

Test rút USB: rút → cắm lại → chạy lại lệnh trên.
