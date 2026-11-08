// Jarvis-on-Desk — Uno Tuần 2 + plan-soft C1/C2/C5
// Pin map: xem uno/README.md
// Baud 115200. Một dòng JSON vào → một dòng JSON ra.
// C1: IR D3 → event name=ir
// C2: ~60s soil khô → beep D6
// C5: đất khô → bơm local (không cần laptop)
//
// USE_LCD 0: tắt LCD (tránh treo Wire khi backpack lỗi) — bật lại = 1 sau khi I2C ổn.

#include <ArduinoJson.h>
#include <DHT.h>
#include <IRremote.hpp>

#define USE_LCD 0
#define USE_IR 1
#define AUTO_WATER 1

#if USE_LCD
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#define LCD_ADDR 0x27
#define LCD_REFRESH_MS 2000UL
#endif

#define DHTPIN 2
#define DHTTYPE DHT11
#define PIN_LIGHT_ADC A0
#define PIN_SOIL_ADC A1
#define PIN_RELAY_LIGHT 7
#define PIN_RELAY_FAN 8
#define PIN_PUMP 9
#define PIN_BUZZER 6
#define PIN_IR 3
#define PUMP_COOLDOWN_MS 5000UL
#define THRESHOLD_MS 60000UL
#define SOIL_DRY_THRESHOLD 650
#define AUTO_PUMP_SECONDS 2

DHT dht(DHTPIN, DHTTYPE);

#if USE_LCD
LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2);
static unsigned long lcdNextRefresh = 0;
#endif

static bool pumpOn = false;
static unsigned long pumpOffAt = 0;
static unsigned long pumpCooldownUntil = 0;
static unsigned long nextThresholdAt = 0;

static bool pumpInCooldown() {
  if (pumpCooldownUntil == 0) {
    return false;
  }
  return (long)(millis() - pumpCooldownUntil) < 0;
}

static void armPumpCooldown() {
  pumpCooldownUntil = millis() + PUMP_COOLDOWN_MS;
}

static void beep(unsigned ms = 120) {
  digitalWrite(PIN_BUZZER, HIGH);
  delay(ms);
  digitalWrite(PIN_BUZZER, LOW);
}

static void beepAlert() {
  beep(80);
  delay(60);
  beep(80);
}

#if USE_LCD
static void refreshLcd(float t, float h, int light, int soil) {
  char line0[17];
  char line1[17];
  snprintf(line0, sizeof(line0), "T%4.1fC H%4.1f%%", t, h);
  snprintf(line1, sizeof(line1), "L%4d S%4d", light, soil);
  lcd.setCursor(0, 0);
  lcd.print(line0);
  lcd.setCursor(0, 1);
  lcd.print(line1);
}

static void safeRefreshLcdFromSensors() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  int light = analogRead(PIN_LIGHT_ADC);
  int soil = analogRead(PIN_SOIL_ADC);
  if (isnan(t) || isnan(h)) {
    lcd.setCursor(0, 0);
    lcd.print("DHT error       ");
    lcd.setCursor(0, 1);
    lcd.print("check D2 wiring ");
    return;
  }
  refreshLcd(t, h, light, soil);
}
#endif

void sendLine(const JsonDocument& doc) {
  serializeJson(doc, Serial);
  Serial.println();
}

void replyError(const char* id, const char* err) {
  StaticJsonDocument<128> doc;
  doc["v"] = 1;
  if (id && id[0]) {
    doc["id"] = id;
  }
  doc["from"] = "uno";
  doc["ok"] = false;
  doc["error"] = err;
  sendLine(doc);
}

void emitIrEvent(const char* codeHex) {
  StaticJsonDocument<128> doc;
  doc["v"] = 1;
  doc["from"] = "uno";
  doc["cmd"] = "event";
  doc["name"] = "ir";
  doc["code"] = codeHex;
  sendLine(doc);
}

void handleGetEnv(const char* id) {
  float t = NAN;
  float h = NAN;
  for (int i = 0; i < 3; i++) {
    t = dht.readTemperature();
    h = dht.readHumidity();
    if (!isnan(t) && !isnan(h)) {
      break;
    }
    delay(50);
  }
  if (isnan(t) || isnan(h)) {
    replyError(id, "sensor");
    return;
  }

  StaticJsonDocument<192> doc;
  doc["v"] = 1;
  doc["id"] = id;
  doc["from"] = "uno";
  doc["ok"] = true;
  doc["temp"] = round(t * 10) / 10.0;
  doc["hum"] = round(h * 10) / 10.0;
  doc["light"] = analogRead(PIN_LIGHT_ADC);
  doc["soil"] = analogRead(PIN_SOIL_ADC);
  sendLine(doc);
}

void handleRelay(const char* id, const char* name, bool on) {
  int pin = -1;
  if (strcmp(name, "light") == 0) {
    pin = PIN_RELAY_LIGHT;
  } else if (strcmp(name, "fan") == 0) {
    pin = PIN_RELAY_FAN;
  } else {
    replyError(id, "bad_args");
    return;
  }

  digitalWrite(pin, on ? HIGH : LOW);

  StaticJsonDocument<128> doc;
  doc["v"] = 1;
  doc["id"] = id;
  doc["from"] = "uno";
  doc["ok"] = true;
  doc["name"] = name;
  doc["on"] = on;
  sendLine(doc);
}

// on=true returns false if busy (caller may silence Serial for auto)
bool startPump(int seconds) {
  if (seconds < 1) seconds = 1;
  if (seconds > 5) seconds = 5;
  if (pumpOn || pumpInCooldown()) {
    return false;
  }
  digitalWrite(PIN_PUMP, HIGH);
  pumpOn = true;
  pumpOffAt = millis() + (unsigned long)seconds * 1000UL;
  return true;
}

void stopPump() {
  bool wasOn = pumpOn;
  digitalWrite(PIN_PUMP, LOW);
  pumpOn = false;
  pumpOffAt = 0;
  if (wasOn) {
    armPumpCooldown();
  }
}

void handlePump(const char* id, bool on, int seconds) {
  if (seconds < 1) seconds = 1;
  if (seconds > 5) seconds = 5;

  if (on) {
    if (!startPump(seconds)) {
      replyError(id, "busy");
      return;
    }
  } else {
    stopPump();
  }

  StaticJsonDocument<128> doc;
  doc["v"] = 1;
  doc["id"] = id;
  doc["from"] = "uno";
  doc["ok"] = true;
  doc["on"] = on;
  doc["seconds"] = seconds;
  sendLine(doc);
}

void servicePump() {
  if (pumpOn && pumpOffAt != 0 && (long)(millis() - pumpOffAt) >= 0) {
    digitalWrite(PIN_PUMP, LOW);
    pumpOn = false;
    pumpOffAt = 0;
    armPumpCooldown();
  }
}

// C2 + C5: mỗi ~60s — khô → beep; AUTO_WATER → bơm 2s
void serviceThreshold() {
  if ((long)(millis() - nextThresholdAt) < 0) {
    return;
  }
  nextThresholdAt = millis() + THRESHOLD_MS;

  int soil = analogRead(PIN_SOIL_ADC);
  if (soil < SOIL_DRY_THRESHOLD) {
    return;  // đủ ẩm
  }

  beepAlert();

#if AUTO_WATER
  if (startPump(AUTO_PUMP_SECONDS)) {
    // local only — không spam Serial khi laptop rút
  }
#endif
}

#if USE_IR
void serviceIr() {
  if (!IrReceiver.decode()) {
    return;
  }
  // Prefer classic 24-bit style (vd FFA25D); fallback raw 32-bit
  unsigned long v = IrReceiver.decodedIRData.decodedRawData;
  if (v == 0 && IrReceiver.decodedIRData.command != 0) {
    v = ((unsigned long)IrReceiver.decodedIRData.address << 8) |
        IrReceiver.decodedIRData.command;
  }
  char code[12];
  if (v <= 0xFFFFFFUL) {
    snprintf(code, sizeof(code), "%06lX", v);
  } else {
    snprintf(code, sizeof(code), "%08lX", v);
  }
  emitIrEvent(code);
  IrReceiver.resume();
}
#endif

void handleLine(char* line) {
  StaticJsonDocument<256> req;
  if (deserializeJson(req, line)) {
    replyError("", "bad_args");
    return;
  }

  const char* id = req["id"] | "";
  const char* to = req["to"] | "uno";
  const char* cmd = req["cmd"] | "";

  if (strcmp(to, "uno") != 0) {
    return;
  }

  if (!id[0]) {
    replyError("", "bad_args");
    return;
  }

  if (strcmp(cmd, "get_env") == 0) {
    handleGetEnv(id);
  } else if (strcmp(cmd, "relay") == 0) {
    const char* name = req["name"] | "";
    handleRelay(id, name, req["on"] | false);
  } else if (strcmp(cmd, "pump") == 0) {
    handlePump(id, req["on"] | false, req["seconds"] | 2);
  } else {
    replyError(id, "unknown_cmd");
  }
}

void setup() {
  pinMode(PIN_RELAY_LIGHT, OUTPUT);
  pinMode(PIN_RELAY_FAN, OUTPUT);
  pinMode(PIN_PUMP, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_RELAY_LIGHT, LOW);
  digitalWrite(PIN_RELAY_FAN, LOW);
  digitalWrite(PIN_PUMP, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  Serial.begin(115200);
  dht.begin();

#if USE_IR
  IrReceiver.begin(PIN_IR, DISABLE_LED_FEEDBACK);
#endif

  nextThresholdAt = millis() + THRESHOLD_MS;
  beep(40);  // boot chirp

#if USE_LCD
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  delay(200);
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Jarvis Uno C");
  lcd.setCursor(0, 1);
  lcd.print("IR+auto soil");
  lcdNextRefresh = millis() + 2000;
#endif
}

void loop() {
  servicePump();
  serviceThreshold();
#if USE_IR
  serviceIr();
#endif

#if USE_LCD
  if ((long)(millis() - lcdNextRefresh) >= 0) {
    if (Wire.getWireTimeoutFlag()) {
      Wire.clearWireTimeoutFlag();
    } else {
      safeRefreshLcdFromSensors();
    }
    lcdNextRefresh = millis() + LCD_REFRESH_MS;
  }
#endif

  static char buf[256];
  static size_t len = 0;

  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (len == 0) {
        continue;
      }
      buf[len] = '\0';
      handleLine(buf);
      len = 0;
    } else if (len < sizeof(buf) - 1) {
      buf[len++] = c;
    } else {
      len = 0;
      replyError("", "bad_args");
    }
  }
}
