# Map emotion / motion → TFT + Otto servo

**Sketch:** `esp32/otto_motion/` — **đã liên kết**: mỗi lệnh đổi mặt TFT rồi chạy servo.  
**Đơn vị amp:** độ servo. BP/BT dùng `FOOT_H=30` (khớp lỏng).

## `cmd:motion` → servo

| `name` | Hành động Otto | Ghi chú |
|--------|----------------|---------|
| `idle` | `home()` | Đứng yên |
| `nod` | `bend(1,1200,LEFT)` | Gật / nghiêng |
| `shake` | `shakeLeg(1,1200,RIGHT)` | Lắc chân |
| `think` | `jitter(3,600,20)` | Suy nghĩ (hông) |
| `happy` | `swing` + `tiptoeSwing` FOOT_H | Vui |
| `alert` | `swing` nhanh + `shakeLeg` LEFT | Cảnh báo |
| `turn_left` | `turn(…,LEFT)` | Tuần 5 |
| `turn_right` | `turn(…,RIGHT)` | Tuần 5 |
| `step_forward` | `walk(2,…,FORWARD)` | Tuần 5 |

Không dùng `playGesture` (cần LED matrix Otto).

## `emotion` / `cmd:led` → default motion

Cùng enum `led.state`. TFT `tft_eyes` label ↔ emotion:

| emotion | TFT face (gần) | motion mặc định |
|---------|----------------|-----------------|
| `idle` | IDLE | `idle` |
| `listening` | LISTEN | `idle` |
| `thinking` | THINK | `think` |
| `speaking` | SPEAK | `nod` |
| `happy` | HAPPY | `happy` |
| `alert` | ALERT | `alert` |

`speak_and_act`: host gửi `emotion` → ESP32 `led` (**chỉ TFT**), `motion` → ESP32 `motion` (TFT theo key + servo).  
Host luôn gửi kèm `motion` (mặc định theo bảng trên nếu LLM không chọn). Plain text `happy` trên Serial vẫn = `act()` (mặt + servo).

## Test Serial

```bash
screen /dev/cu.usbserial-2110 115200
# rồi gõ:
happy
{"v":1,"id":"1","to":"esp32","cmd":"motion","name":"nod"}
{"v":1,"id":"2","to":"esp32","cmd":"led","state":"alert"}
```
