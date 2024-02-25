int red = 2;
int yellow = 3;
int green = 4;
char s;


void setup() {
  // put your setup code here, to run once:
  pinMode(red, OUTPUT);
  Serial.begin(9600);
  // while (!Serial) {}
}

void loop() {
  // put your main code here, to run repeatedly
  while (!Serial.available());
  s = Serial.read();
  
  if (s == '1') { // ???????????? single quote is IMPORTANT!!!!!!!!!!!!!!!!!
    digitalWrite(red, HIGH);
  } else {
    digitalWrite(red, LOW);
  }
}
