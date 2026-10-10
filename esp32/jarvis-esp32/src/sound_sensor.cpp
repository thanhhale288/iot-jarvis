#include <Arduino.h>

#include "sound_sensor.h"

// Điền GPIO sound sensor vào đây
const uint8_t SOUND_SENSOR_PIN = 34;

static volatile bool clapDetected = false;
static bool soundSensorInitialized = false;

static void soundSensorISR()
{
	clapDetected = true;
}

void initSoundSensor()
{
	if (SOUND_SENSOR_PIN == 0xFF)
	{
		Serial.println("Sound sensor disabled: configure its GPIO");
		return;
	}

	pinMode(SOUND_SENSOR_PIN, INPUT);
	attachInterrupt(
		digitalPinToInterrupt(SOUND_SENSOR_PIN),
		soundSensorISR,
		RISING
	);
	soundSensorInitialized = true;
}

bool consumeClapEvent()
{
	if (!soundSensorInitialized)
	{
		return false;
	}

	noInterrupts();
	const bool detected = clapDetected;
	clapDetected = false;
	interrupts();

	return detected;
}
