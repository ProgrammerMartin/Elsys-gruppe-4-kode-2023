int trigPin1 = 2;
int echoPin1 = 4;
char userInput;

void setup() {
  Serial.begin(500000);
  pinMode(trigPin1, OUTPUT);
  pinMode(echoPin1, INPUT);
}

void loop() {
  long duration1, distance1;

  //Leser fra seriellporten
  if (Serial.available() > 0) {
    userInput = Serial.read();

    //Hvis det som skrives fra seriellporten er g, skal if-løkken kjøres, distansen regnes ut og returneres
    if (userInput == 'g') {
      digitalWrite(trigPin1, LOW);
      delayMicroseconds(2);
      digitalWrite(trigPin1, HIGH);
      delayMicroseconds(10);
      digitalWrite(trigPin1, LOW);
      duration1 = pulseIn(echoPin1, HIGH);
      distance1 = (duration1 / 2) / 29.1;

      if (distance1 > 2 && distance1 < 201) {
        Serial.println(distance1);
        }
      else {
        Serial.println("");
      }
    }
  }
  delay(10);
}
