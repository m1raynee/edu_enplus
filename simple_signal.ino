

int led = 2;
int signal;

void setup() {
  // put your setup code here, to run once:
  pinMode(2, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0) {
    signal = Serial.read();
  }
  if (signal == '1') digitalWrite(2, HIGH);
  else digitalWrite(2, LOW);

}
