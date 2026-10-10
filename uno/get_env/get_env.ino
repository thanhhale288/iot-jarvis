// Jarvis-on-Desk — Uno Tuần 1
// Wiring: DHT11 (STT 6) VCC→5V, GND→GND, DATA→D2
// Baud 115200. Một dòng JSON vào → một dòng JSON ra.

#include <ArduinoJson.h>
#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

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
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (isnan(t) || isnan(h)) {
    replyError(id, "sensor");
    return;
  }

  StaticJsonDocument<192> doc;
  doc["v"] = 1;
  if (id && id[0]) {
    doc["id"] = id;
  }
  doc["from"] = "uno";
  doc["ok"] = true;
  doc["temp"] = round(t * 10) / 10.0;
  doc["hum"] = round(h * 10) / 10.0;
  doc["light"] = -1;  // tuần 1 chưa gắn LDR
  doc["soil"] = -1;   // tuần 1 chưa gắn đất
  sendLine(doc);
}

// Tuần 1: stub ACK — chưa bật relay/bơm thật
void handleRelay(const char* id, bool on) {
  StaticJsonDocument<128> doc;
  doc["v"] = 1;
  if (id && id[0]) {
    doc["id"] = id;
  }
  doc["from"] = "uno";
  doc["ok"] = true;
  doc["on"] = on;
  sendLine(doc);
}

void handlePump(const char* id, bool on, int seconds) {
  if (seconds < 1) seconds = 1;
  if (seconds > 5) seconds = 5;
  StaticJsonDocument<128> doc;
  doc["v"] = 1;
  if (id && id[0]) {
    doc["id"] = id;
  }
  doc["from"] = "uno";
  doc["ok"] = true;
  doc["on"] = on;
  doc["seconds"] = seconds;
  sendLine(doc);
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

  if (strcmp(cmd, "get_env") == 0) {
    handleGetEnv(id);
  } else if (strcmp(cmd, "relay") == 0) {
    handleRelay(id, req["on"] | false);
  } else if (strcmp(cmd, "pump") == 0) {
    handlePump(id, req["on"] | false, req["seconds"] | 2);
  } else {
    replyError(id, "unknown_cmd");
  }
}

void setup() {
  Serial.begin(115200);
  dht.begin();
}

void loop() {
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
    } else if (len + 1 < sizeof(buf)) {
      buf[len++] = c;
    } else {
      len = 0;
    }
  }
}
