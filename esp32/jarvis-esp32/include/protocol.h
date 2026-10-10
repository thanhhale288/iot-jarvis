#pragma once

#include <Arduino.h>

void sendEsp32Event(uint8_t clientNum, const char* eventName);

void handleJsonCommand(
    uint8_t clientNum,
    const char* payload,
    size_t length
);