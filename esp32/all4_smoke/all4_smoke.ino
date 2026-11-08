/*
 * Smoke 4 servo lần lượt: CP D13 → CT D14 → BP D16 → BT D26.
 * Serial 115200: boot tự chạy; 'r' chạy lại.
 */

#include <ESP32Servo.h>

#define CP_PIN 13
#define CT_PIN 14
#define BP_PIN 16
#define BT_PIN 26

const int HOME_US = 1500;
const int LO_US = 1200;
const int HI_US = 1800;

Servo cp, ct, bp, bt;

struct Joint {
  Servo *s;
  const char *name;
};

Joint joints[4];

static void holdAll() {
  cp.writeMicroseconds(HOME_US);
  ct.writeMicroseconds(HOME_US);
  bp.writeMicroseconds(HOME_US);
  bt.writeMicroseconds(HOME_US);
}

static void sweepOne(Joint &j) {
  Serial.printf("--- %s start ---\n", j.name);
  j.s->writeMicroseconds(HOME_US);
  delay(350);
  j.s->writeMicroseconds(LO_US);
  Serial.printf("%s -> %d us\n", j.name, LO_US);
  delay(700);
  j.s->writeMicroseconds(HOME_US);
  delay(350);
  j.s->writeMicroseconds(HI_US);
  Serial.printf("%s -> %d us\n", j.name, HI_US);
  delay(700);
  j.s->writeMicroseconds(HOME_US);
  Serial.printf("%s done\n", j.name);
  delay(250);
}

static void runAll() {
  holdAll();
  for (int i = 0; i < 4; i++) {
    sweepOne(joints[i]);
  }
  Serial.println("ALL DONE — gui 'r' de chay lai");
}

void setup() {
  Serial.begin(115200);
  delay(400);

  joints[0] = {&cp, "CP D13"};
  joints[1] = {&ct, "CT D14"};
  joints[2] = {&bp, "BP D16"};
  joints[3] = {&bt, "BT D26"};

  cp.setPeriodHertz(50);
  ct.setPeriodHertz(50);
  bp.setPeriodHertz(50);
  bt.setPeriodHertz(50);
  cp.attach(CP_PIN, 500, 2500);
  ct.attach(CT_PIN, 500, 2500);
  bp.attach(BP_PIN, 500, 2500);
  bt.attach(BT_PIN, 500, 2500);

  Serial.println("=== ALL4 SERVO SMOKE ===");
  Serial.println("Thu tu: CP -> CT -> BP -> BT");
  runAll();
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'r' || c == 'R') {
      runAll();
    }
  }
  delay(20);
}
