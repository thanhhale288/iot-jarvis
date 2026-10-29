# AI — Ollama trường + tools môi trường / relay / bơm

Dùng server: `https://research.neu.edu.vn/ollama` · model `qwen3:8b`  
(xem `.env` / `.env.example`)

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

## Smoke chat (cần Ollama)

`AI_BACKEND=mock` vẫn được. Có board: `AI_BACKEND=serial`, đóng monitor Serial.

```bash
cd /Users/hale/Code/IOT
source .venv/bin/activate
python -m ai
python -m ai "Bật đèn và tưới 2 giây"
```
