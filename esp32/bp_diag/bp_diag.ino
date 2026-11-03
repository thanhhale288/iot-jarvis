/*
 * BP diag — biên độ tối đa + CP nhịp chuẩn.
 * Nhìn: (1) CP nhịp 1 lần → (2) BP quét 0→90→180×3
 * Serial: 'r' chạy lại | 'c' chỉ CP | 'b' chỉ BP
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
  cp.detach();
}

static void pulseCp() {
  Serial.println("REF CP D13 — neu CP khong nhuc: check 5V + GND chung");
  bp.detach();
  ct.detach();
  bt.detach();
  cp.attach(CP_PIN, 500, 2500);
  cp.write(60);
  delay(600);
  cp.write(120);
  delay(600);
  cp.write(90);
  delay(400);
  cp.detach();
}

static void sweepBpHard() {
  Serial.println("BP D16 ONLY (detach 3 servo khac) 0/90/180");
  detachOthers();
  bp.attach(BP_PIN, 500, 2500);
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

static void runAll() {
  pulseCp();
  sweepBpHard();
  Serial.println("DONE — 'r' all | 'c' CP | 'b' BP");
}

void setup() {
  Serial.begin(115200);
  delay(500);

  cp.setPeriodHertz(50);
  bp.setPeriodHertz(50);
  ct.setPeriodHertz(50);
  bt.setPeriodHertz(50);

  Serial.println("=== BP DIAG ===");
  Serial.printf("CP=D%d BP=D%d — 1 PWM, 3 detach\n", CP_PIN, BP_PIN);
  runAll();
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'r' || c == 'R') runAll();
    if (c == 'c' || c == 'C') pulseCp();
    if (c == 'b' || c == 'B') sweepBpHard();
  }
}
