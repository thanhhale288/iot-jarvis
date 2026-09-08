# Jarvis-on-Desk

Đồ án IoT — Otto + cảm biến bàn + Qwen.

**Hợp đồng JSON (đọc trước khi code):** [`docs/PROTOCOL.md`](docs/PROTOCOL.md)

Repo: https://github.com/thanhhale288/iot-jarvis

## Clone

```bash
git clone https://github.com/thanhhale288/iot-jarvis.git
cd iot-jarvis
```

## Thư mục

| Thư mục | Chủ | Việc |
|---------|-----|------|
| `esp32/` | P2 | Firmware Otto, LED, Wi‑Fi |
| `voice/` | P2 | STT / TTS / wake |
| `uno/` | P3 | Firmware DHT, relay, bơm |
| `ai/` | P3 | Qwen, tools |
| `serial_bridge/` | P3 | USB Serial → JSON (quy định C) |
| `docs/` | P1 | PROTOCOL, kế hoạch |
| `tests/` | P5 | Checklist, smoke |

P1 không ôm lát dọc. Đổi schema JSON = họp P2 + P3, không sửa một mình.

## Mạng demo (quy định A)

Laptop **phát Hotspot**. ESP32 join mạng đó — không dùng Wi‑Fi trường.

| | Điền khi có |
|--|-------------|
| SSID | _chưa chốt_ |
| Password | _chưa chốt_ |
| IP ESP32 | _chưa chốt_ |
| Cổng Serial Uno | _vd. `/dev/cu.usbmodem*` hoặc `COM3`_ |

## Tuần 1

P2: Wi‑Fi echo LED + STT 1 câu.  
P3: DHT11 ra JSON sau khi rút/cắm USB.  
P1: PROTOCOL đã ghi; 10/09 họp P2/P3 ký schema.
