# Frontend — cửa sổ chat Jarvis

Transcript kiểu Gemini: bubble bên phải là bạn, chữ bên trái là Jarvis. Cùng lúc loa đọc đúng câu trên màn hình.

LLM vẫn **một lượt một câu** (không nhớ hội thoại cũ). Trang này chỉ để theo dõi. Lịch sử nằm trong trình duyệt (`localStorage`).

Gradio đo độ trễ vẫn ở `python -m voice.ui` (cổng 7860).

## Chạy

```bash
cd /Users/hale/Code/IOT
source .venv/bin/activate
python -m frontend
# → http://127.0.0.1:8787
```

Cần Ollama hoặc DeepSeek như `ai/` (gõ câu). Mic dùng Whisper trên máy chạy server; im ~0,6s thì dừng ghi.

| Env | Mặc định |
|-----|----------|
| `FRONTEND_HOST` | `127.0.0.1` |
| `FRONTEND_PORT` | `8787` |

## API

| | |
|--|--|
| `POST /api/chat` | `{"text":"..."}` → user + assistant, rồi TTS |
| `POST /api/listen` | Ghi mic máy chủ → cùng pipeline |
| `POST /api/replay` | `{"text":"..."}` đọc lại, không gọi LLM |
| `GET /api/health` | provider, model, voice |
