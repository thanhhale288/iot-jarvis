#include <Arduino.h>

#include "ultrasonic.h"

// Điền GPIO TRIG vào đây
const uint8_t ULTRASONIC_TRIG_PIN = 4;
// Điền GPIO ECHO vào đây
const uint8_t ULTRASONIC_ECHO_PIN = 5;
// Điền ngưỡng khoảng cách vào đây
const float PROXIMITY_THRESHOLD_CM = 15;

static const unsigned long ECHO_TIMEOUT_US = 30000UL;
static bool ultrasonicInitialized = false;
static bool proximityActive = false;

void initUltrasonic()
{
	if (
		ULTRASONIC_TRIG_PIN == 0xFF ||
		ULTRASONIC_ECHO_PIN == 0xFF ||
		ULTRASONIC_TRIG_PIN == ULTRASONIC_ECHO_PIN
	)
	{
		Serial.println("Ultrasonic disabled: configure distinct TRIG/ECHO GPIOs");
		return;
	}

	pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
	pinMode(ULTRASONIC_ECHO_PIN, INPUT);
	digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
	ultrasonicInitialized = true;
}

float readDistanceCm()
{
	if (!ultrasonicInitialized)
	{
		return -1.0f;
	}

	digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
	delayMicroseconds(2);
	digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
	delayMicroseconds(10);
	digitalWrite(ULTRASONIC_TRIG_PIN, LOW);

	const unsigned long echoDurationUs = pulseIn(
		ULTRASONIC_ECHO_PIN,
		HIGH,
		ECHO_TIMEOUT_US
	);

	if (echoDurationUs == 0)
	{
		return -1.0f;
	}

	return (static_cast<float>(echoDurationUs) * 0.0343f) / 2.0f;
}

bool checkProximityEvent()
{
	if (PROXIMITY_THRESHOLD_CM <= 0.0f)
	{
		return false;
	}

	const float distanceCm = readDistanceCm();
	if (distanceCm < 0.0f)
	{
		return false;
	}

	if (distanceCm <= PROXIMITY_THRESHOLD_CM)
	{
		if (!proximityActive)
		{
			proximityActive = true;
			return true;
		}

		return false;
	}

	proximityActive = false;
	return false;
}
