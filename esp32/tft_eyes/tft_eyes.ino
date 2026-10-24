// Grobot eyes — many faces. Pins: CS22 DC21 MOSI23 SCK18 RST27.

#include <TFT_eSPI.h>
#include <Grobot_Animations.h>

TFT_eSPI tft = TFT_eSPI();
TFT_eSprite canvas = TFT_eSprite(&tft);
GrobotEyes eyes(0x97E0, TFT_BLACK);

// topH, botH, tilt, pupil, radius
const MoodData MOOD_LISTEN   = {16, 0, -28, 30, 46};
const MoodData MOOD_THINK    = {10, 0, 18, 14, 42};
const MoodData MOOD_SPEAK    = {0, 22, 0, 38, 52};
const MoodData MOOD_WOW      = {0, 0, 0, 40, 58};
const MoodData MOOD_SLEEP    = {55, 0, 0, 12, 40};
const MoodData MOOD_SQUINT   = {28, 8, 12, 16, 40};
const MoodData MOOD_SCARE    = {0, 0, 8, 10, 56};
const MoodData MOOD_BORED    = {32, 0, 0, 18, 40};
const MoodData MOOD_SMILE_L  = {0, 55, -8, 28, 46};
const MoodData MOOD_LOVE     = {0, 42, 0, 22, 48};
const MoodData MOOD_SHOCK    = {0, 0, 0, 8, 54};
const MoodData MOOD_ANNOY_L  = {6, 0, 40, 18, 42};
const MoodData MOOD_ANNOY_R  = {6, 0, 18, 18, 42};
const MoodData MOOD_CONF_L   = {8, 0, -40, 22, 44};
const MoodData MOOD_CONF_R   = {0, 0, 45, 26, 44};

struct Face {
  const char *label;
  MoodData left;
  MoodData right;
  int lookX;
  int lookY;
  uint16_t color;
  uint8_t blush;  // 0 none, 1 pink, 2 heavy
  uint8_t mouth;  // 0 none 1 smile 2 sad 3 open 4 flat 5 tiny
};

static const Face faces[] = {
  {"IDLE",    MOOD_NEUTRAL, MOOD_NEUTRAL, 0, 0,    0x4C9F, 0, 0},
  {"LISTEN",  MOOD_LISTEN,  MOOD_LISTEN,  0, -16,  0xFE60, 1, 0},
  {"THINK",   MOOD_THINK,   MOOD_SQUINT,  16, -10, 0xA11F, 0, 4},
  {"SPEAK",   MOOD_SPEAK,   MOOD_SPEAK,   0, 4,    0x07E0, 1, 3},
  {"HAPPY",   MOOD_HAPPY,   MOOD_HAPPY,   0, 6,    0xFEA0, 2, 1},
  {"ALERT",   MOOD_ANGRY,   MOOD_ANGRY,   0, 0,    0xF800, 1, 4},
  {"SAD",     MOOD_SAD,     MOOD_SAD,     0, 10,   0x2B7F, 0, 2},
  {"WINK",    MOOD_NEUTRAL, MOOD_WINK,    -6, 0,   0xF81F, 2, 5},
  {"WOW",     MOOD_WOW,     MOOD_WOW,     0, -8,   0xFFE0, 1, 3},
  {"SLEEP",   MOOD_SLEEP,   MOOD_SLEEP,   0, 8,    0x4A69, 0, 4},
  {"ANNOY",   MOOD_ANNOY_L, MOOD_ANNOY_R,  8, 0,    0xFD20, 1, 4},
  {"SCARE",   MOOD_SCARE,   MOOD_SCARE,   -14, -6, 0x07FF, 0, 3},
  {"CONFUSE", MOOD_CONF_L,  MOOD_CONF_R,  10, -4,  0xC81F, 1, 4},
  {"SMIRK",   MOOD_SMILE_L, MOOD_SQUINT,  12, 2,   0xFB56, 2, 5},
  {"BORED",   MOOD_BORED,   MOOD_BORED,   0, 6,    0x6C84, 0, 4},
  {"SHOCK",   MOOD_SHOCK,   MOOD_SHOCK,   0, 0,    0xFBE0, 1, 3},
  {"LOVE",    MOOD_LOVE,    MOOD_LOVE,    0, 4,    0xF97F, 2, 5},
  {"SHY",     MOOD_LISTEN,  MOOD_SQUINT,  -4, 8,   0xFC9F, 2, 5},
};
static const int FACE_COUNT = sizeof(faces) / sizeof(faces[0]);

uint32_t lastSwitch = 0;
uint32_t lastLook = 0;
int faceIndex = 0;

void showLabel(const char *label) {
  tft.fillRect(0, 200, 240, 40, TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(2);
  tft.setCursor(8, 208);
  tft.print(label);
}

void applyFace(int index) {
  const Face &f = faces[index];
  eyes.setStyle(f.color, f.blush, f.mouth);
  eyes.setEmotion(f.left, f.right);
  eyes.lookAt(f.lookX, f.lookY);
  showLabel(f.label);
  Serial.printf("emotion=%s\n", f.label);
}

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("Grobot eyes — many");

  tft.init();
  tft.setRotation(1);  // 90° ngang
  tft.fillScreen(TFT_BLACK);
  canvas.createSprite(240, 120);
  applyFace(0);
}

void loop() {
  eyes.renderEmotions(canvas);

  if (millis() - lastLook > 900) {
    const Face &f = faces[faceIndex];
    eyes.lookAt(f.lookX + random(-10, 11), f.lookY + random(-8, 9));
    lastLook = millis();
  }

  if (millis() - lastSwitch > 2800) {
    faceIndex = (faceIndex + 1) % FACE_COUNT;
    applyFace(faceIndex);
    lastSwitch = millis();
  }
}
