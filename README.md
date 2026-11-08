# Jarvis-on-Desk

Đồ án IoT — Otto + cảm biến bàn + LLM (DeepSeek / Ollama Qwen).

**Hợp đồng JSON:** [`docs/PROTOCOL.md`](docs/PROTOCOL.md)  
**Cảm biến / phạm vi:** [`docs/CONTEXT.md`](docs/CONTEXT.md)  
**Plan soft:** [`docs/plan-soft.md`](docs/plan-soft.md)  
**Việc còn lại trước demo:** [`last-task.md`](last-task.md)

Repo: https://github.com/thanhhale288/iot-jarvis

---

## Demo mai — bàn giao nhanh

### 0. Setup máy (một lần)

```bash
git clone https://github.com/thanhhale288/iot-jarvis.git
cd iot-jarvis
python3 -m venv .venv && source .venv/bin/activate
pip install -r voice/requirements.txt
cp .env.example .env
# Dán DEEPSEEK_API_KEY; chỉnh UNO_PORT / ESP32_PORT khi có board
```

| Env quan trọng | Gợi ý demo |
|----------------|------------|
| `LLM_PROVIDER` | `deepseek` (nhanh) hoặc `ollama` (offline) |
| `AI_BACKEND` | `serial` khi cắm board; thiếu cổng → tự mock |
| `OTTO_ACT` | `1` = điều khiển Otto; `0` = chỉ chữ/giọng |
| `TTS_MODE` | `chunk` = nói sớm; `full` = khớp chữ↔audio |
| `STT_MODEL` | `small` (VI đúng hơn); lần đầu load chậm |

### 1. Không cần board (rehearsal)

```bash
source .venv/bin/activate
python -m tests.smoke_mvp_soft          # DeepSeek + mock + TTS
AI_BACKEND=mock python -m frontend      # http://127.0.0.1:8787
```

Cảm biến mock trả JSON mẫu (`temp`/`hum`/`light`/`soil`). Otto `turn_left` / `turn_right` / `step_forward` ACK mock được.

### 2. Có board (demo thật)

1. Đóng Serial Monitor / Arduino IDE trên đúng cổng.  
2. Cắm Uno + ESP32 (chung GND nếu nguồn ngoài).  
3. `.env`: `AI_BACKEND=serial`, đúng `UNO_PORT` / `ESP32_PORT`.  
4. Chạy:

```bash
source .venv/bin/activate
python -m frontend
# hoặc CLI:
python -m voice.pipeline "Nhiệt độ hiện tại?"
python -m ai "Bật đèn"
```

### 3. Script 4 câu (chốt)

1. “Nhiệt độ và độ ẩm hiện tại?”  
2. “Bật đèn”  
3. “Otto vui lên” / “Quay trái”  
4. Một câu chat thường (ngoài IoT)

Checklist đầy đủ: [`last-task.md`](last-task.md).

### Quy định demo

| | |
|--|--|
| **A** | Laptop phát Hotspot; ESP32 join (không Wi‑Fi trường) nếu dùng HTTP |
| **B** | Servo/bơm 5V ngoài, **chung GND** |
| **C** | Serial Uno mở một lần; delay ~2s sau `open` |

| | Điền khi có |
|--|-------------|
| SSID hotspot | _chưa chốt_ |
| Password | _chưa chốt_ |
| IP ESP32 | _chưa chốt_ |
| `UNO_PORT` | vd. `/dev/cu.usbserial-2120` |
| `ESP32_PORT` | vd. `/dev/cu.usbserial-2110` |

---

## Thư mục

| Thư mục | Chủ | Việc |
|---------|-----|------|
| `esp32/` | P2 | Firmware Otto, TFT, Wi‑Fi — [`esp32/README.md`](esp32/README.md) |
| `voice/` | P2 | STT / TTS / pipeline |
| `frontend/` | P2 | Chat web chữ + giọng + Otto |
| `host/` | P3 | Router, `speak_and_act` — [`host/README.md`](host/README.md) |
| `uno/` | P3 | Firmware DHT, relay, bơm |
| `ai/` | P3 | LLM + tools — [`ai/README.md`](ai/README.md) |
| `serial_bridge/` | P3 | USB Serial → JSON (quy định C) |
| `docs/` | P1 | PROTOCOL, kế hoạch |
| `tests/` | P5 | Unit + smoke |

P1 không ôm lát dọc. Đổi schema JSON = họp P2 + P3.

## Clone

```bash
git clone https://github.com/thanhhale288/iot-jarvis.git
cd iot-jarvis
```
