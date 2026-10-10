#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>

void initWebSocket();
void webSocketLoop();

constexpr uint8_t NO_ACTIVE_CLIENT = 0xFF;

uint8_t getActiveClient();
void sendJson(uint8_t clientNum, JsonDocument &doc);