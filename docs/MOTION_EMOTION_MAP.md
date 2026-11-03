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
| `happy` | `swing` + `tiptoeSwing` FOOT_H — đùi CT/CP + bàn BT/BP | Vui |
| `alert` | `swing` nhanh + `shakeLeg` LEFT | Cảnh báo |
| `forward` / `tien` / `step_forward` | `walk(3,1000,FORWARD)` rồi `home()` | 4 servo (đùi + bàn) |
| `backward` / `lui` / `step_back` | `walk(3,1000,BACKWARD)` rồi `home()` | 4 servo |
| `left` / `trai` / `turn_left` | `turn(3,1000,LEFT)` rồi `home()` | 4 servo |
| `right` / `phai` / `turn_right` | `turn(3,1000,RIGHT)` rồi `home()` | 4 servo |

CP trim trong firmware: `Otto.setTrims(0, 14, 0, 0)` (YR ≈ +14° / 1654 µs).  
Emotion `swing`/`bend`/`shakeLeg`/`jitter` cần OttoDIYLib local có amp đùi ≠ 0 (bản trong `refs/OttoDIYLib`).

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

`speak_and_act`: host gửi `emotion` → ESP32 `led`, `motion` → ESP32 `motion`.  
Nếu chỉ gửi `led`, sketch này vẫn chạy motion mặc định ở bảng trên.

## Test Serial

```bash
screen /dev/cu.usbserial-2120 115200
# rồi gõ:
forward
backward
left
right
happy
{"v":1,"id":"1","to":"esp32","cmd":"motion","name":"forward"}
{"v":1,"id":"2","to":"esp32","cmd":"led","state":"alert"}
```
