# Jarvis-on-Desk

Đồ án IoT — Otto + cảm biến bàn + Qwen.

**Hợp đồng JSON (đọc trước khi code):** [`docs/PROTOCOL.md`](docs/PROTOCOL.md)  
**Mỗi cảm biến làm gì (đừng lệch plan):** [`docs/CONTEXT.md`](docs/CONTEXT.md)  
**Repo tham khảo (P2/P3 clone gì):** [`docs/NEED_REPOS.md`](docs/NEED_REPOS.md)

Repo: https://github.com/thanhhale288/iot-jarvis

## Clone

```bash
git clone https://github.com/thanhhale288/iot-jarvis.git
cd iot-jarvis
```

## Thư mục

| Thư mục | Chủ | Việc |
|---------|-----|------|
| `esp32/` | P2 | Firmware Otto, TFT, Wi‑Fi — pin: [`esp32/README.md`](esp32/README.md) |
| `voice/` | P2 | STT / TTS / wake |
| `uno/` | P3 | Firmware DHT, relay, bơm |
| `ai/` | P3 | Qwen, tools |
| `serial_bridge/` | P3 | USB Serial → JSON (quy định C) |
| `docs/` | P1 | PROTOCOL, kế hoạch |
| `tests/` | P5 | Checklist, smoke |

P1 không ôm lát dọc. Đổi schema JSON = họp P2 + P3, không sửa một mình.

## Mạng demo (quy định A)

Laptop **phát Hotspot**. ESP32 join mạng đó — không dùng Wi‑Fi trường.

| | Giá trị |
|--|---------|
| SSID | `halekeke` (pass trong `wifi_config.h` local) |
| Password | _local only — không commit_ |
| IP ESP32 | `192.168.15.165` (Serial 2026-11-03) → `.env` `ESP32_URL=http://192.168.15.165` |
| Cổng Serial Uno | `/dev/cu.usbserial-2110` (`.env` `UNO_PORT`) |
| Cổng Serial ESP32 | `/dev/cu.usbserial-2120` (nạp firmware) |

**Board thật (plan-soft B):** `AI_BACKEND=real` · `ESP32_TRANSPORT=http` · `ESP32_URL=http://192.168.15.165` (đổi IP nếu Serial in khác).

## Tuần 1

P2: Wi‑Fi echo `led`→TFT + STT 1 câu.  
P3: DHT11 ra JSON sau khi rút/cắm USB.  
P1: PROTOCOL đã ghi; 10/09 họp P2/P3 ký schema.
