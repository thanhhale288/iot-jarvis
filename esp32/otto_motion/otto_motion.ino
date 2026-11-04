/*
 * Otto act — TFT + servo + Wi‑Fi PROTOCOL (plan-soft B1).
 * TFT: CS22 DC21 MOSI23 SCK18 RST27
 * Servo: YL14 YR13 RL26 RR16  Buzzer dummy D15
 * Không KY-037 / HC-SR04 (ngoài plan).
 *
 * HTTP POST /cmd  body = 1 JSON → response 1 JSON
 * Serial 115200: cùng JSON / lệnh text (debug)
 */

#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <TFT_eSPI.h>
#include <Grobot_Animations.h>
#include <Otto.h>

#include "wifi_config.h"

Otto Otto;
TFT_eSPI tft = TFT_eSPI();
TFT_eSprite canvas = TFT_eSprite(&tft);
GrobotEyes eyes(0x97E0, TFT_BLACK);
WebServer server(80);

#define LeftLeg 14
#define RightLeg 13
#define LeftFoot 26
#define RightFoot 16
#define BuzzerPin 15
#define FOOT_H 30

const MoodData MOOD_LISTEN = {16, 0, -28, 30, 46};
const MoodData MOOD_THINK  = {10, 0, 18, 14, 42};
const MoodData MOOD_SPEAK  = {0, 22, 0, 38, 52};
const MoodData MOOD_SQUINT = {28, 8, 12, 16, 40};
const MoodData MOOD_ANNOY_L = {6, 0, 40, 18, 42};
const MoodData MOOD_ANNOY_R = {6, 0, 18, 18, 42};

struct Face {
  const char *key;
  const char *label;
  MoodData left;
  MoodData right;
  int lookX;
  int lookY;
  uint16_t color;
  uint8_t blush;
  uint8_t mouth;
};

static const Face faces[] = {
  {"idle",      "IDLE",   MOOD_NEUTRAL, MOOD_NEUTRAL, 0, 0,    0x4C9F, 0, 0},
  {"listening", "LISTEN", MOOD_LISTEN,  MOOD_LISTEN,  0, -16,  0xFE60, 1, 0},
  {"thinking",  "THINK",  MOOD_THINK,   MOOD_SQUINT,  16, -10, 0xA11F, 0, 4},
  {"think",     "THINK",  MOOD_THINK,   MOOD_SQUINT,  16, -10, 0xA11F, 0, 4},
  {"speaking",  "SPEAK",  MOOD_SPEAK,   MOOD_SPEAK,   0, 4,    0x07E0, 1, 3},
  {"nod",       "SPEAK",  MOOD_SPEAK,   MOOD_SPEAK,   0, 4,    0x07E0, 1, 3},
  {"happy",     "HAPPY",  MOOD_HAPPY,   MOOD_HAPPY,   0, 6,    0xFEA0, 2, 1},
  {"alert",     "ALERT",  MOOD_ANGRY,   MOOD_ANGRY,   0, 0,    0xF800, 1, 4},
  {"shake",     "ANNOY",  MOOD_ANNOY_L, MOOD_ANNOY_R, 8, 0,    0xFD20, 1, 4},
  {"turn_left", "IDLE",   MOOD_NEUTRAL, MOOD_NEUTRAL, -12, 0,  0x4C9F, 0, 0},
  {"turn_right","IDLE",   MOOD_NEUTRAL, MOOD_NEUTRAL, 12, 0,   0x4C9F, 0, 0},
  {"step_forward","LISTEN", MOOD_LISTEN, MOOD_LISTEN, 0, -8,   0xFE60, 1, 0},
};
static const int FACE_COUNT = sizeof(faces) / sizeof(faces[0]);

static const Face *currentFace = &faces[0];
static uint32_t lastLook = 0;
static bool wifiReady = false;

static const Face *findFace(const char *key) {
  if (!key) return nullptr;
  for (int i = 0; i < FACE_COUNT; i++) {
    if (strcmp(faces[i].key, key) == 0) return &faces[i];
  }
  return nullptr;
}

static void showLabel(const char *label) {
  tft.fillRect(0, 200, 240, 40, TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(2);
  tft.setCursor(8, 208);
  tft.print(label);
}

static void applyFace(const Face *f) {
  if (!f) return;
  currentFace = f;
  eyes.setStyle(f->color, f->blush, f->mouth);
  eyes.setEmotion(f->left, f->right);
  eyes.lookAt(f->lookX, f->lookY);
  showLabel(f->label);
  eyes.renderEmotions(canvas);
  Serial.printf("face=%s\n", f->label);
}

static const char *emotionToMotion(const char *emotion) {
  if (!emotion || !emotion[0]) return nullptr;
  if (strcmp(emotion, "idle") == 0) return "idle";
  if (strcmp(emotion, "listening") == 0) return "idle";
  if (strcmp(emotion, "thinking") == 0) return "think";
  if (strcmp(emotion, "speaking") == 0) return "nod";
  if (strcmp(emotion, "happy") == 0) return "happy";
  if (strcmp(emotion, "alert") == 0) return "alert";
  return nullptr;
}

static bool runMotion(const char *name) {
  if (strcmp(name, "idle") == 0) {
    Otto.home();
    return true;
  }
  if (strcmp(name, "nod") == 0) {
    Otto.bend(1, 1200, LEFT);
    Otto.home();
    return true;
  }
  if (strcmp(name, "shake") == 0) {
    Otto.shakeLeg(1, 1200, RIGHT);
    Otto.home();
    return true;
  }
  if (strcmp(name, "think") == 0) {
    Otto.jitter(3, 600, 20);
    Otto.home();
    return true;
  }
  if (strcmp(name, "happy") == 0) {
    Otto.swing(2, 800, FOOT_H);
    Otto.tiptoeSwing(1, 500, FOOT_H);
    Otto.home();
    return true;
  }
  if (strcmp(name, "alert") == 0) {
    Otto.swing(2, 600, FOOT_H);
    Otto.shakeLeg(1, 1000, LEFT);
    Otto.home();
    return true;
  }
  if (strcmp(name, "turn_left") == 0) {
    Otto.turn(3, 1000, LEFT);
    Otto.home();
    return true;
  }
  if (strcmp(name, "turn_right") == 0) {
    Otto.turn(3, 1000, RIGHT);
    Otto.home();
    return true;
  }
  if (strcmp(name, "step_forward") == 0) {
    Otto.walk(2, 1000, FORWARD);
    Otto.home();
    return true;
  }
  return false;
}

static bool act(const char *key) {
  const Face *f = findFace(key);
  if (f) applyFace(f);

  const char *motion = key;
  const char *mapped = emotionToMotion(key);
  if (mapped) motion = mapped;

  return runMotion(motion);
}

static String buildAck(const char *id, bool ok, const char *field, const char *value,
                       const char *err) {
  JsonDocument doc;
  doc["v"] = 1;
  if (id && id[0]) doc["id"] = id;
  doc["from"] = "esp32";
  doc["ok"] = ok;
  if (ok && field && value) doc[field] = value;
  if (!ok && err) doc["error"] = err;
  String out;
  serializeJson(doc, out);
  return out;
}

static String handleJsonCmd(const char *line) {
  JsonDocument req;
  if (deserializeJson(req, line)) {
    return buildAck("", false, nullptr, nullptr, "bad_args");
  }

  const char *id = req["id"] | "";
  const char *cmd = req["cmd"] | "";
  if (!id[0] || !cmd[0]) {
    return buildAck(id, false, nullptr, nullptr, "bad_args");
  }

  if (strcmp(cmd, "ping") == 0) {
    return buildAck(id, true, nullptr, nullptr, nullptr);
  }

  if (strcmp(cmd, "motion") == 0) {
    const char *name = req["name"] | "";
    if (!name[0] || !act(name)) {
      return buildAck(id, false, nullptr, nullptr, "bad_args");
    }
    return buildAck(id, true, "name", name, nullptr);
  }

  if (strcmp(cmd, "led") == 0) {
    const char *state = req["state"] | "";
    if (!state[0] || !act(state)) {
      return buildAck(id, false, nullptr, nullptr, "bad_args");
    }
    JsonDocument doc;
    doc["v"] = 1;
    doc["id"] = id;
    doc["from"] = "esp32";
    doc["ok"] = true;
    doc["state"] = state;
    const char *m = emotionToMotion(state);
    if (m) doc["name"] = m;
    String out;
    serializeJson(doc, out);
    return out;
  }

  return buildAck(id, false, nullptr, nullptr, "unknown_cmd");
}

static void handleLine(char *line) {
  while (*line == ' ' || *line == '\t') line++;

  if (line[0] != '{') {
    size_t n = strlen(line);
    while (n > 0 && (line[n - 1] == ' ' || line[n - 1] == '\t')) line[--n] = '\0';
    if (n == 0) return;
    String ack = act(line)
                     ? buildAck("s", true, "name", line, nullptr)
                     : buildAck("s", false, nullptr, nullptr, "bad_args");
    Serial.println(ack);
    return;
  }

  String ack = handleJsonCmd(line);
  Serial.println(ack);
}

static void handleHttpCmd() {
  if (server.method() != HTTP_POST) {
    server.send(405, "application/json",
                "{\"v\":1,\"from\":\"esp32\",\"ok\":false,\"error\":\"bad_args\"}");
    return;
  }
  String body = server.arg("plain");
  if (body.length() == 0) body = server.arg(0);
  body.trim();
  if (body.length() == 0) {
    server.send(400, "application/json",
                "{\"v\":1,\"from\":\"esp32\",\"ok\":false,\"error\":\"bad_args\"}");
    return;
  }
  String ack = handleJsonCmd(body.c_str());
  server.send(200, "application/json", ack);
}

static void startHttpServer() {
  server.on("/cmd", HTTP_POST, handleHttpCmd);
  server.on("/ping", HTTP_GET, []() {
    server.send(200, "application/json",
                "{\"v\":1,\"from\":\"esp32\",\"ok\":true,\"cmd\":\"ping\"}");
  });
  server.begin();
  Serial.println("HTTP :80 POST /cmd");
}

static void connectWifi() {
  if (strcmp(WIFI_PASS, "CHANGE_ME") == 0 || strcmp(WIFI_PASS, "YOUR_HOTSPOT_PASSWORD") == 0) {
    Serial.println("WiFi: set WIFI_PASS in wifi_config.h then reflash");
    wifiReady = false;
    return;
  }
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.printf("WiFi connecting to %s", WIFI_SSID);
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - start) < 20000UL) {
    delay(400);
    Serial.print('.');
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    wifiReady = true;
    Serial.print("WiFi OK IP=");
    Serial.println(WiFi.localIP());
    startHttpServer();
  } else {
    wifiReady = false;
    Serial.println("WiFi FAIL — Serial JSON vẫn dùng được");
  }
}

// C5: tự nối lại khi mất AP (không block loop lâu)
static uint32_t wifiRetryAt = 0;

static void serviceWifi() {
  if (strcmp(WIFI_PASS, "CHANGE_ME") == 0 || strcmp(WIFI_PASS, "YOUR_HOTSPOT_PASSWORD") == 0) {
    return;
  }
  if (WiFi.status() == WL_CONNECTED) {
    if (!wifiReady) {
      wifiReady = true;
      Serial.print("WiFi reconnected IP=");
      Serial.println(WiFi.localIP());
      startHttpServer();
    }
    return;
  }
  if (wifiReady) {
    wifiReady = false;
    Serial.println("WiFi lost — will retry");
  }
  if ((long)(millis() - wifiRetryAt) < 0) {
    return;
  }
  wifiRetryAt = millis() + 8000UL;
  Serial.println("WiFi reconnect…");
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASS);
}

void setup() {
  Serial.begin(115200);
  delay(400);
  Serial.println("=== otto_motion TFT+servo+WiFi PROTOCOL ===");

  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  canvas.createSprite(240, 120);

  Otto.init(LeftLeg, RightLeg, LeftFoot, RightFoot, false, BuzzerPin);
  Otto.home();

  applyFace(findFace("idle"));
  connectWifi();
  Serial.println("ready — Serial JSON hoặc POST /cmd");
}

void loop() {
  eyes.renderEmotions(canvas);

  if (millis() - lastLook > 900 && currentFace) {
    eyes.lookAt(currentFace->lookX + random(-10, 11),
                currentFace->lookY + random(-8, 9));
    lastLook = millis();
  }

  serviceWifi();
  if (wifiReady) {
    server.handleClient();
  }

  static char buf[256];
  static size_t len = 0;
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (len == 0) continue;
      buf[len] = '\0';
      handleLine(buf);
      len = 0;
    } else if (len < sizeof(buf) - 1) {
      buf[len++] = c;
    } else {
      len = 0;
      Serial.println(buildAck("", false, nullptr, nullptr, "bad_args"));
    }
  }
}
