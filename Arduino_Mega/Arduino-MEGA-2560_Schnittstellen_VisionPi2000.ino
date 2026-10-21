// =====================================================================
// VisionPi2000 (Schnittstellen) V6 - ARDUINO KONTROLL-SOFTWARE
// Inkl. Matrix, Taster, Piezo, IR, Relais und MAX7219 Löwen-Display
// =====================================================================

#include "LedControl.h"

// --- 1. PIN-DEFINITIONEN ---
const int rowPins[4]  = {22, 24, 26, 28};
const int colPins[16] = {30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45};

const int btnRed      = 46;
const int btnBlue     = 47;
const int btnGrey     = 48;
const int btnPlayer   = 49;
const int btnCoin     = 50;

const int piezoPin    = A0; // Piezo für Miss-Erkennung / Treffer
const int irSensorPin = 2;  // E18-D80NK Infrarot-Sensor (Spielererkennung)
const int relayPin    = 52; // Relais (z.B. für Spinnenbeleuchtung oder Münzperle)

// --- 2. MAX7219 DISPLAY KONFIGURATION ---
// Parameter: DIN-Pin, CLK-Pin, LOAD/CS-Pin, Anzahl der MAX7219 Module
// Passe die Pins (4, 5, 6) bei Bedarf an deine Verkabelung an!
LedControl lc = LedControl(4, 5, 6, 4); 

// --- 3. VARIABLEN FÜR ENTPRELLUNG & TIMING ---
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50; 

void setup() {
  // Serielle Schnittstelle zum Raspberry Pi starten
  Serial.begin(115200);

  // Matrix Zeilen als Ausgänge definieren
  for (int i = 0; i < 4; i++) {
    pinMode(rowPins[i], OUTPUT);
    digitalWrite(rowPins[i], HIGH); // Standardmäßig HIGH (Invers-Logik je nach Matrix)
  }

  // Matrix Spalten als Eingänge mit Pullup
  for (int j = 0; j < 16; j++) {
    pinMode(colPins[j], INPUT_PULLUP);
  }

  // Taster und Sensoren konfigurieren
  pinMode(btnRed, INPUT_PULLUP);
  pinMode(btnBlue, INPUT_PULLUP);
  pinMode(btnGrey, INPUT_PULLUP);
  pinMode(btnPlayer, INPUT_PULLUP);
  pinMode(btnCoin, INPUT_PULLUP);
  
  pinMode(irSensorPin, INPUT_PULLUP);
  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, LOW);

  // MAX7219 Display initialisieren
  int devices = lc.getDeviceCount();
  for (int i = 0; i < devices; i++) {
    lc.shutdown(i, false);      // Energiesparmodus aus
    lc.setIntensity(i, 8);      // Helligkeit einstellen (0-15)
    lc.clearDisplay(i);         // Display leeren
  }
}

void loop() {
  // 1. Matrix scannen (Treffererkennung)
  scanMatrix();

  // 2. Taster abfragen
  checkButtons();

  // 3. IR-Sensor abfragen (Spieler tritt an die Scheibe)
  checkInfrared();

  // 4. Piezo abfragen (Miss / Anschlag an die Spinne)
  checkPiezo();

  // Kleine Pause zur Entlastung des Mikrocontrollers
  delay(10);
}

void scanMatrix() {
  for (int row = 0; row < 4; row++) {
    digitalWrite(rowPins[row], LOW); // Aktive Zeile auf LOW ziehen

    for (int col = 0; col < 16; col++) {
      if (digitalRead(colPins[col]) == LOW) {
        // Debounce / Kurze Beruhigung der Leitung
        delay(20); 
        if (digitalRead(colPins[col]) == LOW) {
          // Treffer an Raspberry Pi übergeben (Format: T:Zeile:Spalte)
          Serial.print("HIT:");
          Serial.print(row);
          Serial.print(":");
          Serial.println(col);

          // Warten bis der Pfeil wieder gelöst wird (Doppeltreff-Schutz)
          while (digitalRead(colPins[col]) == LOW) {
            delay(10);
          }
        }
      }
    }
    digitalWrite(rowPins[row], HIGH); // Zeile wieder abschalten
  }
}

void checkButtons() {
  if (digitalRead(btnRed) == LOW) {
    Serial.println("BTN:RED");
    delay(200); // Einfache Entprellung
  }
  if (digitalRead(btnBlue) == LOW) {
    Serial.println("BTN:BLUE");
    delay(200);
  }
  if (digitalRead(btnGrey) == LOW) {
    Serial.println("BTN:GREY");
    delay(200);
  }
  if (digitalRead(btnPlayer) == LOW) {
    Serial.println("BTN:PLAYER");
    delay(200);
  }
  if (digitalRead(btnCoin) == LOW) {
    Serial.println("COIN:IN");
    delay(200);
  }
}

void checkInfrared() {
  // Wenn der E18-D80NK ein Objekt (Spieler) erkennt
  if (digitalRead(irSensorPin) == LOW) {
    Serial.println("IR:DETECT");
    delay(1000); // Sperrzeit, damit das Signal nicht im Sekundentakt feuert
  }
}

void checkPiezo() {
  int piezoValue = analogRead(piezoPin);
  // Schwellenwert für einen "Miss"-Treffer oder Aufschlag an die Außenwand
  if (piezoValue > 300) { 
    Serial.print("MISS:");
    Serial.println(piezoValue);
    delay(200);
  }
}
