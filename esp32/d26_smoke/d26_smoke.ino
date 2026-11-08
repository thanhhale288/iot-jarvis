/*
 * Smoke chỉ GPIO D26 — 3 vòng HARD 0/90/180.
 * Serial: 'r' chạy lại.
 */

#include <ESP32Servo.h>

#define PIN26 26

Servo s;

static void sweep() {
  Serial.println("--- D26 HARD start ---");
  for (int i = 0; i < 3; i++) {
    Serial.printf("D26 round %d -> 0\n", i + 1);
    s.write(0);
    delay(900);
    Serial.printf("D26 round %d -> 90\n", i + 1);
    s.write(90);
    delay(700);
    Serial.printf("D26 round %d -> 180\n", i + 1);
    s.write(180);
    delay(900);
    s.write(90);
    delay(400);
  }
  Serial.println("D26 HARD done — gui 'r'");
}

void setup() {
  Serial.begin(115200);
  delay(400);
  s.setPeriodHertz(50);
  s.attach(PIN26, 500, 2500);
  Serial.println("=== D26 ONLY SMOKE ===");
  sweep();
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'r' || c == 'R') sweep();
  }
  delay(20);
}
