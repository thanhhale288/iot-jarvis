// TFT ST7789 smoke test — pin map Jarvis Otto
// CS→D22 DC→D21 MOSI→D23 SCK→D18 RST→D27 VCC→3V3 GND→GND BL→3V3

#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>

static const int PIN_CS  = 22;
static const int PIN_DC  = 21;
static const int PIN_RST = 27;
// ESP32 VSPI defaults: MOSI=23, SCK=18

Adafruit_ST7789 tft = Adafruit_ST7789(PIN_CS, PIN_DC, PIN_RST);

void fillScreenColor(uint16_t color, const char *name) {
  tft.fillScreen(color);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.setCursor(10, 100);
  tft.print(name);
  Serial.printf("screen=%s\n", name);
  delay(900);
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.println("TFT ST7789 test start");
  Serial.println("pins CS=22 DC=21 RST=27 MOSI=23 SCK=18");

  // Most 1.3–1.54" modules are 240x240; change to init(240, 320) if blank/wrong.
  tft.init(240, 240);
  tft.setRotation(0);

  fillScreenColor(ST77XX_RED, "RED");
  fillScreenColor(ST77XX_GREEN, "GREEN");
  fillScreenColor(ST77XX_BLUE, "BLUE");
  fillScreenColor(ST77XX_BLACK, "OK");

  tft.setTextColor(ST77XX_GREEN);
  tft.setTextSize(3);
  tft.setCursor(40, 90);
  tft.println("TFT OK");
  tft.setTextSize(2);
  tft.setCursor(20, 140);
  tft.println("ST7789 240");

  Serial.println("TFT test done — look at screen colors");
}

void loop() {
  delay(2000);
  Serial.println("alive");
}
