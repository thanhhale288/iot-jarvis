/*
 * Idle ESP32 — detatch moi PWM, dung servo.
 */
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("esp_idle: no PWM");
}

void loop() {
  delay(1000);
}
