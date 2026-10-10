#include <Arduino.h>
#include "led_controller.h"

void initLED()
{
    Serial.println("LED initialized");
}

void setLEDState(const char* state)
{
    Serial.print("Set LED state: ");
    Serial.println(state);
}