# ESP32 — pin map Otto (P2)

**Chốt:** theo sơ đồ nhóm; **không NeoPixel**; **buzzer không gắn ESP32** (cắm Uno — xem [`uno/README.md`](../uno/README.md)).

Smoke TFT: `esp32/tft_test/`. Firmware chính khi có → ghi thêm ở đây, không ghi pin vào PROTOCOL.

**Luật:** đang cắm/rút → rút USB ESP32. Servo / HC-SR04 ăn **5V ngoài**, **chung GND** với ESP32 (quy định B).

---

## Pin map

| Thiết bị | GPIO ESP32 | Cách nối |
|----------|------------|----------|
| **TFT ST7789** | D22, D21, D23, D18, D27 | CS→D22 · DC→D21 · SDA/MOSI→D23 · SCL/SCK→D18 · RST→D27 (không dùng D12) · VCC→3V3 · GND→GND · BL→3V3 (nếu có) |
| **HC-SR04** | D4, D5 | TRIG→LV→HV→**D4** · ECHO→HV→LV→**D5** · VCC→5V ngoài · GND chung · qua level shifter |
| **KY-037** (âm thanh) | D35 (ưu tiên) / D34 | **D0→D35** · `+`→3V3 · G→GND · A0 để trống nếu dùng D0 |
| **Servo SG90 ×4** | D16, D13, D26, D14 | PWM lần lượt D16 / D13 / D26 / D14 (**không** D15) · V+→5V ngoài · GND chung |
| **Level shifter** | — | LV→3V3 · HV→5V ngoài · GND chung · chỉ cho TRIG/ECHO |
| **Nguồn 5V ngoài ≥3A** | — | `(+)` → nhánh 5V (servo, HC-SR04, HV shifter) · `(−)` → GND chung ESP32 |
| **ESP32** | USB | Nuôi board bằng USB; không cần nối chân 5V board nếu đã USB |

### Không còn trên ESP32

| Cũ | Việc mới |
|----|----------|
| NeoPixel (mọi chân) | **Loại khỏi dự án** — trạng thái `cmd:led` → **TFT** (Grobot / mắt) |
| Buzzer D25 (+ BC547) | **Uno D6** — cắm ngoài hub Uno |

---

## Map JSON → phần cứng

| PROTOCOL | Phần cứng |
|----------|-----------|
| `cmd:led` / `emotion` | TFT ST7789 emotion |
| `cmd:motion` | 4× SG90 |
| `event` `clap` | KY-037 D35 |
| `event` `proximity` | HC-SR04 D4/D5 |

Beep khi clap/proximity: **không** trên ESP32 — Uno buzzer (local / host sau).

---

## Nguồn (nhắc)

- Servo + HC-SR04: **5V ngoài ≥3A**, không lấy từ chân 5V ESP32.
- Thiếu GND chung → giật servo / reset.
