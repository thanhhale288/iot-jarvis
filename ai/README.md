# AI — Ollama trường + tools môi trường / relay / bơm

Mặc định local: `http://127.0.0.1:11434` · `qwen2.5:7b` (Ollama Homebrew).  
Trường (khi sống): `https://research.neu.edu.vn/ollama` · `qwen3:8b` — xem `.env` / `.env.example`.

## Tools (tuần 2)

| Tool | Việc |
|------|------|
| `get_environment` | temp, hum, light, soil |
| `set_relay` | `name`: light\|fan, `on` |
| `set_pump` | `on`, `seconds` 1–5 |

## Backend (A3)

| `AI_BACKEND` | Việc |
|--------------|------|
| `mock` (mặc định) | Tools → `host` mock, **không** Serial |
| `serial` | Tools → `SerialBridge` + Uno thật |

```bash
# Chỉ tools mock (không cần Ollama / USB)
python -c "from ai.chat_env import MockBoardBackend, run_tool; print(run_tool('get_environment', {}, MockBoardBackend()))"
```

## Style (A4)

Mặc định: ngắn, tiếng Việt, đúng số/ACK từ tool.  
Chỉnh giọng: set `AI_SYSTEM_PROMPT` trong `.env` (không sửa code).

## Smoke chat (cần Ollama)

`AI_BACKEND=mock` vẫn được. Có board: `AI_BACKEND=serial`, đóng monitor Serial.

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
