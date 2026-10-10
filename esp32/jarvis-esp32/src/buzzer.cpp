#include <Arduino.h>

#include "buzzer.h"

// Điền GPIO buzzer vào đây
const uint8_t BUZZER_PIN = 0xFF;

static bool buzzerInitialized = false;

void initBuzzer()
{
	if (BUZZER_PIN == 0xFF)
	{
		Serial.println("Buzzer disabled: configure its GPIO");
		return;
	}

	pinMode(BUZZER_PIN, OUTPUT);
	digitalWrite(BUZZER_PIN, LOW);
	buzzerInitialized = true;
}

void beep(unsigned long durationMs)
{
	if (!buzzerInitialized || durationMs == 0)
	{
		return;
	}

	tone(BUZZER_PIN, 1000, durationMs);
}
