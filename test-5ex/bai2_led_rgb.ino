/*
 * Bài 2: LED RGB WS2812
 * Đấu nối: D3 → DIN của LED WS2812
 * Cần thư viện: Adafruit NeoPixel
 */

#include <Adafruit_NeoPixel.h>

#define LED_PIN 3
#define NUM_LEDS 12
#define BRIGHTNESS 5
#define LED_TYPE NEO_GRB + NEO_KHZ800

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, LED_TYPE);

void setup() {
  strip.begin();
  strip.show();
  strip.setBrightness(BRIGHTNESS);
}

void loop() {
  rainbowCycle(20);
}

void rainbowCycle(int wait) {
  uint16_t i, j;

  for (j = 0; j < 256 * 5; j++) {
    for (i = 0; i < strip.numPixels(); i++) {
      strip.setPixelColor(i, Wheel((i + j) & 255));
    }
    strip.show();
    delay(wait);
  }
}

uint32_t Wheel(byte WheelPos) {
  if (WheelPos < 85) {
    return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
  } else if (WheelPos < 170) {
    WheelPos -= 85;
    return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  } else {
    WheelPos -= 170;
    return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  }
}
