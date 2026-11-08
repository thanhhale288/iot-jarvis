# ESP32 — pin map Otto (P2)

**Chốt:** theo sơ đồ nhóm; **không NeoPixel**; **buzzer không gắn ESP32** (cắm Uno — xem [`uno/README.md`](../uno/README.md)).  
**Không gắn** KY-037 / HC-SR04 (đã ngoài plan — xem [`CONTEXT.md`](../docs/CONTEXT.md)).

Smoke TFT: `esp32/tft_test/`. Firmware chính: `esp32/otto_motion/`.

**Luật:** đang cắm/rút → rút USB ESP32. Servo ăn **5V ngoài ≥3A**, **chung GND** với ESP32 (quy định B).

---

## Pin map

| Thiết bị | GPIO ESP32 | Cách nối |
|----------|------------|----------|
| **TFT ST7789** | D22, D21, D23, D18, D27 | CS→D22 · DC→D21 · SDA/MOSI→D23 · SCL/SCK→D18 · RST→D27 (không dùng D12) · VCC→3V3 · GND→GND · BL→3V3 (nếu có) |
| **Servo SG90 ×4** | D16, D13, D26, D14 | PWM lần lượt D16 / D13 / D26 / D14 (**không** D15) · V+→5V ngoài · GND chung |
| **Nguồn 5V ngoài ≥3A** | — | `(+)` → nhánh 5V servo · `(−)` → GND chung ESP32 |
| **ESP32** | USB | Nuôi board bằng USB |

### Không còn trên ESP32

| Cũ | Việc mới |
|----|----------|
| NeoPixel (mọi chân) | **Loại khỏi dự án** — trạng thái `cmd:led` → **TFT** |
| Buzzer D25 (+ BC547) | **Uno D6** |
| KY-037 / HC-SR04 | **Ngoài plan** — không nối, không `event` clap/proximity |

---

## Map JSON → phần cứng

| PROTOCOL | Phần cứng |
|----------|-----------|
| `cmd:led` / `emotion` | TFT ST7789 emotion |
| `cmd:motion` | 4× SG90 |
| `cmd:ping` | Wi‑Fi hello |

---

## Wi‑Fi `POST /cmd` (B1)

Sketch `otto_motion/` (Serial **và** HTTP):

1. Copy `esp32/otto_motion/wifi_config.example.h` → `wifi_config.h`, điền SSID/pass Hotspot laptop.
2. Nạp board, Serial 115200: dòng `WiFi OK http://x.x.x.x/cmd`.
3. Host: `ESP32_TRANSPORT=http` · `ESP32_URL=http://x.x.x.x`.

```bash
curl -sS -X POST http://x.x.x.x/cmd -H 'Content-Type: application/json' \
  -d '{"v":1,"id":"1","to":"esp32","cmd":"ping"}'
```

## Nguồn (nhắc)

- Servo: **5V ngoài ≥3A**, không lấy từ chân 5V ESP32.
- Thiếu GND chung → giật servo / reset.

---

## Firmware chính + Wi‑Fi (plan-soft B1)

Sketch: `esp32/otto_motion/`

1. Copy `wifi_config.h.example` → `wifi_config.h`, điền `WIFI_SSID` / `WIFI_PASS` (hotspot laptop).
2. Nạp:

```bash
arduino-cli compile --fqbn esp32:esp32:esp32 esp32/otto_motion
arduino-cli upload -p /dev/cu.usbserial-2120 --fqbn esp32:esp32:esp32:UploadSpeed=115200 esp32/otto_motion
```

3. Serial in `WiFi OK IP=x.x.x.x` → `.env`: `ESP32_URL=http://x.x.x.x` · `AI_BACKEND=real` · `ESP32_TRANSPORT=http`
4. Smoke: `curl -s -X POST "$ESP32_URL/cmd" -H 'Content-Type: application/json' -d '{"v":1,"id":"0","to":"esp32","cmd":"ping"}'`
5. **C5:** mất Wi‑Fi → firmware tự `WiFi.begin` lại mỗi ~8s (Serial: `WiFi reconnect…` / `WiFi reconnected IP=…`)
6. **C4 motions:** `turn_left` / `turn_right` / `step_forward` qua `cmd:motion`
