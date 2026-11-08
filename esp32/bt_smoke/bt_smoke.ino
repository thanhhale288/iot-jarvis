/*
 * Smoke BT bàn chân trái D26 — lặp 2 vòng.
 * Serial: 'r' chạy lại.
 */

#include <ESP32Servo.h>

#define BT_PIN 26
#define CP_PIN 13
#define CT_PIN 14
#define BP_PIN 16

const int HOME_US = 1500;
const int LO_US = 1200;
const int HI_US = 1800;

Servo bt, cp, ct, bp;

static void holdOthers() {
  cp.writeMicroseconds(HOME_US);
  ct.writeMicroseconds(HOME_US);
  bp.writeMicroseconds(HOME_US);
}

static void sweepBt() {
  Serial.println("--- BT start (ban chan trai D26) ---");
  bt.writeMicroseconds(HOME_US);
  delay(400);
  bt.writeMicroseconds(LO_US);
  Serial.println("BT -> 1200 us");
  delay(800);
  bt.writeMicroseconds(HOME_US);
  delay(400);
  bt.writeMicroseconds(HI_US);
  Serial.println("BT -> 1800 us");
  delay(800);
  bt.writeMicroseconds(HOME_US);
  Serial.println("BT done");
}

void setup() {
  Serial.begin(115200);
  delay(400);

  bt.setPeriodHertz(50);
  cp.setPeriodHertz(50);
  ct.setPeriodHertz(50);
  bp.setPeriodHertz(50);
  bt.attach(BT_PIN, 500, 2500);
  cp.attach(CP_PIN, 500, 2500);
  ct.attach(CT_PIN, 500, 2500);
  bp.attach(BP_PIN, 500, 2500);

  holdOthers();
  Serial.println("=== BT SMOKE D26 ===");
  for (int i = 0; i < 2; i++) {
    Serial.printf("round %d\n", i + 1);
    sweepBt();
    delay(300);
  }
  Serial.println("ALL DONE — gui 'r' de chay lai");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'r' || c == 'R') {
      holdOthers();
      for (int i = 0; i < 2; i++) {
        Serial.printf("round %d\n", i + 1);
        sweepBt();
        delay(300);
      }
      Serial.println("ALL DONE");
    }
  }
  delay(20);
}
