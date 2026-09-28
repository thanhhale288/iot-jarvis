# CONTEXT — mỗi linh kiện làm gì

Đọc file này **trước** khi code một cảm biến hoặc actuator.  
Hợp đồng JSON: [`PROTOCOL.md`](PROTOCOL.md). Danh sách kit: [`linh_kien.json`](linh_kien.json). Task: `IOT J.A.R.V.I.S - Trang tính1.csv` (T01–T37).

Kit có đồ **không nằm trong plan**. Có trong JSON ≠ được làm.

## Cách làm khi được giao 1 linh kiện

1. Tìm đúng dòng trong bảng dưới (đúng tên kit).
2. Chỉ sửa **folder** và **board** của dòng đó.
3. Chỉ dùng **lệnh JSON** đã ghi. Thiếu lệnh trong PROTOCOL → dừng, không tự thêm field.
4. Dòng **Ngoài plan** → báo lại, không code, không nối dây “cho đủ kit”.

Không đổi schema một mình. Không đưa JSON của ESP32 qua Serial Uno. Không lấy firmware xiaozhi / app Otto Bluetooth làm nền.

## Mốc (để khỏi làm sớm)

| Mốc | Task | Được làm |
|-----|------|----------|
| 14/09 | T01–T06 | `ping`, `led`, `motion` ACK, `get_env` (`temp`+`hum` thật) |
| 19/09 | T07–T12 | Bridge giữ cổng + chống reset; LDR, đất, LCD, `relay`, `pump`; vỗ tay + siêu âm + TTS |
| 24/09 | T13–T18 | MVP nói → Qwen → loa → Otto; `speak_and_act`; đất khô thì tưới |
| 29/09 | T19–T24 | Remote IR; Uno nhắc khi vượt ngưỡng (vòng ~60s) |
| sau 29/09, trước 10/10 | T25–T30 | Đóng băng kịch bản; Hey Jarvis; `turn_left` / `turn_right` / `step_forward`. Bỏ gait nếu chưa ổn |
| 10/10 | T31–T36 | Chỉ sửa lỗi P0; Wi‑Fi tự nối lại; Uno vẫn tưới khi rút cáp laptop |
| 15/10 | T37 | Diễn tập, không thêm tính năng |

`light` / `soil` chưa gắn → trả `-1`, không bịa số.

## Trong plan

| Linh kiện | STT | Ai / folder | Task | Việc đúng | JSON |
|-----------|-----|-------------|------|-----------|------|
| DHT11 | 6 | P3 `uno/` | T03 | Nhiệt °C, ẩm %RH. OUT → **D2** | `get_env`: `temp`, `hum` |
| MS-CDS05 | 8 | P3 `uno/` | T09 | Ánh sáng ADC 0–1023. AO → **A0**. **Số thấp = sáng hơn** | `get_env`: `light` |
| Độ ẩm đất TH | 12 | P3 `uno/` | T09, T15 | ADC 0–1023. AO → **A1**. **Số lớn = khô hơn**. Khô → tưới có hạn | `get_env`: `soil` rồi `pump` |
| LCD1602 + I2C | 2, 3 | P3 `uno/` | T09 | Hiện T/H và L/S tại chỗ. SDA→**A4**, SCL→**A5** | Không có lệnh riêng |
| Relay 1 kênh | 11 | P3 `uno/` | T09 | Đèn. IN → **D7** | `relay` `id:"light"` |
| LED + trở (giả quạt) | 34–36, 32 | P3 `uno/` | T09 | Quạt tuần 2 = LED, (+) qua trở → **D8** | `relay` `id:"fan"` |
| L298 + bơm MB370 | 10, 23 | P3 `uno/` | T09, T15, T33 | IN1 → **D9**. `seconds` 1–5, mặc định 2. Hết giờ tự tắt. Cooldown 5s → `busy`. Nguồn bơm riêng, chung GND | `pump` |
| Arduino Uno R3 | 1 | P3 `uno/` + `serial_bridge/` | T03, T07 | Serial **115200**. Bridge mở **một lần**, DTR/RTS false, delay ~2s. Không reset mỗi lệnh | Mọi lệnh `to:"uno"` |
| NeoPixel 12 LED | 18 | P2 `esp32/` | T02, T14 | 5 trạng thái: idle, listening, thinking, speaking, happy, alert | `led` `state` |
| Cảm biến âm thanh | 5 | P2 `esp32/` | T08 | Vỗ tay, digital + debounce | `event` `name:"clap"` |
| Siêu âm SRF04 | 14 | P2 `esp32/` | T08 | Mắt khoảng cách gần. Chi tiết ở mục dưới | `event` `name:"proximity"` |
| Buzzer 5V | 26 | P2 `esp32/` | T08 | Kêu local khi `clap` hoặc `proximity`. Không phải lệnh host | Không thêm `cmd` |
| Servo SG90 | 24 | P2 `esp32/` | T14, T16, T26 | Otto: nod, shake, think, happy, alert; tuần 5 thêm turn_left, turn_right, step_forward. Kit 1 con; plan mua thêm (T04) cho ~3 servo. **5V ngoài ≥2A, chung GND**. Không đi bộ | `motion` `name` |
| Thu IR 1838 + remote | 20, 21 | P3 `uno/` | T21, T19 | Điều khiển khi tắt mic. Tuần 4 | `event` `name:"ir"` `code` |
| Breadboard, dây, trở, LED rời | 31–41 | P4 / người đang cắm | T10 | Chỉ để nối các dòng **trong plan** | — |

Pin Uno chi tiết: [`uno/README.md`](../uno/README.md). Pin ESP32 (siêu âm, mic, NeoPixel, servo) **chưa chốt trong repo** — ghi vào `esp32/README.md` khi cắm, không ghi vào PROTOCOL.

`speak_and_act` (tuần 3, P3 → host → P2): `text` tiếng Việt, `emotion` = enum `led.state`, `motion` = enum `motion.name`. Host đọc `to` rồi gửi đúng đường.

## Ngoài plan — không làm

Có trong kit, **không** có task. Không thêm field JSON, không gắn “cho đủ”.

| Linh kiện | STT | Vì sao để yên |
|-----------|-----|----------------|
| DS1307 + AT24C32 | 4 | Plan không có đồng hồ / log thời gian |
| Rung SW-420 | 7 | Không có event rung |
| Cảm biến mưa | 9 | Tưới theo **đất**, không theo mưa |
| NE555 | 13 | Không tạo xung riêng |
| 74HC595 | 15 | Không có tác vụ shift-register |
| LED 7 đoạn (4 số và 1 số) | 16, 17 | Hiển thị = LCD, trạng thái = NeoPixel |
| LED matrix 8×8 | 19 | Plan không giao miệng ma trận |
| Động cơ bước 28BYJ-48 | 22 | Otto dùng servo; không gait |
| Pin 9V + jack | 25, 37 | Servo/bơm dùng nguồn 5V ngoài (T04), không nuôi servo từ pin 9V trên ESP32 |
| Keypad 4×4 | 27 | Điều khiển = giọng nói + remote IR |
| Nút nhấn + vỏ | 28, 29 | Không có nút trên bàn trong task |
| Chiết áp B10K | 30 | Ngưỡng để trong code, không chỉnh bằng biến trở |

## Ví dụ: “làm cảm biến siêu âm”

Làm **đúng** thế này:

- Folder `esp32/` (P2), task **T08**, cùng tuần với vỗ tay + TTS (mốc 19/09).
- SRF04 là **mắt**: vật ở gần → gửi một dòng

```json
{"v":1,"from":"esp32","cmd":"event","name":"proximity"}
```

- Host nhận `proximity` rồi mới quyết định (tuần 3 có thể `speak_and_act` / `led` alert). Firmware mắt **không** tưới, không gọi Qwen.
- Buzzer chỉ kêu local, cùng task T08.

Làm **sai** (dừng, dù user chỉ nói “làm siêu âm”):

- Gắn SRF04 lên Uno hoặc nhét `distance` vào `get_env`.
- Thêm `cmd:"ultrasonic"` hoặc field `cm` — PROTOCOL chưa có.
- Dùng khoảng cách để bật bơm / relay.
- Làm mắt trước khi `ping` + `led` trên ESP32 chạy.
- Đổi PROTOCOL một mình.

Âm thanh đi cùng mắt, không phải cảm biến thứ hai tùy ý: vỗ tay → `event` `name:"clap"`, cũng từ ESP32, cũng T08.
