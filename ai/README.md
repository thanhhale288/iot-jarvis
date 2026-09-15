# AI — Ollama trường + tool get_environment

Dùng server: `https://research.neu.edu.vn/ollama` · model `qwen3:8b`  
(xem `.env` / `.env.example`)

## Smoke

Đóng monitor Serial. Cắm Uno + DHT.

```bash
cd /Users/hale/Code/IOT
source .venv/bin/activate
python -m ai
# hoặc:
python -m ai "Nhiệt độ bàn bao nhiêu?"
```

Log kỳ vọng: `[tool] get_environment` → JSON temp/hum → câu trả lời tiếng Việt có số thật.
