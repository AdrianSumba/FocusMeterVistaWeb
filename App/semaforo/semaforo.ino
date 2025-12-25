const int ledRojo = A5;
const int ledAmarillo = A4;
const int ledVerde = A3;

const int alertaSonora = A2;

#include <LiquidCrystal.h>
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

const int ATENCION_BAJA  = 0;
const int ATENCION_MEDIA = 1;
const int ATENCION_ALTA  = 2;

int nivelAtencionAnterior = -1;


void setup()
{
  pinMode(ledRojo, OUTPUT);
  pinMode(ledAmarillo, OUTPUT);
  pinMode(ledVerde, OUTPUT);
  
  pinMode(alertaSonora, OUTPUT);
  
  lcd.begin(16, 2);
  randomSeed(analogRead(A0));
}


void loop()
{
  float estimacion_atencion = random(0, 10000) / 100.0;
  
  int nivelAtencionActual;
  
  if (estimacion_atencion >= 80.0) {
    digitalWrite(ledVerde, HIGH);
    digitalWrite(ledAmarillo, LOW);
    digitalWrite(ledRojo, LOW);
    nivelAtencionActual = ATENCION_ALTA;
  } else if (estimacion_atencion >= 70.0) {
    digitalWrite(ledVerde, LOW);
    digitalWrite(ledAmarillo, HIGH);
    digitalWrite(ledRojo, LOW);
    nivelAtencionActual = ATENCION_MEDIA;
  } else {
    digitalWrite(ledVerde, LOW);
    digitalWrite(ledAmarillo, LOW);
    digitalWrite(ledRojo, HIGH);
    nivelAtencionActual = ATENCION_BAJA;
  }

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Estimacion de");
  lcd.setCursor(0, 1);
  lcd.print("atencion: ");
  lcd.print(estimacion_atencion, 2);
  lcd.print("%");

  if (nivelAtencionActual != nivelAtencionAnterior ) {
    tone(alertaSonora, 2000);
    delay(300);
    noTone(alertaSonora);
    delay(2000);
    nivelAtencionAnterior = nivelAtencionActual;
  } else {
    delay(2000);
  }
  
}
