# Repo cần clone / tham khảo — Jarvis-on-Desk

> Mục tiêu: lấy **thư viện + wiring**, **không** fork nguyên một “full Jarvis” thay PROTOCOL.  
> Schema JSON vẫn theo [`PROTOCOL.md`](PROTOCOL.md).

Clone vào thư mục ngoài monorepo (vd. `~/Code/refs/`) hoặc submodule tùy nhóm. Trong `iot-jarvis` chỉ copy/adapt code cần dùng.

---

## Ai clone cái gì (tóm tắt)

| Vai | Bắt buộc | Tùy chọn (TFT / wake) | Không clone |
|-----|----------|------------------------|-------------|
| **P2** (`esp32/`, `voice/`) | OttoDIYLib · openWakeWord · Whisper | Grobot_Animations (nếu mua TFT) · OttoDIY_ESP32 (chỉ xem pin) | xiaozhi-esp32 · JarvisNano · Beee · Pipecat |
| **P3** (`uno/`, `ai/`, `serial_bridge/`) | 1 repo tưới Uno · Ollama + Qwen tools | — | Smart-home ESP thay Uno · framework voice nặng |
| **P1** | Đọc file này + PROTOCOL | — | Không ôm firmware |

---

## P2 — Robot + giọng nói

### 1. Otto motion / gesture (bắt buộc)

```bash
git clone https://github.com/OttoDIY/OttoDIYLib.git
```

- Dùng: `Oscillator`, `playGesture`, mouths (nếu có matrix).
- Map gesture → `cmd: motion` (`nod`, `shake`, `happy`, …).
- Plan dùng ~3 servo, **không** gait mặc định tuần 1–4 — bỏ / không phụ thuộc walk 4 chân nếu khung không đủ.

### 2. Otto trên ESP32 — chỉ tham khảo pin (tùy chọn)

```bash
git clone https://github.com/rhansenne/OttoDIY_ESP32.git
```

- Lấy: map chân servo / Wi‑Fi boot.
- **Không** lấy protocol Bluetooth/app; giữ `POST /cmd` (hoặc WebSocket) theo PROTOCOL.

### 3. TFT emotion (chỉ khi đã mua màn)

```bash
git clone https://github.com/tanmaywankar/Grobot_Animations.git
```

- ESP32 + `TFT_eSPI` (ST7789 / ILI9341 / ST7735).
- `setEmotion(...)` map với `led.state` / `emotion` trong PROTOCOL:

| PROTOCOL `state` / `emotion` | Grobot (gợi ý) |
|------------------------------|----------------|
| `idle` | `NEUTRAL` / `IDLE1` |
| `listening` | `QUESTIONING` |
| `thinking` | `IDLE2` |
| `speaking` | `EXCITED` |
| `happy` | `HAPPY` |
| `alert` | `ANGRY` hoặc `SAD` |

**Backup cùng kiểu mắt (chọn 1 nếu Grobot không khớp màn):**

```bash
git clone https://github.com/yousseftechdev/RoboEyesTFT.git
# hoặc OLED rẻ: https://github.com/FluxGarage/RoboEyes
# hoặc ST7735: https://github.com/Shourov-Paul/AnimatedroboEye
```

Màn nên mua: **ST7789 240×240 SPI ~1.3–1.54"** gắn **ESP32** (không gắn Uno). Logic 3.3V; servo vẫn nguồn ngoài + GND chung (quy định B).

### 4. Wake “Hey Jarvis” trên laptop (Tuần 5)

```bash
git clone https://github.com/dscripka/openWakeWord.git
# hoặc: pip install openwakeword  — model sẵn hey_jarvis
```

- Chạy trên **laptop**, không nhét wake nặng vào ESP32 tuần 5 nếu không cần.

### 5. STT / TTS trên laptop (Tuần 1+)

Không bắt buộc clone repo — cài Python:

| Việc | Gợi ý |
|------|--------|
| STT | `faster-whisper` hoặc `openai-whisper` |
| TTS | `edge-tts` (nhanh demo) hoặc `pyttsx3` / Piper |

---

## P3 — Môi trường + AI + bridge

### 1. Hub tưới / cảm biến Uno (bắt buộc — chọn 1)

```bash
git clone https://github.com/thecollectives6/Smart-Irrigation-System.git
# hoặc:
git clone https://github.com/phambaoquan25qc-hub/Smart-Plant-Watering.git
```

- Lấy: wiring DHT / đất / relay / bơm / LCD, hysteresis tưới.
- Viết lại thành JSON: `get_env`, `relay`, `pump` theo PROTOCOL.
- `serial_bridge`: mở Serial **một lần**, delay ~2s sau `open` (quy định C).

### 2. AI tools (không cần clone “Jarvis”)

- Cài [Ollama](https://ollama.com/) + model kiểu `qwen2.5`.
- Đăng ký tools map đúng lệnh Uno/ESP32: `get_env`, `relay`, `pump`, và (qua host) `motion` / `led` / `speak_and_act`.
- Fallback offline tuần 5–6 theo plan — không phụ thuộc cloud bắt buộc lúc demo Hotspot.

### 3. IR (Tuần 4)

- Library Arduino IDE: **IRremote** (examples decode) → event `ir` theo PROTOCOL mục 7.

---

## Lib Arduino / PlatformIO (không phải “repo product”)

Cài qua Library Manager khi code firmware:

| Lib | Ai | Việc |
|-----|----|------|
| `ArduinoJson` | P2, P3 | Parse/serialize 1 dòng JSON |
| `WebServer` / WiFi (ESP32 core) | P2 | `POST /cmd` |
| `TFT_eSPI` | P2 | Chỉ khi có TFT |
| `ESP32Servo` hoặc Servo tương thích | P2 | Servo Otto |
| `DHT sensor library` | P3 | DHT11 |
| `LiquidCrystal` / I2C LCD | P3 | LCD 16×2 |
| `IRremote` | P3 | Remote tuần 4 |

---

## Không clone / không fork làm nền project

| Repo | Lý do |
|------|--------|
| [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) | Full assistant trên board (ESP-IDF + cloud) — lệch laptop STT/TTS/Qwen |
| JarvisNano / Beee (Waveshare AMOLED/LCD kit) | Hardware đắt, protocol khác |
| Pipecat / Huxley / jarvis-py / anyrobo | Framework voice nặng; che mất glue PROTOCOL |
| Otto PLUS Bluetooth app firmware | Không khớp Hotspot + JSON host |

Clap: module **KY-037/038**, digital DO + debounce → `event: clap` — không cần repo riêng.

---

## Thứ tự gợi ý (khớp hạn plan)

1. **Tuần 1:** P2 OttoDIYLib + WebServer echo `led`/`ping` · P3 irrigation wiring + `get_env` + bridge delay 2s · STT 1 câu (Whisper).  
2. **Tuần 2–3:** servo + GND · TTS · `speak_and_act` · (tùy) Grobot nếu đã có TFT.  
3. **Tuần 5:** openWakeWord `hey_jarvis` · turn left/right.  

MVP **24/09** không phụ thuộc TFT hay wake.

---

## Checklist clone

- [ ] P2: `OttoDIYLib`
- [ ] P2: Whisper / faster-whisper (pip)
- [ ] P2: `openWakeWord` (trước Tuần 5)
- [ ] P2: `Grobot_Animations` (chỉ nếu mua ST7789)
- [ ] P3: Smart-Irrigation **hoặc** Smart-Plant-Watering
- [ ] P3: Ollama + Qwen
- [ ] P3: IRremote (Tuần 4)
- [ ] Cả nhóm: **không** lấy xiaozhi làm firmware chính
