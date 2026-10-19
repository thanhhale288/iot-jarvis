/*
 * Bài 1: Các LED đơn — hiệu ứng LED bằng Arduino
 * Đấu nối: chân 2–13 Arduino với 12 LED đơn
 *   D2→LED1 … D13→LED12
 */

const int ledPins[] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13};
const int numLeds = sizeof(ledPins) / sizeof(ledPins[0]);

void allOn();
void allOff();
void blinkAll();
void runningLight();
void chasing();
void randomBlink();
void knightRider();
void sparkle();
void fadeInOut();
void alternatingBlink();

void setup() {
  for (int i = 0; i < numLeds; i++) {
    pinMode(ledPins[i], OUTPUT);
  }
}

void loop() {
  allOn();
  delay(1000);

  allOff();
  delay(1000);

  blinkAll();
  delay(1000);

  runningLight();
  delay(2000);

  chasing();
  delay(2000);

  randomBlink();
  delay(2000);

  knightRider();
  delay(2000);

  sparkle();
  delay(2000);

  fadeInOut();
  delay(3000);

  alternatingBlink();
  delay(2000);
}

void allOn() {
  for (int i = 0; i < numLeds; i++) {
    digitalWrite(ledPins[i], HIGH);
  }
}

void allOff() {
  for (int i = 0; i < numLeds; i++) {
    digitalWrite(ledPins[i], LOW);
  }
}

void blinkAll() {
  allOn();
  delay(500);
  allOff();
  delay(500);
}

void runningLight() {
  for (int i = 0; i < numLeds; i++) {
    digitalWrite(ledPins[i], HIGH);
    delay(200);
    digitalWrite(ledPins[i], LOW);
  }
}

void chasing() {
  for (int i = 0; i < numLeds; i++) {
    digitalWrite(ledPins[i], HIGH);
    delay(100);
    digitalWrite(ledPins[i], LOW);
  }
}

void randomBlink() {
  for (int i = 0; i < 5; i++) {
    int randomLed = random(numLeds);
    digitalWrite(ledPins[randomLed], HIGH);
    delay(100);
    digitalWrite(ledPins[randomLed], LOW);
  }
}

void knightRider() {
  for (int i = 0; i < numLeds; i++) {
    digitalWrite(ledPins[i], HIGH);
    delay(100);
  }
  for (int i = numLeds - 1; i >= 0; i--) {
    digitalWrite(ledPins[i], LOW);
    delay(100);
  }
}

void sparkle() {
  for (int i = 0; i < numLeds; i++) {
    digitalWrite(ledPins[i], HIGH);
    delay(100);
    digitalWrite(ledPins[i], LOW);
  }
  int randomLed = random(numLeds);
  digitalWrite(ledPins[randomLed], HIGH);
  delay(300);
}

void fadeInOut() {
  for (int brightness = 0; brightness <= 255; brightness++) {
    for (int i = 0; i < numLeds; i++) {
      analogWrite(ledPins[i], brightness);
    }
    delay(10);
  }
  for (int brightness = 255; brightness >= 0; brightness--) {
    for (int i = 0; i < numLeds; i++) {
      analogWrite(ledPins[i], brightness);
    }
    delay(10);
  }
}

void alternatingBlink() {
  for (int i = 0; i < numLeds; i += 2) {
    digitalWrite(ledPins[i], HIGH);
  }
  delay(500);
  for (int i = 0; i < numLeds; i += 2) {
    digitalWrite(ledPins[i], LOW);
  }
  for (int i = 1; i < numLeds; i += 2) {
    digitalWrite(ledPins[i], HIGH);
  }
  delay(500);
  for (int i = 1; i < numLeds; i += 2) {
    digitalWrite(ledPins[i], LOW);
  }
}
