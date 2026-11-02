# Handoff — Otto 4 servo (ESP32)

**Ngày:** 2026-10-24  
**Branch:** `test-servo`  
**Mục đích:** chat sau đọc file này là đủ nối việc (pin, nguồn, trim, OttoDIYLib, lệnh nạp).

---

## Pin map (đã chốt khi test)

| Khớp | Tên | GPIO ESP32 | OttoDIYLib |
|------|-----|------------|------------|
| Chân phải (thân→đùi) | **CP** | **D13** | YR (RightLeg) |
| Chân trái | **CT** | **D14** | YL (LeftLeg) |
| Bàn chân phải | **BP** | **D16** | RR (RightFoot) |
| Bàn chân trái | **BT** | **D26** | RL (LeftFoot) |

**Không dùng D15** cho servo.

> Lúc debug từng cái, CP từng test tạm trên D16 — **map chính thức vẫn CP=D13, BP=D16**. Đừng để hai vàng chung một chân.

---

## Nguồn / dây (bắt buộc)

```
Adapter 5V (jack → Uno chỉ để chia nguồn)
  Uno 5V  → ray +  → đỏ ×4 servo
  Uno GND → ray −  → nâu ×4 servo
  ESP32 GND → cùng ray −   ← thiếu cái này = im / loạn

ESP32 USB → laptop (nuôi board)
Vàng servo → GPIO ở bảng trên (PWM 3.3V, không cần level shifter)
```

- Servo **không** lấy 5V từ chân ESP32.  
- Im + không quay: thường thiếu đỏ/nâu hoặc GND chung (PWM vẫn chạy — xem Serial).  
- Có tiếng không quay (khi còn giữ nhiều servo): dễ kẹt khung / chống lực; test **1 PWM, 3 detach**.

---

## Trim

- Horn đã gắn lại về ~1500 µs (cách 1) cho bàn chân; CP/CT cũng chỉnh horn.  
- **CP** vừa trim tinh lại trên D13 (sketch `esp32/servo_smoke/`).  
  - Serial 115200, cổng `/dev/cu.usbserial-2110`  
  - `+`/`-` = ±2 µs, `=`/`_` = ±10 µs, `s` = lưu NVS key `cp`  
- User báo CP **đã ổn** (2026-10-24) — **xác nhận đã bấm `s`** nếu mở chat mới; đọc lại:

```bash
screen /dev/cu.usbserial-2110 115200
# gõ p → in CP us
```

- NVS namespace: `servo`, key `cp` (Preferences).  
- Các chân khác home mặc định **1500 µs** nếu chưa trim riêng.

---

## OttoDIYLib (đã clone + smoke)

| Path | Việc |
|------|------|
| `refs/OttoDIYLib/` | Library (symlink → `~/Documents/Arduino/libraries/OttoDIYLib`) |
| `refs/OttoDIY_ESP32/` | Tham khảo pin (không lấy Bluetooth protocol) |
| `esp32/otto_smoke/otto_smoke.ino` | Smoke **gait sync**: walk ↔ turn ↔ swing/updown/tiptoe (FOOT_H=30°) |
| `esp32/otto_motion/otto_motion.ino` | **PROTOCOL** `motion`/`led` → **TFT face + servo** (đã liên kết) |

Init trong smoke:

```cpp
Otto.init(14, 13, 26, 16, false, 15);
// YL, YR, RL, RR — BuzzerPin 15 dummy (buzzer thật = Uno D6)
```

**Biên độ BP/BT (độ servo, Oscillator):** khớp lỏng → tăng ×2 so với mặc định Otto.

| Chỗ | Cũ | Mới |
|-----|----|-----|
| `walk` / `turn` `A[RL,RR]` | 20° | **40°** (`refs/OttoDIYLib/src/Otto.cpp`) |
| smoke `swing` / `updown` / `tiptoeSwing` `h` | 15° | **30°** (`FOOT_H` trong `otto_smoke.ino`) |

**Patch local:**
- `SerialCommand.h` — `SERIALCOMMAND_HARDWAREONLY` (ESP32 không có SoftwareSerial)
- `Otto.cpp` — foot amp walk/turn 20→40 (Jarvis)

Nếu Otto đứng bàn / đế cố định: comment `walk`/`turn` trong smoke, chỉ giữ swing. Chi tiết clone: [`docs/NEED_REPOS.md`](NEED_REPOS.md).

---

## Sketch / lệnh hữu ích

| Sketch | Vai trò |
|--------|---------|
| `esp32/servo_smoke/` | Trim / smoke 1–4 servo (ESP32Servo) |
| `esp32/otto_smoke/` | OttoDIYLib gait sync (walk/turn/swing FOOT_H=30) |
| `esp32/otto_motion/` | Map emotion/motion → servo (đứng chờ lệnh) |
| `esp32/esp_idle/` | Dừng PWM |
| `/tmp/esp_idle` (nạp khi cần) | Tắt PWM |

```bash
# Cổng ESP32 (thường):
# /dev/cu.usbserial-2110  = ESP32
# /dev/cu.usbserial-2130  = Uno (hay gặp)

arduino-cli compile --fqbn esp32:esp32:esp32 esp32/otto_smoke
arduino-cli upload -p /dev/cu.usbserial-2110 --fqbn esp32:esp32:esp32 \
  --upload-property upload.speed=115200 esp32/otto_smoke
```

Nếu upload báo port busy: tắt `screen` / Serial Monitor đang giữ cổng.

---

## Việc tiếp theo (gợi ý)

1. Nạp `otto_motion` — test `happy` / JSON `cmd:motion` (map: [`MOTION_EMOTION_MAP.md`](MOTION_EMOTION_MAP.md)).  
2. Gộp TFT + motion 1 firmware (hoặc host gửi `led`+`motion` song song).  
3. Nếu BP/BT yếu: `FOOT_H` 30→40; `A[RL,RR]` 40→50.  
4. NVS trim → `Otto.setTrims(...)`.  
5. Không commit secrets; `refs/` ignore hoặc submodule tùy nhóm.

---

## Tài liệu liên quan

- [`esp32/README.md`](../esp32/README.md) — pin map đầy đủ (TFT, SR04, servo)  
- [`docs/CONTEXT.md`](CONTEXT.md) — sensor / task map  
- [`docs/NEED_REPOS.md`](NEED_REPOS.md) — OttoDIYLib + clone list  
- [`docs/PROTOCOL.md`](PROTOCOL.md) — `cmd:motion`
