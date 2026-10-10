#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsServer.h>
#include <ArduinoJson.h>

#include "secrets.h"

// =========================
// WebSocket
// =========================
WebSocketsServer webSocket = WebSocketsServer(81);

// =========================
// Helpers
// =========================

void sendJson(uint8_t clientNum, JsonDocument &doc)
{
    String output;
    serializeJson(doc, output);

    // Protocol: tối đa 256 byte / message
    if (output.length() > 256)
    {
        Serial.println("ERROR: JSON exceeds 256 bytes");
        return;
    }

    webSocket.sendTXT(clientNum, output);

    Serial.print("ESP32 -> ");
    Serial.println(output);
}

bool isValidLedState(const char *state)
{
    if (state == nullptr)
        return false;

    return
        strcmp(state, "idle") == 0 ||
        strcmp(state, "listening") == 0 ||
        strcmp(state, "thinking") == 0 ||
        strcmp(state, "speaking") == 0 ||
        strcmp(state, "happy") == 0 ||
        strcmp(state, "alert") == 0;
}

bool isValidMotionName(const char *name)
{
    if (name == nullptr)
        return false;

    return
        strcmp(name, "idle") == 0 ||
        strcmp(name, "nod") == 0 ||
        strcmp(name, "shake") == 0 ||
        strcmp(name, "think") == 0 ||
        strcmp(name, "happy") == 0 ||
        strcmp(name, "alert") == 0 ||
        strcmp(name, "turn_left") == 0 ||
        strcmp(name, "turn_right") == 0 ||
        strcmp(name, "step_forward") == 0;
}

// =========================
// Process JSON command
// =========================

void handleJsonCommand(uint8_t clientNum, const char *payload, size_t length)
{
    // Protocol giới hạn 256 byte
    if (length > 256)
    {
        JsonDocument errorDoc;

        errorDoc["v"] = 1;
        errorDoc["from"] = "esp32";
        errorDoc["ok"] = false;
        errorDoc["error"] = "bad_args";

        sendJson(clientNum, errorDoc);
        return;
    }

    Serial.print("ESP32 <- ");
    Serial.println(payload);

    // Parse JSON
    JsonDocument doc;

    DeserializationError error =
        deserializeJson(doc, payload, length);

    if (error)
    {
        Serial.println("Invalid JSON");

        JsonDocument response;

        response["v"] = 1;
        response["from"] = "esp32";
        response["ok"] = false;
        response["error"] = "bad_args";

        sendJson(clientNum, response);
        return;
    }

    // =========================
    // Read common fields
    // =========================

    const char *id = doc["id"];
    const char *cmd = doc["cmd"];

    // cmd bắt buộc
    if (cmd == nullptr)
    {
        JsonDocument response;

        response["v"] = 1;

        if (id != nullptr)
            response["id"] = id;

        response["from"] = "esp32";
        response["ok"] = false;
        response["error"] = "bad_args";

        sendJson(clientNum, response);
        return;
    }

    // =========================
    // PING
    // =========================

    if (strcmp(cmd, "ping") == 0)
    {
        JsonDocument response;

        response["v"] = 1;

        if (id != nullptr)
            response["id"] = id;

        response["from"] = "esp32";
        response["ok"] = true;

        sendJson(clientNum, response);
        return;
    }

    // =========================
    // LED
    // =========================

    if (strcmp(cmd, "led") == 0)
    {
        const char *state = doc["state"];

        if (!isValidLedState(state))
        {
            JsonDocument response;

            response["v"] = 1;

            if (id != nullptr)
                response["id"] = id;

            response["from"] = "esp32";
            response["ok"] = false;
            response["error"] = "bad_args";

            sendJson(clientNum, response);
            return;
        }

        // Tuần 1: hiện tại chỉ ACK.
        // Sau này có thể gọi NeoPixel ở đây.
        Serial.print("LED state = ");
        Serial.println(state);

        JsonDocument response;

        response["v"] = 1;

        if (id != nullptr)
            response["id"] = id;

        response["from"] = "esp32";
        response["ok"] = true;
        response["state"] = state;

        sendJson(clientNum, response);
        return;
    }

    // =========================
    // MOTION
    // =========================

    if (strcmp(cmd, "motion") == 0)
    {
        const char *name = doc["name"];

        if (!isValidMotionName(name))
        {
            JsonDocument response;

            response["v"] = 1;

            if (id != nullptr)
                response["id"] = id;

            response["from"] = "esp32";
            response["ok"] = false;
            response["error"] = "bad_args";

            sendJson(clientNum, response);
            return;
        }

        // Tuần 1: chỉ log + ACK.
        // Servo thật sẽ tích hợp sau.
        Serial.print("Motion = ");
        Serial.println(name);

        JsonDocument response;

        response["v"] = 1;

        if (id != nullptr)
            response["id"] = id;

        response["from"] = "esp32";
        response["ok"] = true;
        response["name"] = name;

        sendJson(clientNum, response);
        return;
    }

    // =========================
    // UNKNOWN COMMAND
    // =========================

    JsonDocument response;

    response["v"] = 1;

    if (id != nullptr)
        response["id"] = id;

    response["from"] = "esp32";
    response["ok"] = false;
    response["error"] = "unknown_cmd";

    sendJson(clientNum, response);
}

// =========================
// WebSocket event
// =========================

void webSocketEvent(
    uint8_t clientNum,
    WStype_t type,
    uint8_t *payload,
    size_t length)
{
    switch (type)
    {
    case WStype_CONNECTED:
    {
        IPAddress clientIP = webSocket.remoteIP(clientNum);

        Serial.print("WebSocket client connected: ");
        Serial.println(clientIP);

        break;
    }

    case WStype_DISCONNECTED:
    {
        Serial.println("WebSocket client disconnected");
        break;
    }

    case WStype_TEXT:
    {
        // Chỉ xử lý text frame
        handleJsonCommand(
            clientNum,
            reinterpret_cast<const char *>(payload),
            length
        );

        break;
    }

    default:
        // Bỏ qua binary/ping/pong...
        break;
    }
}

// =========================
// Setup
// =========================

void setup()
{
    Serial.begin(115200);
    delay(1000);

    const unsigned long wifiTimeoutMs = 30000;
    const unsigned long wifiStartMs = millis();

    Serial.println();
    Serial.println("=== JARVIS ESP32 ===");

    // -------------------------
    // Wi-Fi
    // -------------------------

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    Serial.print("Connecting to Wi-Fi");

    while (WiFi.status() != WL_CONNECTED && millis() - wifiStartMs < wifiTimeoutMs)
    {
        delay(500);
        Serial.print(".");
    }

    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println();
        Serial.println("Wi-Fi connection timeout");
        return;
    }

    Serial.println();
    Serial.println("Wi-Fi connected!");

    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());

    // -------------------------
    // WebSocket server
    // -------------------------

    webSocket.begin();

    webSocket.onEvent(webSocketEvent);

    Serial.println("WebSocket server started");
    Serial.println("Port: 81");
}

// =========================
// Loop
// =========================

void loop()
{
    webSocket.loop();
}