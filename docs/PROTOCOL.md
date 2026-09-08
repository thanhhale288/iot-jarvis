# PROTOCOL — hợp đồng JSON Jarvis-on-Desk

**Trạng thái:** nháp P1 — P2 và P3 ký **10/09/2026**.  
Sau khi ký: không đổi schema một mình. PR phá JSON bị từ chối.

Tuần 1 chỉ bắt buộc các lệnh ở mục 3–4. Mục 7 là chỗ dành sẵn, chưa implement.

---

## 1. Quy tắc chung

- Một tin = **một object JSON**, UTF-8, **một dòng** (NDJSON). Cấm pretty-print trên Serial.
- Tối đa **256 byte / dòng** (buffer Arduino).
- Số: không dùng string cho `temp`, `on`, `seconds`.
- Không hiểu `cmd` → trả `ok: false`, không được im.

### Phong bì (mọi lệnh / mọi board)

Gửi:

```json
{"v":1,"id":"a1","to":"esp32","cmd":"led","state":"listening"}
```

Trả:

```json
{"v":1,"id":"a1","from":"esp32","ok":true}
```

Lỗi:

```json
{"v":1,"id":"a1","from":"uno","ok":false,"error":"unknown_cmd"}
```

| Field | Bắt buộc | Giá trị |
|-------|----------|---------|
| `v` | có | `1` |
| `id` | nên có | Chuỗi ngắn, host tự sinh; board **echo lại** đúng `id` |
| `to` | khi gửi | `esp32` \| `uno` \| `host` |
| `from` | khi trả | `esp32` \| `uno` \| `host` |
| `cmd` | khi gửi | Xem bảng dưới |
| `ok` | khi trả | `true` \| `false` |
| `error` | khi `ok` false | `unknown_cmd` \| `bad_args` \| `busy` \| `timeout` \| `sensor` |

`id` tuần 1 được phép bỏ (LED echo). Từ tuần 2: luôn có `id`.

---

## 2. Đường truyền

### ESP32 — Wi‑Fi (quy định A)

Laptop phát **Hotspot**. ESP32 join mạng đó. Không dùng Wi‑Fi trường (Captive Portal).

SSID / pass / IP: ghi trong [README](../README.md) khi P2 có số.

Tuần 1 chọn **một** (P2 chốt, ghi README):

- HTTP `POST /cmd` — body = một JSON, response = một JSON
- hoặc WebSocket — mỗi text frame = một JSON

### Uno — USB Serial (quy định C)

- Baud **115200**, 8N1.
- `serial_bridge` **mở cổng một lần rồi giữ**. Không open/close mỗi lệnh.
- Sau `open`: **timeout đọc + delay ~2 giây** rồi mới gửi JSON. Uno reset vì DTR khi mở Serial; bỏ bước này là mất dòng JSON.
- Host không gửi lệnh mới khi chưa nhận dòng trả (hoặc hết timeout).

### Nguồn servo (quy định B)

Servo **không** ăn 5V từ chân ESP32. Nguồn 5V ngoài ≥2A, **chung GND** với ESP32. Thiếu GND chung → giật / reset.

---

## 3. ESP32 — tuần 1 bắt buộc

Chủ: P2 (`esp32/`).

### `led`

```json
{"v":1,"id":"1","to":"esp32","cmd":"led","state":"listening"}
```

```json
{"v":1,"id":"1","from":"esp32","ok":true,"state":"listening"}
```

`state` chỉ được:

| state | Ý nghĩa |
|-------|---------|
| `idle` | Nghỉ |
| `listening` | Đang nghe |
| `thinking` | Đang nghĩ |
| `speaking` | Đang nói |
| `happy` | Vui |
| `alert` | Cảnh báo |

Tuần 1: nhận `led` → đổi màu/đèn. Chưa cần đúng màu cuối.

### `motion`

```json
{"v":1,"id":"2","to":"esp32","cmd":"motion","name":"nod"}
```

```json
{"v":1,"id":"2","from":"esp32","ok":true,"name":"nod"}
```

`name` chỉ được:

| name | Ý nghĩa | Tuần |
|------|---------|------|
| `idle` | Đứng yên | 1 (nháp) |
| `nod` | Gật / nghiêng thân | 1 (nháp) |
| `shake` | Lắc | 1 (nháp) |
| `think` | Suy nghĩ | 1 (nháp) |
| `happy` | Vui | 1 (nháp) |
| `alert` | Cảnh báo | 1 (nháp) |
| `turn_left` | Quay trái | 5 |
| `turn_right` | Quay phải | 5 |
| `step_forward` | Tới gần (không gait mặc định) | 5 |

Tuần 1: firmware **nhận và log/ACK** đủ enum. Servo thật có thể tuần 2. Lệnh lạ → `bad_args`.

### `ping` (hello Wi‑Fi)

```json
{"v":1,"id":"0","to":"esp32","cmd":"ping"}
```

```json
{"v":1,"id":"0","from":"esp32","ok":true}
```

---

## 4. Uno — tuần 1 bắt buộc

Chủ: P3 (`uno/` + `serial_bridge/`).

### `get_env`

```json
{"v":1,"id":"3","to":"uno","cmd":"get_env"}
```

```json
{"v":1,"id":"3","from":"uno","ok":true,"temp":28.4,"hum":61.0,"light":420,"soil":610}
```

| Field | Đơn vị | Ghi chú |
|-------|--------|---------|
| `temp` | °C | DHT11, 1 chữ số thập phân |
| `hum` | %RH | DHT11 |
| `light` | ADC 0–1023 | LDR; số lớn = sáng hơn (P3 ghi ngược lại nếu wiring khác) |
| `soil` | ADC 0–1023 | Cảm biến đất; **số lớn = khô hơn** trên module kit (P3 xác nhận tuần 2) |

Tuần 1: `temp` + `hum` phải ra thật. `light` / `soil` được trả `-1` nếu chưa gắn.

Sensor lỗi:

```json
{"v":1,"id":"3","from":"uno","ok":false,"error":"sensor"}
```

### `relay` — khóa tên tuần 1, bật thật tuần 2

```json
{"v":1,"id":"4","to":"uno","cmd":"relay","id":"light","on":true}
```

```json
{"v":1,"id":"4","from":"uno","ok":true,"id":"light","on":true}
```

`id` chỉ được: `light` | `fan`.

### `pump` — khóa tên tuần 1, bật thật tuần 2

```json
{"v":1,"id":"5","to":"uno","cmd":"pump","on":true,"seconds":2}
```

```json
{"v":1,"id":"5","from":"uno","ok":true,"on":true,"seconds":2}
```

- `seconds` nguyên, 1–5. Thiếu field → mặc định `2`.
- Hết giờ tự `on: false`. Không tưới vô hạn.

---

## 5. Host → hai board (glue)

Laptop (P1 skeleton / P3 bridge) đọc `to` rồi gửi đúng đường:

```
{"to":"esp32", ...}  →  Wi‑Fi ESP32
{"to":"uno",   ...}  →  Serial Uno
```

Không gửi JSON ESP32 qua Serial Uno.

---

## 6. Smoke 5 bước (P1 chạy thứ Sáu — mock được)

1. Nói → P2 STT ra chữ.
2. Gửi `motion` hoặc `led` → ESP32 ACK.
3. Câu môi trường → P3 / Qwen gọi `get_env`.
4. P3 trả chữ + (tuần 3) `emotion`.
5. P2 TTS; LED/motion theo state (mock được).

Thiếu tầng: mock JSON đúng schema, không bịa field mới.

---

## 7. Dành sẵn — chưa làm tuần 1

Không implement. Không xóa khỏi PROTOCOL. Không tự thêm field khác.

**P3 → host → P2 (tuần 3):**

```json
{"v":1,"id":"9","to":"host","cmd":"speak_and_act","text":"Đất khô, mình tưới 2 giây.","emotion":"alert","motion":"nod"}
```

`emotion` dùng cùng enum `led.state`. `motion` dùng enum `motion.name`. `text` tiếng Việt, TTS của P2.

**ESP32 → host (tuần 2+):**

```json
{"v":1,"from":"esp32","cmd":"event","name":"clap"}
```

`name`: `clap` | `proximity`.

**Uno IR (tuần 4):**

```json
{"v":1,"from":"uno","cmd":"event","name":"ir","code":"FFA25D"}
```

---

## 8. Chữ ký schema

| Vai | Người | Ngày | Ký (viết tên) |
|-----|-------|------|----------------|
| Soạn | P1 | 08/09 | |
| ESP32 / voice | P2 | 10/09 | |
| Uno / AI / bridge | P3 | 10/09 | |

Đổi enum, đổi tên field, đổi đơn vị `soil`/`light` = họp lại, bump không cần `v` nếu chỉ thêm lệnh mới ở mục 7. Phá field tuần 1 → `v: 2` và họp.
