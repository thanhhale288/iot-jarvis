/*
 * BP diag — CP nhịp chuẩn rồi BP quét mạnh D16.
 * Serial: 'r' full | 'c' chỉ CP | 'b' chỉ BP
 */

#include <ESP32Servo.h>

#define CP_PIN 13
#define BP_PIN 16
#define CT_PIN 14
#define BT_PIN 26

Servo cp, bp, ct, bt;

static void detachOthers() {
  ct.detach();
  bt.detach();
}

static void pulseCp() {
  Serial.println("REF CP D13 — neu CP khong nhuc: nguon/GND chung");
  if (!cp.attached()) cp.attach(CP_PIN, 500, 2500);
  cp.write(60);
  delay(600);
  cp.write(120);
  delay(600);
  cp.write(90);
  delay(400);
  Serial.println("CP ref done");
}

static void sweepBpHard() {
  Serial.println("BP D16 HARD 0 / 90 / 180");
  if (!bp.attached()) bp.attach(BP_PIN, 500, 2500);
  for (int i = 0; i < 3; i++) {
    Serial.printf("BP round %d -> 0\n", i + 1);
    bp.write(0);
    delay(900);
    Serial.printf("BP round %d -> 90\n", i + 1);
    bp.write(90);
    delay(700);
    Serial.printf("BP round %d -> 180\n", i + 1);
    bp.write(180);
    delay(900);
    bp.write(90);
    delay(500);
  }
  Serial.println("BP HARD done");
}

static void runFull() {
  detachOthers();
  pulseCp();
  delay(400);
  // detach CP de giam tai nguon khi BP quet
  cp.detach();
  delay(200);
  sweepBpHard();
  Serial.println("ALL DONE — r/c/b");
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
  Serial.println("=== BP DIAG ===");
  Serial.println("1) CP nhịp  2) BP 0↔180 x3 (CT/BT detach)");
  runFull();
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'r' || c == 'R') {
      runFull();
    } else if (c == 'c' || c == 'C') {
      detachOthers();
      bp.detach();
      pulseCp();
    } else if (c == 'b' || c == 'B') {
      detachOthers();
      cp.detach();
      sweepBpHard();
    }
  }
  delay(20);
}
