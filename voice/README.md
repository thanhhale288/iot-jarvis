# Voice — STT / TTS / low-latency pipeline

**Không dùng live STT.** Đoạn đường tối ưu:  
`record (cắt im lặng) → Whisper nhanh → LLM stream câu → TTS overlap`.

## Chạy

```bash
cd /Users/hale/Code/IOT
source .venv/bin/activate
pip install -r voice/requirements.txt

# Cửa sổ hội thoại (chữ + giọng + Otto nếu OTTO_ACT=1)
python -m frontend
# → http://127.0.0.1:8787

# CLI: STT/text → LLM → speak_and_act (TFT+servo) + TTS
python -m voice.pipeline "Otto vui lên"
python -m voice.pipeline "Gật đầu" --no-tts

# UI đo độ trễ: mic → Jarvis + time-to-first-speech
python -m voice.ui
# → http://127.0.0.1:7860

# CLI pipeline (có text = bỏ STT)
python -m voice.pipeline "Bật đèn"
python -m voice.pipeline   # ghi mic đến khi im

# Chỉ STT / TTS
python -m voice
python -c "from voice.tts import speak; speak('Xin chào')"

# C3 — Wake “Hey Jarvis” rồi pipeline
python -m voice.wake
# WAKE_BACKEND=stt (mặc định, Whisper tiny) | openwakeword + WAKE_MODEL=…
# WAKE_ONCE=1 — một lần rồi thoát
```

## Tối ưu độ trễ

| Tầng | Cách |
|------|------|
| Record | Cắt khi im lặng (`STT_SILENCE_MS=600`) |
| STT | Mặc định `small` + `beam=5` (đúng VI); `base`/`1` nếu cần tốc độ |
| LLM | Ollama Qwen hoặc `LLM_PROVIDER=deepseek`; prompt viết **để đọc thành tiếng** |
| TTS | `TTS_MODE=full`: **text UI = audio** (một lần đọc); `chunk` = overlap |

Metric: **`time-to-first-speech`**. Kiểm tra khớp: `assistant` và `spoken` phải giống nhau.

## Env

| Key | Mặc định | Việc |
|-----|----------|------|
| `STT_MODEL` | `base` | `tiny` nhanh hơn / `small` chính xác hơn |
| `STT_BEAM` | `1` | Tăng = chậm + đúng hơn |
| `STT_LANGUAGE` | `vi` | |
| `STT_SILENCE_MS` | `600` | Im lặng bao lâu thì dừng ghi |
| `STT_MAX_SECONDS` | `8` | Trần một lượt ghi |
| `TTS_VOICE` | `vi-VN-HoaiMyNeural` | edge-tts |
| `TTS_RATE` | `+10%` | Hơi nhanh |
| `STT_UI_PORT` | `7860` | |
