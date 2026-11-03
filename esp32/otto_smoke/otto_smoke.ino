/*
 * Smoke gait dong bo 4 servo — pin map Jarvis.
 *   YL (chan trai)  CT = D14
 *   YR (chan phai)  CP = D13
 *   RL (ban trai)   BT = D26
 *   RR (ban phai)   BP = D16
 * Buzzer: pin dummy (khong noi) — beep thuoc Uno.
 *
 * Bien do ban chan (BP/BT): don vi do servo (Otto Oscillator).
 * Khop long → FOOT_H = 30 (gap doi so voi smoke cu h=15).
 * walk/turn: A[RL,RR]=40° (patch local OttoDIYLib).
 */

#include <Otto.h>

Otto Otto;

#define LeftLeg 14   // CT
#define RightLeg 13  // CP
#define LeftFoot 26  // BT
#define RightFoot 16 // BP
#define BuzzerPin 15 // khong noi day — tranh pinMode crash

// Bien do BP/BT cho swing / updown / tiptoe (do)
#define FOOT_H 30

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("=== Otto gait sync smoke ===");
  Serial.println("YL14 YR13 RL26 RR16  FOOT_H=30 walk feet=40");

  Otto.init(LeftLeg, RightLeg, LeftFoot, RightFoot, false, BuzzerPin);
  Otto.home();
  Serial.println("home");
  delay(800);
}

void loop() {
  // Hip + foot 90° out of phase — di chuyen dong bo
  Serial.println("walk FORWARD");
  Otto.walk(4, 1000, FORWARD);
  Otto.home();
  delay(500);

  Serial.println("walk BACKWARD");
  Otto.walk(4, 1000, BACKWARD);
  Otto.home();
  delay(500);

  Serial.println("turn LEFT");
  Otto.turn(3, 1000, LEFT);
  Otto.home();
  delay(400);

  Serial.println("turn RIGHT");
  Otto.turn(3, 1000, RIGHT);
  Otto.home();
  delay(400);

  // Chi BP/BT (A={0,0,h,h}) — kiem tra bien do ban chan
  Serial.println("swing FOOT_H");
  Otto.swing(3, 1000, FOOT_H);
  Otto.home();
  delay(400);

  Serial.println("updown FOOT_H");
  Otto.updown(2, 1000, FOOT_H);
  Otto.home();
  delay(400);

  Serial.println("tiptoeSwing FOOT_H");
  Otto.tiptoeSwing(2, 900, FOOT_H);
  Otto.home();
  delay(800);

  Serial.println("--- cycle ---");
  delay(1000);
}
