const int clkPin  = 4;   // ST1 Pin 20
const int loadPin = 5;   // ST1 Pin 18

// Unsere 5 parallelen Datenstränge
const int dataPins[5] = {6, 7, 8, 9, 10}; 

void sendCommandAll(byte reg, byte data) {
  digitalWrite(loadPin, LOW);
  delayMicroseconds(5); // Dem Load-Signal Zeit geben
  
  for(int chip = 0; chip < 2; chip++) {
    
    // 1. Register-Byte senden
    for (int i = 7; i >= 0; i--) {
      int bitVal = (reg >> i) & 1;
      for(int d = 0; d < 5; d++) {
        digitalWrite(dataPins[d], bitVal);
      }
      delayMicroseconds(2); // Daten anliegen lassen
      digitalWrite(clkPin, HIGH);
      delayMicroseconds(2); // Takt halten
      digitalWrite(clkPin, LOW);
      delayMicroseconds(2); // Signal abklingen lassen
    }
    
    // 2. Daten-Byte senden
    for (int i = 7; i >= 0; i--) {
      int bitVal = (data >> i) & 1;
      for(int d = 0; d < 5; d++) {
        digitalWrite(dataPins[d], bitVal);
      }
      delayMicroseconds(2);
      digitalWrite(clkPin, HIGH);
      delayMicroseconds(2);
      digitalWrite(clkPin, LOW);
      delayMicroseconds(2);
    }
  }
  
  delayMicroseconds(5);
  digitalWrite(loadPin, HIGH);
  delayMicroseconds(5);
}

// Funktion zum Leeren des Speichers
void clearDisplay() {
  for (byte i = 1; i <= 8; i++) {
    sendCommandAll(i, 0x00); // Schreibt "Null" in alle 8 Segment-Register
  }
}

void setup() {
  pinMode(clkPin, OUTPUT);
  pinMode(loadPin, OUTPUT);
  for(int d = 0; d < 5; d++) {
    pinMode(dataPins[d], OUTPUT);
    digitalWrite(dataPins[d], LOW);
  }
  
  digitalWrite(loadPin, HIGH);
  digitalWrite(clkPin, LOW);
  
  delay(100); 
  
  sendCommandAll(0x09, 0x00); // Decode-Mode AUS
  sendCommandAll(0x0A, 0x0F); // Helligkeit MAX
  sendCommandAll(0x0B, 0x07); // Scan-Limit: Alle 8 Digits
  sendCommandAll(0x0C, 0x01); // Shutdown beenden (Normalbetrieb)
  
  // WICHTIG: Zufälligen Speicher-Müll löschen
  clearDisplay(); 
}

void loop() {
  // Zeigt den Hardware-Test (Alles an)
  sendCommandAll(0x0F, 0x01); 
  delay(2000);
  
  // Beendet den Hardware-Test (Kehrt zum geleerten Speicher zurück -> Alles aus)
  sendCommandAll(0x0F, 0x00); 
  delay(2000);
}
