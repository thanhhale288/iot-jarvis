/*
 * Bài 17: Cảm biến nhiệt độ
 * Đấu nối: cảm biến → A0
 */

int Sensor = A0;
int Val = 0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  Val = analogRead(Sensor);
  int Force = map(Val, 0, 1023, 0, 255);
  Serial.println(Force);
  delay(500);
}
