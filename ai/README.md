# AI — Ollama trường + tools môi trường / relay / bơm

Dùng server: `https://research.neu.edu.vn/ollama` · model `qwen3:8b`  
(xem `.env` / `.env.example`)

## Tools (tuần 2)

| Tool | Việc |
|------|------|
| `get_environment` | temp, hum, light, soil |
| `set_relay` | `name`: light\|fan, `on` |
| `set_pump` | `on`, `seconds` 1–5 |

## Smoke

Đóng monitor Serial. Cắm Uno đã nạp sketch tuần 2.

```bash
cd /Users/hale/Code/IOT
source .venv/bin/activate
python -m ai
python -m ai "Bật đèn và tưới 2 giây"
```
