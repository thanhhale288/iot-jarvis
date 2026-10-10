#include <Arduino.h>
#include <TFT_eSPI.h>
#include "animation_controller.h"
#include "Grobot_Animations.h"
#include "Moods.h"

// Single authoritative TFT & Sprite instance for the entire firmware
static TFT_eSPI tft = TFT_eSPI();
static TFT_eSprite sprite = TFT_eSprite(&tft);

// Grobot eyes instance (Default eyeColor: Light Green/Cyan, bgColor: Black)
static GrobotEyes eyes(0x07E0, TFT_BLACK);

static bool animationInitialized = false;
static unsigned long lastRenderTime = 0;
static const unsigned long FRAME_INTERVAL_MS = 25; // ~40 FPS target (non-blocking)

void initAnimation()
{
    Serial.println("Initializing TFT animation (Grobot_animation)...");

    tft.init();
    tft.setRotation(1);
    tft.fillScreen(TFT_BLACK);

    // 8-bit color depth to conserve RAM while maintaining smooth animations
    sprite.setColorDepth(8);
    if (sprite.createSprite(240, 120) == nullptr)
    {
        // Fallback for smaller canvas if heap is tight
        sprite.createSprite(160, 90);
    }

    eyes.setEmotion(MOOD_NEUTRAL);
    animationInitialized = true;
    Serial.println("TFT animation system initialized.");
}

void setAnimation(const char* name)
{
    if (name == nullptr || !animationInitialized)
    {
        return;
    }

    Serial.print("Set animation: ");
    Serial.println(name);

    if (strcmp(name, "idle") == 0)
    {
        eyes.setEmotion(MOOD_NEUTRAL);
        eyes.lookAt(0, 0);
    }
    else if (strcmp(name, "listening") == 0)
    {
        eyes.setEmotion(MOOD_QUESTIONING);
        eyes.lookAt(8, -6);
    }
    else if (strcmp(name, "thinking") == 0)
    {
        eyes.setEmotion(MOOD_THINKING);
        eyes.lookAt(-10, -10);
    }
    else if (strcmp(name, "speaking") == 0)
    {
        eyes.setEmotion(MOOD_EXCITED);
        eyes.lookAt(0, 0);
    }
    else if (strcmp(name, "happy") == 0)
    {
        eyes.setEmotion(MOOD_HAPPY);
        eyes.lookAt(0, 0);
    }
    else if (strcmp(name, "alert") == 0)
    {
        eyes.setEmotion(MOOD_ALERT);
        eyes.lookAt(0, 0);
    }
    else
    {
        Serial.print("Unknown animation name: ");
        Serial.println(name);
    }
}

void updateAnimation()
{
    if (!animationInitialized)
    {
        return;
    }

    unsigned long now = millis();
    if (now - lastRenderTime >= FRAME_INTERVAL_MS)
    {
        lastRenderTime = now;
        eyes.renderEmotions(sprite);
    }
}
