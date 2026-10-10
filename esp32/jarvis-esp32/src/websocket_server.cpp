#include <Arduino.h>
#include <WebSocketsServer.h>

#include "websocket_server.h"
#include "protocol.h"

// Điền WebSocket port vào đây
static const uint16_t WEBSOCKET_PORT = 0;

static WebSocketsServer webSocket(WEBSOCKET_PORT);
static uint8_t activeClient = NO_ACTIVE_CLIENT;
static bool webSocketStarted = false;

void webSocketEvent(
    uint8_t clientNum,
    WStype_t type,
    uint8_t *payload,
    size_t length
)
{
    switch (type)
    {
    case WStype_CONNECTED:
    {
        IPAddress clientIP = webSocket.remoteIP(clientNum);
        activeClient = clientNum;

        Serial.print("WebSocket client connected: ");
        Serial.println(clientIP);

        break;
    }

    case WStype_DISCONNECTED:
        Serial.println("WebSocket client disconnected");
        if (activeClient == clientNum)
        {
            activeClient = NO_ACTIVE_CLIENT;
        }
        break;

    case WStype_TEXT:
        handleJsonCommand(
            clientNum,
            reinterpret_cast<const char*>(payload),
            length
        );
        break;

    default:
        break;
    }
}

void initWebSocket()
{
    if (WEBSOCKET_PORT == 0)
    {
        Serial.println("WebSocket disabled: configure its port");
        return;
    }

    webSocket.begin();
    webSocket.onEvent(webSocketEvent);
    webSocketStarted = true;

    Serial.println("WebSocket server started");
    Serial.print("Port: ");
    Serial.println(WEBSOCKET_PORT);
}

void webSocketLoop()
{
    if (webSocketStarted)
    {
        webSocket.loop();
    }
}

uint8_t getActiveClient()
{
    return activeClient;
}

void sendJson(uint8_t clientNum, JsonDocument &doc)
{
    if (!webSocketStarted || clientNum == NO_ACTIVE_CLIENT)
    {
        return;
    }

    const size_t jsonLength = measureJson(doc);
    if (jsonLength > 256)
    {
        Serial.println("WebSocket JSON exceeds 256-byte limit");
        return;
    }

    char jsonBuffer[257];
    const size_t bytesWritten = serializeJson(doc, jsonBuffer, sizeof(jsonBuffer));
    if (bytesWritten != jsonLength)
    {
        Serial.println("WebSocket JSON serialization failed");
        return;
    }

    jsonBuffer[bytesWritten] = '\0';
    webSocket.sendTXT(clientNum, jsonBuffer, bytesWritten);
}