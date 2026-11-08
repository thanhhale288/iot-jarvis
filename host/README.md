# Host — router + speak_and_act (A2 / A7 / B7)

| `to` | Đường |
|------|--------|
| `uno` | USB Serial (`UNO_PORT`) hoặc mock |
| `esp32` | USB Serial Otto (`ESP32_PORT`) / HTTP `ESP32_URL/cmd` / mock |
| `host` | `speak_and_act` → led + motion + TTS |

JSON `to:esp32` **không** bao giờ ghi vào Serial Uno.

## Chạy nhanh

```bash
# Offline
python -c "from host.router import make_mock_router; print(make_mock_router().dispatch({'v':1,'id':'1','to':'host','cmd':'speak_and_act','text':'Hi','emotion':'happy'}))"

# Board: UNO_PORT + ESP32_TRANSPORT=serial|http
python -m voice.pipeline "Otto vui lên đi" --no-tts
```

| Env | Việc |
|-----|------|
| `AI_BACKEND` | `mock` \| `serial` / `real` |
| `ESP32_TRANSPORT` | `serial` \| `http` \| `mock` \| `auto` |
| `ESP32_PORT` | USB otto_motion |
| `ESP32_URL` | Base URL khi `http` |
| `OTTO_ACT` | `1` = pipeline/chat điều khiển Otto |
