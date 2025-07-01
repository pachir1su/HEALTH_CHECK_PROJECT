#define PULSE_PIN  A0
#define TEMP_PIN   5

void setup() {
  Serial.begin(9600);
}

void loop() {
  // 심박수 (A0)
  int pulseValue = analogRead(PULSE_PIN);
  int bpm = map(pulseValue, 0, 1023, 60, 120);

  // 온도
  int raw = analogRead(TEMP_PIN);
  float voltage = raw * (5.0 / 1023.0);
  float tempC = voltage * 18.0; // 임의로 맞춤

  // 시리얼
  Serial.print("BPM:"); Serial.println(bpm);
  Serial.print("TEMP:"); Serial.println(tempC, 2);

  delay(1000);
}
