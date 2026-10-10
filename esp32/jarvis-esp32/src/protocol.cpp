#include <Arduino.h>
#include <ArduinoJson.h>

#include "protocol.h"
#include "websocket_server.h"
#include "motion_controller.h"
#include "led_controller.h"
#include "animation_controller.h"

// ============================================================
// Validate LED state
// ============================================================

static bool isValidLedState(const char *state)
{
    if (state == nullptr)
    {
        return false;
    }

    return
        strcmp(state, "idle") == 0 ||
        strcmp(state, "listening") == 0 ||
        strcmp(state, "thinking") == 0 ||
        strcmp(state, "speaking") == 0 ||
        strcmp(state, "happy") == 0 ||
        strcmp(state, "alert") == 0;
}

// ============================================================
// Validate Motion name
// ============================================================

static bool isValidMotionName(const char *name)
{
    if (name == nullptr)
    {
        return false;
    }

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

// ============================================================
// Send ESP32 event to Host
//
// Ví dụ:
// {"v":1,"from":"esp32","cmd":"event","name":"clap"}
//
// hoặc:
// {"v":1,"from":"esp32","cmd":"event","name":"proximity"}
// ============================================================

void sendEsp32Event(
    uint8_t clientNum,
    const char *eventName)
{
    if (
        eventName == nullptr ||
        (strcmp(eventName, "clap") != 0 && strcmp(eventName, "proximity") != 0)
    )
    {
        return;
    }

    JsonDocument doc;

    doc["v"] = 1;
    doc["from"] = "esp32";
    doc["cmd"] = "event";
    doc["name"] = eventName;

    sendJson(clientNum, doc);
}

// ============================================================
// Process JSON command
// ============================================================

void handleJsonCommand(
    uint8_t clientNum,
    const char *payload,
    size_t length)
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

    // ========================================================
    // Parse JSON
    // ========================================================

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

    // ========================================================
    // Read common fields
    // ========================================================

    const char *id = doc["id"];
    const char *to = doc["to"];
    const char *cmd = doc["cmd"];

    // ESP32 processes only messages routed to this board by the Host.
    if (to == nullptr || strcmp(to, "esp32") != 0)
    {
        JsonDocument response;

        response["v"] = 1;

        if (id != nullptr)
        {
            response["id"] = id;
        }

        response["from"] = "esp32";
        response["ok"] = false;
        response["error"] = "bad_args";

        sendJson(clientNum, response);
        return;
    }

    // cmd bắt buộc
    if (cmd == nullptr)
    {
        JsonDocument response;

        response["v"] = 1;

        if (id != nullptr)
        {
            response["id"] = id;
        }

        response["from"] = "esp32";
        response["ok"] = false;
        response["error"] = "bad_args";

        sendJson(clientNum, response);
        return;
    }

    // ========================================================
    // PING
    // ========================================================

    if (strcmp(cmd, "ping") == 0)
    {
        JsonDocument response;

        response["v"] = 1;

        if (id != nullptr)
        {
            response["id"] = id;
        }

        response["from"] = "esp32";
        response["ok"] = true;

        sendJson(clientNum, response);
        return;
    }

    // ========================================================
    // LED
    // ========================================================

    if (strcmp(cmd, "led") == 0)
    {
        const char *state = doc["state"];

        if (!isValidLedState(state))
        {
            JsonDocument response;

            response["v"] = 1;

            if (id != nullptr)
            {
                response["id"] = id;
            }

            response["from"] = "esp32";
            response["ok"] = false;
            response["error"] = "bad_args";

            sendJson(clientNum, response);
            return;
        }

        setLEDState(state);
        setAnimation(state);

        JsonDocument response;

        response["v"] = 1;

        if (id != nullptr)
        {
            response["id"] = id;
        }

        response["from"] = "esp32";
        response["ok"] = true;
        response["state"] = state;

        sendJson(clientNum, response);
        return;
    }

    // ========================================================
    // MOTION
    // ========================================================

    if (strcmp(cmd, "motion") == 0)
    {
        const char *name = doc["name"];

        if (!isValidMotionName(name))
        {
            JsonDocument response;

            response["v"] = 1;

            if (id != nullptr)
            {
                response["id"] = id;
            }

            response["from"] = "esp32";
            response["ok"] = false;
            response["error"] = "bad_args";

            sendJson(clientNum, response);
            return;
        }

        runMotion(name);

        JsonDocument response;

        response["v"] = 1;

        if (id != nullptr)
        {
            response["id"] = id;
        }

        response["from"] = "esp32";
        response["ok"] = true;
        response["name"] = name;

        sendJson(clientNum, response);
        return;
    }

    // ========================================================
    // UNKNOWN COMMAND
    // ========================================================

    JsonDocument response;

    response["v"] = 1;

    if (id != nullptr)
    {
        response["id"] = id;
    }

    response["from"] = "esp32";
    response["ok"] = false;
    response["error"] = "unknown_cmd";

    sendJson(clientNum, response);
}