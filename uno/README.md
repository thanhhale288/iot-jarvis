# Uno — hướng dẫn cắm breadboard (P3 tuần 2)

File này = **thứ tự cắm + cách dùng breadboard**.  
Firmware: `uno/get_env/` · baud **115200**.

**Luật an toàn:** đang cắm/rút dây → **rút USB** Uno. Cắm xong một bước mới cắm USB để test.

---

## 1. Breadboard là gì (nhìn hình trong đầu)

Breadboard kiểu kit (GL No.12) thường thế này:

```text
  +  −                         −  +     ← ray nguồn (dọc 2 mép)
  ●  ●  ● ● ● ● ●  …  ● ● ●   ●  ●
  ●  ●  ● ● ● ● ●  …  ● ● ●   ●  ●
        ↑↑↑↑↑↑↑
        mỗi cụm 5 lỗ ngang = 1 hàng nối với nhau
        giữa board có rãnh → 2 nửa KHÔNG nối xuyên
```


| Vùng                     | Nối điện thế nào                                              |
| ------------------------ | ------------------------------------------------------------- |
| Ray `+` (đỏ)             | Tất cả lỗ trên cùng một ray `+` = chung nhau                  |
| Ray `−` (xanh/đen)       | Tất cả lỗ trên cùng một ray `−` = chung nhau                  |
| Hàng giữa (a–e hoặc f–j) | **5 lỗ ngang cùng số hàng** nối với nhau; hàng khác số = tách |
| 2 nửa trái/phải          | **Không** thông qua rãnh giữa — phải bắc jumper nếu cần       |


**Cách tiết kiệm dây (bắt buộc với ~10 jumper):**

1. Uno `5V` → **một** lỗ trên ray `+`
2. Uno `GND` → **một** lỗ trên ray `−`
3. Mỗi module: `VCC` cắm vào ray `+`, `GND` vào ray `−` (không chạy thêm dây về Uno)
4. Chỉ dây **tín hiệu** (OUT / AO / IN) chạy từ module → chân Uno (D2, A0, …)

---



## 2. Pin map (nhắc nhanh)


| Module              | STT   | Tín hiệu → Uno            |
| ------------------- | ----- | ------------------------- |
| DHT11               | 6     | OUT → **D2**              |
| MS-CDS05 (ánh sáng) | 8     | AO → **A0** (bỏ DO); **số thấp = sáng hơn** |
| Đất TH              | 12    | AO → **A1**               |
| **LCD1602 + I2C**   | 2+3   | **SDA→A4**, **SCL→A5**    |
| Relay               | 11    | IN → **D7**               |
| LED fan tạm         | —     | (+) qua trở → **D8**      |
| L298 → bơm          | 10+23 | IN1 → **D9** (xem Bước 6) |


Cổng Serial mẫu: `/dev/cu.usbserial-2110` (đổi `.env` → `UNO_PORT` nếu khác).

---



## 3. Thứ tự làm (đừng nhảy bước)


| #   | Việc                | Dây thêm (ước)          | Check                           |
| --- | ------------------- | ----------------------- | ------------------------------- |
| 0   | Chuẩn bị + hiểu ray | 0                       | Có Uno, board, jumper           |
| 1   | Ray nguồn + DHT11   | 2 nguồn + 1 tín hiệu    | `temp`/`hum` ra số              |
| 2   | Ánh sáng            | +1 tín hiệu             | `light` ≠ -1                    |
| 3   | Đất                 | +1 tín hiệu             | `soil` đổi khi ẩm/khô           |
| 3b  | **LCD I2C**         | +2 tín hiệu (SDA/SCL)   | Màn hiện T/H và L/S             |
| 4   | Relay light         | +1 tín hiệu             | `--cmd relay --name light --on` |
| 5   | LED fan D8          | +2 (LED+trở)            | `--cmd relay --name fan --on`   |
| 6   | L298 + bơm          | dây riêng + nguồn ngoài | `--cmd pump --on --seconds 2`   |


Mỗi bước: **rút USB → cắm → cắm USB → chạy lệnh check → tick → bước sau.**

---



## 4. Chi tiết từng bước (breadboard)



### Bước 0 — Chuẩn bị (~2 phút)

Lấy ra:

- KIT Arduino Uno + cáp USB
- Breadboard
- ~10 jumper đực–đực (hoặc đực–cái nếu module có chân cắm)
- Module **STT 6 DHT11** (bước 1)

Đặt board nằm ngang trước mặt. Chọn **một mép** làm “nguồn”: ray đỏ = `+`, ray xanh = `−`.  
**Chưa** cắm USB.

Xong khi: đồ nằm trên bàn, README mở.

---



### Bước 1 — Ray nguồn + DHT11 (~5 phút)



#### 1a. Nguồn từ Uno xuống breadboard (2 dây)


| Từ               | Đến                            |
| ---------------- | ------------------------------ |
| Uno chân **5V**  | **một lỗ bất kỳ** trên ray `+` |
| Uno chân **GND** | **một lỗ bất kỳ** trên ray `−` |


Chạm tay thử: 2 dây này không được chạm nhau.

#### 1b. Cắm DHT11 lên board (gợi ý hàng 1–5)

Cắm 3 chân module vào **3 hàng khác nhau** cùng một nửa board (vd. hàng 1, 2, 3 — cột a/b/c).

Giả sử chân DHT lần lượt: `VCC` | `OUT` | `GND` (nhìn chữ in trên module — **đừng đoán nếu khác**).


| Chân DHT               | Nối bằng jumper tới                     |
| ---------------------- | --------------------------------------- |
| **VCC** / `+`          | ray `+` (cùng mép đã nối 5V)            |
| **GND** / `−`          | ray `−`                                 |
| **OUT** / `DATA` / `S` | Uno chân **D2** (số **2** hàng digital) |


Sơ đồ chữ:

```text
Uno 5V  --------→  ray +  ←--------  DHT VCC
Uno GND --------→  ray −  ←--------  DHT GND
Uno D2  <---------------------------  DHT OUT
```



#### 1c. Check Bước 1

1. Cắm USB Uno
2. Nạp `uno/get_env/get_env.ino` (nếu chưa nạp tuần 2)
3. Đóng Serial Monitor
4. Chạy:

```bash
cd /Users/hale/Code/IOT
source .venv/bin/activate
python -m serial_bridge
```

**Đạt:** JSON `ok: true` và `temp` / `hum` là số (vd. 28.4).  
`light`/`soil` có thể còn `-1` nếu chưa cắm — bình thường ở Bước 1.

**Lỗi thường:** `sensor` → đảo VCC/GND hoặc OUT sai chân; timeout → sai cổng `.env` hoặc Monitor còn mở.

Xong Bước 1 → rút USB → sang Bước 2.

---



### Bước 2 — Ánh sáng MS-CDS05 (STT 8)

Cắm module sang hàng trống (vd. hàng 10–12), **cùng nửa** hoặc nửa kia cũng được.


| Chân module | →             |
| ----------- | ------------- |
| VCC         | ray `+`       |
| GND         | ray `−`       |
| **AO**      | Uno **A0**    |
| DO          | **không nối** |


Check: `python -m serial_bridge` → `light` từ 0–1023 (che tay: số đổi).

---



### Bước 3 — Đất TH (STT 12)


| Chân   | →          |
| ------ | ---------- |
| VCC    | ray `+`    |
| GND    | ray `−`    |
| **AO** | Uno **A1** |


Check: `soil` 0–1023. Ghi lại số khi khô / khi nhúng ẩm → xác nhận “lớn = khô hơn”.

---



### Bước 3b — LCD 1602 + module I2C (STT 2 + 3)

**Tác dụng:** hiện nhiệt/ẩm + light/soil trên màn (T09), không cần laptop nhìn Serial.

#### Ghép STT 2 ↔ STT 3 (trước khi nối Uno)

| STT | Là gì |
|-----|--------|
| **2** | Màn LCD1602 — hàng **16 chân** dọc mép trên |
| **3** | Module I2C — board nhỏ, thường có **ổ 16 lỗ** + 4 chân GND/VCC/SDA/SCL |

1. Úp **STT 3** vào mặt sau **STT 2**  
2. 16 lỗ của I2C **khớp** 16 chân LCD (cùng chiều; chân 1 thường phía có chữ VSS/GND trên LCD)  
3. Ấn sát; nếu lỏng thì **hàn** 16 chân (kit hay để hàn)  
4. Sau khi gắn: **chỉ dùng 4 chân** trên I2C ra breadboard — **không** nối 16 chân LCD thẳng ra Uno  

```text
        [ LCD 1602  STT 2 ]
         ||||||||||||||||   16 chân
        [ I2C backpack STT 3 ]
              |  |  |  |
            GND VCC SDA SCL  → Uno
```

#### 4 dây I2C → Uno
#### Check

1. Rút USB → cắm 4 dây → cắm USB  
2. Nạp `uno/get_env` (đã có trong sketch tuần 2)  
3. Sau ~2s: dòng 1 `Txx.xC Hxx.x%` · dòng 2 `Lxxx Sxxx`  
4. (Tuỳ) `python -m serial_bridge` — số Serial khớp LCD  

---


**Nếu màn sáng, I2C `0x27`, xoay núm vẫn trắng:** diagnostic `hd44780` *LCD Display Memory Test* = FAILED → lỗi **cơ khí STT2↔STT3** (chưa hàn/lệch chân), không phải code. Tháo gắn lại 16 chân, hàn chắc, không lệch 1 pin.

### Bước 4 — Relay (STT 11) = `light`

#### Relay làm gì?

Uno chân digital chỉ chịu **tín hiệu yếu** (khoảng 5V, vài mA).  
Đèn / quạt / thiết bị thật cần **dòng lớn hơn** (hoặc nguồn riêng).

**Relay = công tắc điện điều khiển bằng tín hiệu:**

- Uno ra lệnh `on` → chân **IN** HIGH → trong module có “công tắc” **đóng**
- Uno `off` → IN LOW → công tắc **mở**

Jarvis gọi: `relay` + `name=light` → firmware kéo **D7** → module relay này.

Hai phía trên module — **không trộn dây**:

```text
  [PHÍA ĐIỀU KHIỂN — nối Uno]     [PHÍA TẢI — nối đèn/quạt]
   VCC  GND  IN                      COM   NO   NC
      ↑ tín hiệu yếu                    ↑ công tắc công suất
```

| Phía | Chân | Việc |
|------|------|------|
| **Điều khiển** | VCC, GND, **IN** | Nuôi module + Uno bảo “bật/tắt” |
| **Tải** | **COM**, **NO**, (NC) | Chỗ mắc đèn/quạt + nguồn của đèn — **tách** khỏi chân D7 |

Chữ trên module:

| Chữ | Nghĩa |
|-----|--------|
| **COM** | Common — chân chung của công tắc |
| **NO** | Normally Open — mặc định **hở**; khi IN bật thì **nối** với COM |
| **NC** | Normally Closed — mặc định **nối**; khi IN bật thì **ngắt** (demo thường **không dùng**) |

**Phía tải trong README** = chỗ COM/NO: bạn mắc **vòng mạch đèn** đi qua công tắc đó, không phải cắm đèn vào D7.

#### Demo LED + trở 220Ω (làm từng mối)

**Lấy:** LED 5mm · trở **220Ω** (đỏ-đỏ-nâu-vàng hoặc STT 32) · 2–3 jumper.

**Nhận chân LED:** chân **dài** = (+), chân **ngắn** = (−).  
Nếu bằng nhau: nhìn trong bóng — miếng kim loại **lớn hơn** bên trong = (−).

Cắm trên breadboard (gợi ý hàng trống, vd. 20–25) — **mỗi chân một hàng**:

| # | Làm gì |
|---|--------|
| 1 | LED: chân dài → hàng **20**, chân ngắn → hàng **21** |
| 2 | Trở 220Ω: một đầu vào **cùng hàng 20** với chân dài LED; đầu kia → hàng **22** |
| 3 | Jumper: hàng **22** → ray **`+`** (5V) |
| 4 | Jumper: hàng **21** (chân ngắn LED) → chân **COM** trên relay (phía vít/3 chân tải, không phải VCC/GND/IN) |
| 5 | Jumper: chân **NO** trên relay → ray **`−`** (GND) |

```text
ray + ──jumper── hàng22 ──[220Ω]── hàng20 ── LED(+) 
                                              LED(−) hàng21 ──jumper── COM
                                                                    NO ──jumper── ray −
```

Khi `relay --on`: COM nối NO → mạch kín → LED sáng.  
Khi `--off`: COM–NO hở → LED tắt.


#### Cắm phía điều khiển (3 dây)

| Chân module | → |
|-------------|---|
| VCC | ray **`+`** |
| GND | ray **`−`** |
| **IN** | Uno **D7** |

Xong khi: VCC/GND/IN đúng; phía tải có LED demo **hoặc** tạm để trống (vẫn nghe click khi on/off).

Check:

```bash
python -m serial_bridge --cmd relay --name light --on
python -m serial_bridge --cmd relay --name light --off
```

Kỳ vọng: tiếng **click** trong relay; LED phía tải sáng/tắt nếu đã mắc COM/NO.

---



### Bước 5 — Fan tạm = LED trên D8

#### Việc này là gì?

Kit chỉ có **1 relay** (đã dùng cho `light` / D7).  
Lệnh `relay` + `name=fan` trong firmware kéo chân **D8** — tuần 2 dùng **LED** giả làm quạt.

| Lệnh | Chân Uno | Phần cứng tuần 2 |
|------|----------|------------------|
| `name=light` | D7 | Module relay (click) |
| `name=fan` | D8 | LED + trở (sáng/tắt) |

**Không** đi qua COM/NO của relay. Cắm thẳng breadboard ↔ D8.

#### Lấy đồ

- LED 5mm (khác cái dành cho relay nếu còn)
- Trở **220Ω** (STT 32)
- 2 jumper

LED: chân **dài** = (+), chân **ngắn** = (−).

#### Cắm từng mối (gợi ý hàng 30–32)

| # | Làm gì |
|---|--------|
| 1 | LED chân dài → hàng **30** |
| 2 | LED chân ngắn → hàng **31** |
| 3 | Trở: một đầu **cùng hàng 30**; đầu kia → hàng **32** |
| 4 | Jumper: hàng **32** → Uno chân **D8** (số **8** hàng digital) |
| 5 | Jumper: hàng **31** (chân ngắn) → ray **`−`** (GND) |

```text
Uno D8 ──jumper── hàng32 ──[220Ω]── hàng30 ── LED(+)
                                                   LED(−) hàng31 ──jumper── ray −
```

**Cấm:** LED không có trở (dễ cháy).  
**Cấm:** nhầm D8 với D7 (D7 = relay light).

#### Check (~30 giây)

Cắm USB · đóng Serial Monitor:

```bash
cd /Users/hale/Code/IOT
source .venv/bin/activate
python -m serial_bridge --cmd relay --name fan --on
```

→ LED sáng · JSON `ok: true`, `"name":"fan"`

```bash
python -m serial_bridge --cmd relay --name fan --off
```

→ LED tắt

**Lỗi thường**

| Hiện tượng | Nguyên nhân |
|------------|-------------|
| Không sáng | Đảo chân LED (+/−) |
| Không sáng | Nhầm D7 thay vì D8 |
| Rất tối / cháy | Thiếu trở hoặc trở sai |
| `bad_args` | Gõ sai `--name fan` |

---



### Bước 6 — Bơm MB370 + L298 (làm sau cùng)

#### Có nguy hiểm không?

| Mức | Việc | Thực tế |
|-----|------|---------|
| **Không** phải điện nhà 220V | Bơm MB370 chỉ **3.7–6V DC** | Không giật như ổ tường |
| **Có** rủi ro cháy board / hỏng bơm | Cắm sai nguồn | Uno reset, nóng, cháy cầu chì USB |
| **Có** rủi ro cơ | Bơm + nước | Không để nước dây vào Uno/laptop |

**Nguy hiểm thật sự ở bước này = nguồn nuôi motor sai chỗ**, không phải “điện cao thế”.

#### Cấm tuyệt đối

1. **Không** lấy nguồn bơm từ chân **5V** hoặc ray `+` của Uno (quy định B) — bơm kéo dòng mạnh → Uno reset / hỏng cổng USB Mac  
2. **Không** nối dây bơm thẳng vào **D9** — D9 chỉ là tín hiệu vào L298  
3. **Không** quên **chung GND**: GND L298 ↔ GND Uno (ray `−`)  
4. **Không** dùng **9V** nuôi MB370 lâu — bơm chỉ chịu tới ~6V; kit có pin 9V thì **ưu tiên adapter/powerbank 5V**  
5. **Không** để nước bắn lên board khi test

#### L298 làm gì?

Uno ra lệnh yếu (D9) → L298 = “van công suất” → cấp dòng từ **nguồn motor riêng** ra bơm.

```text
  [Uno D9] ──IN1──→ [ L298 ] ──OUT──→ [Bơm MB370]
  [Uno GND]─GND──→ [      ] ←── nguồn motor 5V NGOÀI (không từ Uno 5V)
```

#### Chuẩn bị trước khi cắm

- Module **L298 V3** (STT 10), bơm **MB370** (STT 23)
- Nguồn **5V DC ngoài** (cục sạc/powerbank + dây) — **chưa** cắm điện nguồn này
- USB Uno: **rút** khi đang nối dây
- Ống nước / khăn — test khô không nước cũng được (nghe motor quay)

Nhìn chữ in trên L298 (tên chân có thể hơi khác bản in):

| Nhóm | Chữ thường gặp | Việc |
|------|----------------|------|
| Logic | IN1, IN2, ENA, 5V, GND | Nối Uno |
| Motor out | OUT1, OUT2 (hoặc MOTOR A) | Nối bơm |
| Nguồn motor | +12V / VS / VCC motor (chữ to) | **5V ngoài** (+) |
| GND nguồn | GND (chung) | Chung với Uno |

Một số L298 có jumper **5V-EN**: để jumper nếu dùng logic 5V từ Uno.

#### Thứ tự cắm (làm đúng số — đừng đảo)

**A. Tín hiệu & mass (chưa có nguồn motor)**

| # | Từ | Đến |
|---|-----|-----|
| 1 | L298 **GND** | ray **`−`** (cùng GND Uno) |
| 2 | L298 **IN1** | Uno **D9** |
| 3 | L298 **IN2** | ray **`−`** (cố định chiều quay) |
| 4 | **ENA** (nếu có) | Jumper enable / nối 5V logic theo in module — xem mặt module |

**B. Bơm vào OUT (vẫn chưa cấp nguồn motor)**

| # | Từ | Đến |
|---|-----|-----|
| 5 | Dây bơm (2 dây) | L298 **OUT1** và **OUT2** |

Chiều đỏ/đen đảo → bơm quay ngược hoặc yếu: đảo 2 dây OUT nếu không hút.

**C. Nguồn motor — làm cuối, kiểm tra kỹ**

| # | Từ | Đến |
|---|-----|-----|
| 6 | Nguồn 5V ngoài **(+)** | Chân **nguồn motor** L298 (VS / +12V — dù ghi 12V vẫn có thể cấp 5V) |
| 7 | Nguồn 5V ngoài **(−)** | L298 **GND** (đã chung ray `−`) |

**Checklist trước khi cắm jack nguồn motor:**

- [ ] Bơm không đụng D9  
- [ ] GND L298 đã vào ray `−`  
- [ ] Nguồn motor **không** lấy từ Uno 5V  
- [ ] Nguồn là **~5V**, không phải 220V, tránh 9V nếu có 5V  

Rồi mới cắm USB Uno + bật nguồn motor.

#### Check phần mềm

```bash
cd /Users/hale/Code/IOT
source .venv/bin/activate
python -m serial_bridge --cmd pump --on --seconds 2
```

**Đạt:** bơm chạy ~2 giây rồi **tự tắt** · JSON `ok: true`.

```bash
python -m serial_bridge --cmd pump --off
```

→ tắt ngay nếu đang chạy.

#### Nếu sợ / chưa có nguồn 5V ngoài

**Bỏ qua Bước 6 tuần này cũng được.**  
Cảm biến + relay click + LED fan đã đủ demo lát P3.  
Bơm làm khi có adapter 5V và đã đọc hết mục Cấm.

#### Lỗi thường

| Hiện tượng | Nguyên nhân |
|------------|-------------|
| Uno reset khi bơm | Đang nuôi motor từ USB/Uno 5V |
| Bơm không quay | Thiếu nguồn motor / ENA chưa enable / sai OUT |
| Nóng L298 nhiều | Bình thường nhẹ; rất nóng → tắt nguồn, xem ngắn mạch |
| `ok` nhưng im | Nguồn motor chưa cắm |

---



## 5. Smoke đầy đủ (sau Bước 3 trở lên)

```bash
cd /Users/hale/Code/IOT
source .venv/bin/activate
python -m serial_bridge
python -m ai "Nhiệt độ và độ ẩm bàn bao nhiêu?"
```

---



## 6. JSON ngắn

- `"id"` = mã lệnh (bắt buộc)  
- Relay: `"cmd":"relay","name":"light"|"fan","on":true|false`  
- Bơm: `"cmd":"pump","on":true,"seconds":1..5` — hết giờ tự tắt; **5s cooldown** sau đó (`busy` nếu gọi on sớm)


