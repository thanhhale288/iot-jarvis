/*
 * Smoke CP (D13) + BP (D16) — lần lượt, giữ CT/BT @ 1500us.
 * Serial 115200: tự chạy khi boot; gửi 'r' để chạy lại.
 */

#include <ESP32Servo.h>

#define CP_PIN 13
#define BP_PIN 16
#define CT_PIN 14
#define BT_PIN 26

const int HOME_US = 1500;
const int LO_US = 1200;
const int HI_US = 1800;

Servo cp, bp, ct, bt;

static void holdSide() {
  ct.writeMicroseconds(HOME_US);
  bt.writeMicroseconds(HOME_US);
}

static void sweep(Servo &s, const char *name) {
  Serial.printf("--- %s start ---\n", name);
  s.writeMicroseconds(HOME_US);
  delay(400);
  s.writeMicroseconds(LO_US);
  Serial.printf("%s -> %d us\n", name, LO_US);
  delay(700);
  s.writeMicroseconds(HOME_US);
  delay(400);
  s.writeMicroseconds(HI_US);
  Serial.printf("%s -> %d us\n", name, HI_US);
  delay(700);
  s.writeMicroseconds(HOME_US);
  Serial.printf("--- %s done (home) ---\n", name);
  delay(500);
}

static void runTest() {
  holdSide();
  Serial.println("TEST CP (chan phai D13)");
  sweep(cp, "CP");
  Serial.println("TEST BP (ban chan phai D16)");
  sweep(bp, "BP");
  Serial.println("ALL DONE — gui 'r' de chay lai");
}

void setup() {
  Serial.begin(115200);
  delay(400);

  cp.setPeriodHertz(50);
  bp.setPeriodHertz(50);
  ct.setPeriodHertz(50);
  bt.setPeriodHertz(50);
  cp.attach(CP_PIN, 500, 2500);
  bp.attach(BP_PIN, 500, 2500);
  ct.attach(CT_PIN, 500, 2500);
  bt.attach(BT_PIN, 500, 2500);

  holdSide();
  cp.writeMicroseconds(HOME_US);
  bp.writeMicroseconds(HOME_US);
  Serial.println("=== CP/BP smoke ===");
  runTest();
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'r' || c == 'R') runTest();
  }
}
