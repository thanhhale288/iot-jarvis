#include <Arduino.h>
#include "wifi_manager.h"
#include "websocket_server.h"
#include "protocol.h"
#include "led_controller.h"
#include "animation_controller.h"
#include "motion_controller.h"
#include "buzzer.h"
#include "sound_sensor.h"
#include "ultrasonic.h"

// Edge-TTS chạy trên laptop bằng Python trong voice/, không chạy trên ESP32.

void setup()
{
    Serial.begin(115200);

    initWiFi();
    initLED();
    initAnimation();
    initMotion();
    initBuzzer();
    initSoundSensor();
    initUltrasonic();
    initWebSocket();
}

void loop()
{
    webSocketLoop();
    updateAnimation();

    if (consumeClapEvent())
    {
        const uint8_t clientNum = getActiveClient();
        if (clientNum != NO_ACTIVE_CLIENT)
        {
            sendEsp32Event(clientNum, "clap");
        }
        beep(100);
    }

    if (checkProximityEvent())
    {
        const uint8_t clientNum = getActiveClient();
        if (clientNum != NO_ACTIVE_CLIENT)
        {
            sendEsp32Event(clientNum, "proximity");
        }
    }
}