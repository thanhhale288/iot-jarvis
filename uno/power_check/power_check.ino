// Uno — kiểm tra ổn định nguồn (pin 9V → Vin)
// Đo VCC 5V qua bandgap 1.1V nội. Baud 115200.
// Mỗi ~250ms: vcc_mv, millis, load (0=idle / 1=D8 HIGH giả tải).
// Sau test: nạp lại uno/get_env.

#define PIN_LOAD 8
#define SAMPLE_MS 250UL
#define LOAD_PERIOD_MS 4000UL  // 2s off, 2s on

// mV trên chân 5V (ước lượng; bandgap ~1100mV)
static int readVccMv() {
  ADMUX = _BV(REFS0) | _BV(MUX3) | _BV(MUX2) | _BV(MUX1);
  delay(2);
  ADCSRA |= _BV(ADSC);
  while (bit_is_set(ADCSRA, ADSC)) {
  }
  uint8_t low = ADCL;
  uint8_t high = ADCH;
  long result = (high << 8) | low;
  if (result == 0) {
    return -1;
  }
  return (int)((1100L * 1024L) / result);
}

void setup() {
  pinMode(PIN_LOAD, OUTPUT);
  digitalWrite(PIN_LOAD, LOW);
  Serial.begin(115200);
  delay(300);
  Serial.println(F("power_check v1 — vcc_mv,ms,load"));
}

void loop() {
  static unsigned long nextSample = 0;
  unsigned long now = millis();
  if ((long)(now - nextSample) < 0) {
    return;
  }
  nextSample = now + SAMPLE_MS;

  bool loadOn = ((now / LOAD_PERIOD_MS) % 2) == 1;
  digitalWrite(PIN_LOAD, loadOn ? HIGH : LOW);

  int vcc = readVccMv();
  Serial.print(vcc);
  Serial.print(',');
  Serial.print(now);
  Serial.print(',');
  Serial.println(loadOn ? 1 : 0);
}
