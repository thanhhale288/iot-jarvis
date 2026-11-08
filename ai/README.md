# AI — LLM + tools môi trường / relay / bơm

Mặc định local: `LLM_PROVIDER=ollama` · `http://127.0.0.1:11434` · `qwen2.5:7b`.  
Cloud nhanh hơn: `LLM_PROVIDER=deepseek` + `DEEPSEEK_API_KEY` (model `deepseek-chat`).  
Trường (khi sống): `https://research.neu.edu.vn/ollama` · `qwen3:8b` — xem `.env` / `.env.example`.

## LLM provider

| `LLM_PROVIDER` | Việc |
|----------------|------|
| `ollama` (mặc định) | Local / offline; A4 + A6b stream qua Ollama |
| `deepseek` | API DeepSeek (OpenAI-compatible); cần `DEEPSEEK_API_KEY` |

```bash
# Bật DeepSeek (sau khi dán key vào .env)
# LLM_PROVIDER=deepseek
# DEEPSEEK_API_KEY=sk-...
python -m ai "Nhiệt độ và độ ẩm hiện tại?"
```

## Tools (tuần 2)

| Tool | Việc |
|------|------|
| `get_environment` | temp, hum, light, soil |
| `set_relay` | `name`: light\|fan, `on` |
| `set_pump` | `on`, `seconds` 1–5 |
| `otto_act` | `emotion` / `motion` (enum PROTOCOL) → ESP32 |

## Backend (A3)

| `AI_BACKEND` | Việc |
|--------------|------|
| `mock` (mặc định) | Tools → `host` mock, **không** Serial |
| `serial` | Tools → `SerialBridge` + Uno thật |
| `real` | Tools → Uno Serial + ESP32 `ESP32_URL` (B4/B5) |

```bash
# Chỉ tools mock (không cần Ollama / USB)
python -c "from ai.chat_env import MockBoardBackend, run_tool; print(run_tool('get_environment', {}, MockBoardBackend()))"
```

## Style (A4)

Mặc định: hội thoại đa chủ đề (như DeepSeek); tool chỉ khi cảm biến/đèn/quạt/bơm.  
Điều khiển bàn: ngắn + đúng số/ACK. Chỉnh giọng: `AI_SYSTEM_PROMPT` trong `.env`.

## Smoke chat (cần Ollama hoặc DeepSeek)

`AI_BACKEND=mock` vẫn được. Có board: `AI_BACKEND=serial`, đóng monitor Serial.  
Lệnh cứng tắt mặc định; `AI_FAST_PATH=1` thì không gọi LLM.

```bash
cd /Users/hale/Code/IOT
source .venv/bin/activate
# Môi trường → get_environment
python -m ai "Nhiệt độ và độ ẩm hiện tại?"
# Đèn → set_relay
python -m ai "Bật đèn"
# Tưới → set_pump
python -m ai "Tưới 2 giây"
# Ghép
python -m ai "Bật đèn và tưới 2 giây"
```
