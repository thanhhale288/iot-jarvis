/*
 * Trim tinh CP (chan phai) D13 — sau Otto home.
 * CT/BP/BT: hold 90 (khong trim).
 *
 * Serial 115200:
 *   + / -   ±2 us (tinh)
 *   = / _   ±10 us
 *   s       luu NVS key "cp"
 *   z       hold lai
 *   p       in
 */

#include <ESP32Servo.h>
#include <Preferences.h>

#define CP_PIN 13
#define CT_PIN 14
#define BP_PIN 16
#define BT_PIN 26

const int DEFAULT_US = 1500;

Preferences prefs;
Servo cp, ct, bp, bt;
int cpUs = DEFAULT_US;

int usFromDeg(int deg) {
  return 500 + (constrain(deg, 0, 180) * 2000) / 180;
}

void holdOthers90() {
  ct.writeMicroseconds(DEFAULT_US);
  bp.writeMicroseconds(DEFAULT_US);
  bt.writeMicroseconds(DEFAULT_US);
}

void applyCp() {
  cp.writeMicroseconds(cpUs);
  Serial.printf("CP D13 = %d us\n", cpUs);
}

void setup() {
  Serial.begin(115200);
  delay(400);
  prefs.begin("servo", true);
  cpUs = prefs.getInt("cp", DEFAULT_US);
  prefs.end();

  cp.setPeriodHertz(50);
  ct.setPeriodHertz(50);
  bp.setPeriodHertz(50);
  bt.setPeriodHertz(50);
  cp.attach(CP_PIN, 500, 2500);
  ct.attach(CT_PIN, 500, 2500);
  bp.attach(BP_PIN, 500, 2500);
  bt.attach(BT_PIN, 500, 2500);

  holdOthers90();
  applyCp();
  Serial.println("=== TRIM CP D13 ===");
  Serial.println("+/- 2us | =/_ 10us | s luu | p in | z hold");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '+' || c == '.') {
      cpUs = constrain(cpUs + 2, 500, 2500);
      applyCp();
    } else if (c == '-' || c == ',') {
      cpUs = constrain(cpUs - 2, 500, 2500);
      applyCp();
    } else if (c == '=' ) {
      cpUs = constrain(cpUs + 10, 500, 2500);
      applyCp();
    } else if (c == '_') {
      cpUs = constrain(cpUs - 10, 500, 2500);
      applyCp();
    } else if (c == 's' || c == 'S') {
      prefs.begin("servo", false);
      prefs.putInt("cp", cpUs);
      prefs.end();
      Serial.printf("SAVED cp = %d us\n", cpUs);
    } else if (c == 'p' || c == 'P') {
      Serial.printf("CP = %d us (home khac = %d)\n", cpUs, DEFAULT_US);
    } else if (c == 'z' || c == 'Z') {
      holdOthers90();
      applyCp();
      Serial.println("hold");
    }
  }
  delay(20);
}
