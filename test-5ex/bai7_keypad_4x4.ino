/*
 * Bài 7: Giao tiếp bàn phím 4x4
 * Cần thư viện: Keypad
 * Row pins: 9, 8, 7, 6 | Col pins: 5, 4, 3, 2
 */

#include <Keypad.h>

const byte ROWS = 4;
const byte COLS = 4;

char hexaKeys[ROWS][COLS] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

byte rowPins[ROWS] = {9, 8, 7, 6};
byte colPins[COLS] = {5, 4, 3, 2};

Keypad customKeypad = Keypad(makeKeymap(hexaKeys), rowPins, colPins, ROWS, COLS);

void setup() {
  Serial.begin(9600);
}

void loop() {
  char keyPress = customKeypad.getKey();
  static int keyCount = 0;

  if (keyPress) {
    if (keyPress != '#') {
      Serial.print(keyPress);
      keyCount++;
    }
    if (keyCount >= 10 || keyPress == '#') {
      Serial.println();
      keyCount = 0;
    }
  }
}
