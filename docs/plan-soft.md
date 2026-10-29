# Plan phần mềm (plan-soft)

**Khi nào dùng:** hardware cảm biến / servo / TFT đã smoke xong, hoặc ngồi code **không cắm board**.  
**Hợp đồng:** [`PROTOCOL.md`](PROTOCOL.md) · ngữ cảnh linh kiện: [`CONTEXT.md`](CONTEXT.md) · map Otto: [`MOTION_EMOTION_MAP.md`](MOTION_EMOTION_MAP.md).

Không thêm field JSON mới. Thiếu tầng → **mock đúng schema**.

---

## A. Làm được khi không cắm IoT

| # | Việc | Folder | DoD (xong khi) |
|---|------|--------|----------------|
| A1 | Mock board Uno + ESP32 trả NDJSON mẫu | host / `tests/` hoặc module mock | `get_env`, ACK `led`/`motion`, lỗi `unknown_cmd` đúng phong bì |
| A2 | Host router đọc `to` | host (skeleton) | `to:uno` ≠ `to:esp32`; không gửi JSON ESP32 qua Serial |
| A3 | AI tools gọi mock | `ai/` | `get_environment` / `set_relay` / `set_pump` không cần Serial |
| A4 | Prompt Qwen → tool → JSON Uno | `ai/` | Câu môi trường / đèn / tưới ra đúng lệnh PROTOCOL |
| A5 | STT 1 câu (mic laptop) | `voice/` | Text tiếng Việt ra stdout/log |
| A6 | TTS từ `text` (loa laptop) | `voice/` | Phát được câu mẫu |
| A7 | Ghép `speak_and_act` phía host | host / `voice/` | Tách `emotion`→`led`, `motion`→`motion`, `text`→TTS |
| A8 | Unit test enum + cooldown bơm | `tests/` | Enum khớp PROTOCOL; `pump` 1–5s; cooldown 5s → `busy` |
| A9 | Checklist smoke 5 bước (mục 6 PROTOCOL) | `tests/` | Chạy được với mock, tick pass/fail |

**Thứ tự A:** A1 → A2 → A3 → A4 → A5+A6 → A7 → A8 → A9.

---

## B. Khi đã có board — nối mock → thật

| # | Việc | Folder | DoD |
|---|------|--------|-----|
| B1 | ESP32 firmware PROTOCOL qua Wi‑Fi | `esp32/` | `ping` / `led` / `motion` ACK; Hotspot laptop; ghi SSID/IP README |
| B2 | Uno firmware tuần 2 đủ | `uno/` | `get_env` thật; `relay` light\|fan; `pump` + cooldown |
| B3 | `serial_bridge` giữ cổng, chống reset | `serial_bridge/` | DTR/RTS false; delay ~2s; không mất dòng JSON đầu |
| B4 | Host: mock → bridge + Wi‑Fi thật | host | Cùng API A2, đổi transport |
| B5 | AI tools → bridge thật | `ai/` | `python -m ai "…"` điều khiển Uno thật |
| B6 | Event ESP32 | `esp32/` | `clap` (KY-037), `proximity` (HC-SR04); host nhận rồi quyết định |
| B7 | E2E giọng → Otto | `voice/` + host + `esp32/` | STT → Qwen → TTS + `led`/`motion` trên robot |
| B8 | Luật đất khô → tưới | host / `ai/` | Đọc `soil` → `pump` có hạn, không tưới vô hạn |

**Thứ tự B:** B1+B2 → B3 → B4 → B5 → B6 → B7 → B8.

---

## C. Sau MVP (chỉ khi A+B ổn)

| # | Việc | Ghi chú |
|---|------|---------|
| C1 | IR → `event` `ir` + `code` | Uno, tuần 4 |
| C2 | Uno vòng ~60s nhắc ngưỡng | Local / host |
| C3 | Wake “Hey Jarvis” | `voice/` |
| C4 | `turn_left` / `turn_right` / `step_forward` | ESP32 motion tuần 5 |
| C5 | Wi‑Fi tự nối lại; Uno tưới khi rút laptop | P0 trước diễn tập |

---

## Đã có sẵn (không làm lại từ đầu)

| Path | Dùng cho |
|------|----------|
| `esp32/otto_motion/` | `led`+`motion` → TFT + servo (thường còn Serial; B1 gắn Wi‑Fi) |
| `serial_bridge/` | B3 / B5 |
| `ai/` | A3–A4, B5 |
| `uno/get_env/` | Nền B2 |
| `docs/MOTION_EMOTION_MAP.md` | A7 / B7 |

---

## Ngoài phạm vi plan-soft

- Linh kiện **Ngoài plan** trong CONTEXT (NeoPixel, mưa, keypad, …).
- Đổi schema PROTOCOL một mình.
- Gait Otto đầy đủ / app Bluetooth Otto làm nền.

---

## Trạng thái nhanh

| Bucket | Trạng thái |
|--------|------------|
| A (offline) | A1 ✅ A2 ✅ — tiếp A3 |
| B (có board) | phụ thuộc A1–A2 + hardware đã smoke |
| C (sau MVP) | khóa đến khi B7–B8 ổn |

**Next:** làm **A3** — AI tools gọi mock (`get_environment` / `set_relay` / `set_pump`).
