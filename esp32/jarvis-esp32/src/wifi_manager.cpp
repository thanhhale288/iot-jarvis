#include <Arduino.h>
#include <WiFi.h>

#include "wifi_manager.h"
#include "secrets.h"

bool initWiFi()
{
    const unsigned long wifiTimeoutMs = 30000;
    const unsigned long wifiStartMs = millis();

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    Serial.print("Connecting to Wi-Fi");

    while (
        WiFi.status() != WL_CONNECTED &&
        millis() - wifiStartMs < wifiTimeoutMs
    )
    {
        delay(500);
        Serial.print(".");
    }

    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println();
        Serial.println("Wi-Fi connection timeout");
        return false;
    }

    Serial.println();
    Serial.println("Wi-Fi connected!");

    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());

    return true;
}