/*
 * Smoke BP bàn chân phải D16 — lặp 2 vòng.
 * Serial: 'r' chạy lại.
 */

#include <ESP32Servo.h>

#define BP_PIN 16
#define CP_PIN 13
#define CT_PIN 14
#define BT_PIN 26

const int HOME_US = 1500;
const int LO_US = 1200;
const int HI_US = 1800;

Servo bp, cp, ct, bt;

static void holdOthers() {
  cp.writeMicroseconds(HOME_US);
  ct.writeMicroseconds(HOME_US);
  bt.writeMicroseconds(HOME_US);
}

static void sweepBp() {
  Serial.println("--- BP start (ban chan phai D16) ---");
  bp.writeMicroseconds(HOME_US);
  delay(400);
  bp.writeMicroseconds(LO_US);
  Serial.println("BP -> 1200 us");
  delay(800);
  bp.writeMicroseconds(HOME_US);
  delay(400);
  bp.writeMicroseconds(HI_US);
  Serial.println("BP -> 1800 us");
  delay(800);
  bp.writeMicroseconds(HOME_US);
  Serial.println("--- BP done ---");
  delay(400);
}

static void runTest() {
  holdOthers();
  sweepBp();
  sweepBp();
  Serial.println("ALL DONE — gui 'r' de chay lai");
}

void setup() {
  Serial.begin(115200);
  delay(400);
  bp.setPeriodHertz(50);
  cp.setPeriodHertz(50);
  ct.setPeriodHertz(50);
  bt.setPeriodHertz(50);
  bp.attach(BP_PIN, 500, 2500);
  cp.attach(CP_PIN, 500, 2500);
  ct.attach(CT_PIN, 500, 2500);
  bt.attach(BT_PIN, 500, 2500);
  holdOthers();
  bp.writeMicroseconds(HOME_US);
  Serial.println("=== BP-only smoke ===");
  runTest();
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'r' || c == 'R') runTest();
  }
}
