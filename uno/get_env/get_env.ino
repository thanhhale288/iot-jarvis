// Jarvis-on-Desk — Uno Tuần 2
// Pin map: xem uno/README.md
// Baud 115200. Một dòng JSON vào → một dòng JSON ra.
// id bắt buộc. relay dùng name=light|fan.
//
// USE_LCD 0: tắt LCD (tránh treo Wire khi backpack lỗi) — bật lại = 1 sau khi I2C ổn.

#include <ArduinoJson.h>
#include <DHT.h>

#define USE_LCD 0

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
#define PUMP_COOLDOWN_MS 5000UL

DHT dht(DHTPIN, DHTTYPE);

#if USE_LCD
LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2);
static unsigned long lcdNextRefresh = 0;
#endif

static bool pumpOn = false;
static unsigned long pumpOffAt = 0;
static unsigned long pumpCooldownUntil = 0;

static bool pumpInCooldown() {
  if (pumpCooldownUntil == 0) {
    return false;
  }
  return (long)(millis() - pumpCooldownUntil) < 0;
}

static void armPumpCooldown() {
  pumpCooldownUntil = millis() + PUMP_COOLDOWN_MS;
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

void handlePump(const char* id, bool on, int seconds) {
  if (seconds < 1) seconds = 1;
  if (seconds > 5) seconds = 5;

  if (on) {
    if (pumpOn || pumpInCooldown()) {
      replyError(id, "busy");
      return;
    }
    digitalWrite(PIN_PUMP, HIGH);
    pumpOn = true;
    pumpOffAt = millis() + (unsigned long)seconds * 1000UL;
  } else {
    bool wasOn = pumpOn;
    digitalWrite(PIN_PUMP, LOW);
    pumpOn = false;
    pumpOffAt = 0;
    if (wasOn) {
      armPumpCooldown();
    }
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
  digitalWrite(PIN_RELAY_LIGHT, LOW);
  digitalWrite(PIN_RELAY_FAN, LOW);
  digitalWrite(PIN_PUMP, LOW);

  Serial.begin(115200);
  dht.begin();

#if USE_LCD
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  delay(200);
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Jarvis Uno T2");
  lcd.setCursor(0, 1);
  lcd.print("LCD OK 0x27");
  lcdNextRefresh = millis() + 2000;
#endif
}

void loop() {
  servicePump();

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
