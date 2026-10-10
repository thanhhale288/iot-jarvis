#include <Arduino.h>
#include "motion_controller.h"
#include "Otto.h"
#include "Otto_gestures.h"

// ============================================================
// Hardware Servo Pin Configuration (Configuration 1: Standard Otto DIY)
// 4 physical servos: 2 Legs (YL, YR) + 2 Feet (RL, RR)
//
// Default example assignments on ESP32:
//   SERVO_PIN_YL: GPIO 13 (Servo 0 - Đùi trái / Left Leg)
//   SERVO_PIN_YR: GPIO 14 (Servo 1 - Đùi phải / Right Leg)
//   SERVO_PIN_RL: GPIO 27 (Servo 2 - Bàn chân trái / Left Foot)
//   SERVO_PIN_RR: GPIO 26 (Servo 3 - Bàn chân phải / Right Foot)
//
// Set to 0xFF if hardware is not yet connected.
// ============================================================
#ifndef SERVO_PIN_YL
#define SERVO_PIN_YL 16
#endif

#ifndef SERVO_PIN_YR
#define SERVO_PIN_YR 13
#endif

#ifndef SERVO_PIN_RL
#define SERVO_PIN_RL 15
#endif

#ifndef SERVO_PIN_RR
#define SERVO_PIN_RR 14
#endif

// Aliases for 1..4 naming
#define SERVO_PIN_1 SERVO_PIN_YL
#define SERVO_PIN_2 SERVO_PIN_YR
#define SERVO_PIN_3 SERVO_PIN_RL
#define SERVO_PIN_4 SERVO_PIN_RR

static Otto ottoHal;
static bool motionInitialized = false;

void initMotion()
{
    Serial.println("Motion system initializing (4-servo standard Otto HAL)...");

    if (SERVO_PIN_YL != 0xFF && SERVO_PIN_YR != 0xFF &&
        SERVO_PIN_RL != 0xFF && SERVO_PIN_RR != 0xFF)
    {
        ottoHal.init(SERVO_PIN_YL, SERVO_PIN_YR, SERVO_PIN_RL, SERVO_PIN_RR, false);
        ottoHal.home();
        motionInitialized = true;
        Serial.printf("Motion system initialized on GPIOs (YL:%d, YR:%d, RL:%d, RR:%d)\n",
                      SERVO_PIN_YL, SERVO_PIN_YR, SERVO_PIN_RL, SERVO_PIN_RR);
    }
    else
    {
        Serial.println("Motion system disabled: Configure SERVO_PIN_YL, YR, RL, RR");
    }
}

void executeMotion(const char* name)
{
    runMotion(name);
}

void runMotion(const char* name)
{
    if (name == nullptr)
    {
        return;
    }

    Serial.print("Run motion: ");
    Serial.println(name);

    if (!motionInitialized)
    {
        Serial.println("Motion ignored: servos not initialized");
        return;
    }

    if (strcmp(name, "idle") == 0)
    {
        ottoHal.home();
    }
    else if (strcmp(name, "nod") == 0)
    {
        ottoHal.nod(2, 600);
    }
    else if (strcmp(name, "shake") == 0)
    {
        ottoHal.shake(2, 600);
    }
    else if (strcmp(name, "think") == 0)
    {
        ottoHal.playGesture(OttoConfused);
    }
    else if (strcmp(name, "happy") == 0)
    {
        ottoHal.playGesture(OttoHappy);
    }
    else if (strcmp(name, "alert") == 0)
    {
        ottoHal.playGesture(OttoAngry);
    }
    else if (strcmp(name, "turn_left") == 0)
    {
        ottoHal.turn(2, 1000, LEFT);
    }
    else if (strcmp(name, "turn_right") == 0)
    {
        ottoHal.turn(2, 1000, RIGHT);
    }
    else if (strcmp(name, "step_forward") == 0)
    {
        ottoHal.walk(2, 1000, FORWARD);
    }
    else
    {
        Serial.print("Unknown motion name: ");
        Serial.println(name);
    }
}