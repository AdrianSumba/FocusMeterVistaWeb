#include <LiquidCrystal.h>

const int ledVerde1 = A1;
const int ledVerde2 = A3;
const int ledVerde3 = A4;
const int ledVerde4 = A5;

const int ledAmarillo1 = A0;
const int ledAmarillo2 = 6;
const int ledAmarillo3 = 7;

const int ledRojo1 = 8;
const int ledRojo2 = 9;
const int ledRojo3 = 10;
const int ledRojo4 = 13;

const int alertaSonora = A2;

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

const int ATENCION_BAJA  = 0;
const int ATENCION_MEDIA = 1;
const int ATENCION_ALTA  = 2;

int nivelAtencionAnterior = -1;

unsigned long ultimoDatoMillis = 0;
const unsigned long TIMEOUT_MS = 5000;
bool datoValido = false;

// ================= FUNCIONES =================

void setLuzVerde(int estado){
  digitalWrite(ledVerde1, estado);
  digitalWrite(ledVerde2, estado);
  digitalWrite(ledVerde3, estado);
  digitalWrite(ledVerde4, estado);
}

void setLuzAmarilla(int estado){
  digitalWrite(ledAmarillo1, estado);
  digitalWrite(ledAmarillo2, estado);
  digitalWrite(ledAmarillo3, estado);
}

void setLuzRoja(int estado){
  digitalWrite(ledRojo1, estado);
  digitalWrite(ledRojo2, estado);
  digitalWrite(ledRojo3, estado);
  digitalWrite(ledRojo4, estado);
}

void apagarLeds() {
  setLuzVerde(0);
  setLuzAmarilla(0);
  setLuzRoja(0);
}

// ================= SETUP =================

void setup() {
  pinMode(ledVerde1, OUTPUT);
  pinMode(ledVerde2, OUTPUT);
  pinMode(ledVerde3, OUTPUT);
  pinMode(ledVerde4, OUTPUT);

  pinMode(ledAmarillo1, OUTPUT);
  pinMode(ledAmarillo2, OUTPUT);
  pinMode(ledAmarillo3, OUTPUT);

  pinMode(ledRojo1, OUTPUT);
  pinMode(ledRojo2, OUTPUT);
  pinMode(ledRojo3, OUTPUT);
  pinMode(ledRojo4, OUTPUT);

  pinMode(alertaSonora, OUTPUT);

  lcd.begin(16, 2);
  Serial.begin(115200);

  lcd.clear()
  lcd.setCursor(0, 0);
  lcd.print("FOCUS METER: ");
  lcd.setCursor(0, 1);
  lcd.print("Sin datos...");

  setLuzVerde(1);
  setLuzAmarilla(1);
  setLuzRoja(1);

  delay(5000);

  apagarLeds();
}

// ================= LOOP =================

void loop() {
  unsigned long ahora = millis();

  if (Serial.available()) {
    String dato = Serial.readStringUntil('\n');
    dato.trim();

    if (dato.startsWith("<") && dato.endsWith(">")) {
      dato = dato.substring(1, dato.length() - 1);
      float valor = dato.toFloat();

      if (valor >= 0.0 && valor <= 100.0) {
        ultimoDatoMillis = ahora;
        datoValido = true;

        int nivelAtencionActual;

        if (valor >= 80.0) {
          setLuzVerde(1);
          setLuzAmarilla(0);
          setLuzRoja(0);
          nivelAtencionActual = ATENCION_ALTA;

        } else if (valor >= 70.0) {
          setLuzVerde(0);
          setLuzAmarilla(1);
          setLuzRoja(0);
          nivelAtencionActual = ATENCION_MEDIA;

        } else {
          setLuzVerde(0);
          setLuzAmarilla(0);
          setLuzRoja(1);
          nivelAtencionActual = ATENCION_BAJA;
        }

        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Estimacion de");
        lcd.setCursor(0, 1);
        lcd.print("atencion: ");
        lcd.print(valor, 2);
        lcd.print("%");

        if (nivelAtencionActual != nivelAtencionAnterior) {
          tone(alertaSonora, 2000, 200);
          nivelAtencionAnterior = nivelAtencionActual;
        }
      }
    }
  }

  if (datoValido && (ahora - ultimoDatoMillis > TIMEOUT_MS)) {
    apagarLeds();
    lcd.clear()
    lcd.setCursor(0, 0);
    lcd.print("FOCUS METER: ");
    lcd.setCursor(0, 1);
    lcd.print("Sin datos...");
    datoValido = false;
    nivelAtencionAnterior = -1;
  }
}