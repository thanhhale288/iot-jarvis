/*
 * Smoke D17 rồi D26 — mỗi chân HARD 0/90/180 x2.
 * Serial: 'r' chạy lại | 'a' chỉ D17 | 'b' chỉ D26
 */

#include <ESP32Servo.h>

#define PIN17 17
#define PIN26 26

Servo s17, s26;

static void sweepPin(Servo &s, int pin, const char *label) {
  Serial.printf("--- %s HARD start ---\n", label);
  if (!s.attached()) s.attach(pin, 500, 2500);
  for (int i = 0; i < 2; i++) {
    Serial.printf("%s round %d -> 0\n", label, i + 1);
    s.write(0);
    delay(800);
    Serial.printf("%s round %d -> 90\n", label, i + 1);
    s.write(90);
    delay(600);
    Serial.printf("%s round %d -> 180\n", label, i + 1);
    s.write(180);
    delay(800);
    s.write(90);
    delay(400);
  }
  Serial.printf("%s HARD done\n", label);
}

static void runBoth() {
  // một chân một lúc: detach chân kia
  s26.detach();
  sweepPin(s17, PIN17, "D17");
  delay(300);
  s17.detach();
  sweepPin(s26, PIN26, "D26");
  Serial.println("ALL DONE — r/a/b");
}

void setup() {
  Serial.begin(115200);
  delay(400);
  s17.setPeriodHertz(50);
  s26.setPeriodHertz(50);
  Serial.println("=== D17 + D26 SMOKE ===");
  runBoth();
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'r' || c == 'R') {
      runBoth();
    } else if (c == 'a' || c == 'A') {
      s26.detach();
      sweepPin(s17, PIN17, "D17");
    } else if (c == 'b' || c == 'B') {
      s17.detach();
      sweepPin(s26, PIN26, "D26");
    }
  }
  delay(20);
}
