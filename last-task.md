# Last tasks — demo mai (bàn giao)

Soft/MVP gần đủ. **Không cần feature lớn mới.** Làm theo thứ tự dưới trước giờ thuyết trình.

## Bắt buộc (trước demo)

1. **Warm-up 1 lần** trên máy demo:
   ```bash
   cd /path/to/iot-jarvis && source .venv/bin/activate
   python -m frontend
   ```
   Mở http://127.0.0.1:8787 → hỏi mic + “nhiệt độ” + “quay trái”  
   (Whisper `small` lần đầu chậm ~30–60s.)

2. **Cắm board** (Uno + ESP32 Otto), đóng Serial Monitor:
   - `.env`: `AI_BACKEND=serial`, đúng `UNO_PORT` / `ESP32_PORT`
   - Thử: `Bật đèn` → `Nhiệt độ` → `Otto vui lên`

3. **Mạng DeepSeek** sống (key trong `.env`, `LLM_PROVIDER=deepseek`).  
   Wi‑Fi trường chặn API → dùng hotspot điện thoại.

4. **Script 4 câu chốt sẵn** (đừng improv dài):
   1. Cảm biến: “Nhiệt độ và độ ẩm hiện tại?”
   2. Thiết bị: “Bật đèn”
   3. Otto: “Quay trái” / “Đi tới” / “Otto vui lên”
   4. Chat thường: một câu ngoài bàn học (chứng minh không chỉ IoT)

## Nên có (không bắt buộc sửa code)

| Việc | Ghi chú |
|------|---------|
| `TTS_MODE=chunk` trong `.env` | Nói sớm hơn (~giảm chờ full TTS) |
| Soft smoke trước khi cắm board | `python -m tests.smoke_mvp_soft` |
| Hotspot laptop + ESP32 Wi‑Fi | Chỉ nếu không demo Serial |
| Slide / checklist 5 bước | Xem `docs/PROTOCOL.md` §6 |

## Bỏ / để sau (không chặn demo)

- Wake “Hey Jarvis”
- IR, clap, tưới tự động đất khô
- Clone giọng VoiceStudio
- Gait Otto đầy đủ trên servo thật (mock/ACK `turn_*` / `step_forward` đã có)

## Khi không có board

Host **soft-fallback → mock** nếu thiếu cổng USB. Chat + TTS + tool JSON vẫn chạy:

```bash
AI_BACKEND=mock OTTO_ACT=0 python -m frontend
# hoặc
python -m ai "Nhiệt độ hiện tại?"
```

## Owner gợi ý

| Việc | Ai |
|------|----|
| Mic / TTS / frontend | P2 |
| Uno Serial / AI tools / DeepSeek | P3 |
| Smoke checklist / slide | P5 / P1 |
| Cắm dây / nguồn / GND | P4 / P6 |

Chi tiết chạy nhanh: [`README.md`](README.md) mục **Demo mai**.
