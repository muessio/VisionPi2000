// =================================================================================
// VisionPi2000 - ARDUINO MEGA KONTROLL-SOFTWARE (FINAL VERSION)
// =================================================================================

// --- 1. PIN-DEFINITIONEN ---
// Dart-Matrix (4 Reihen, 16 Spalten)
const int rowPins[4]  = {22, 24, 26, 28}; 
const int colPins[16] = {30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 23, 42, 43, 44, 45};

// Taster, Sensoren & Relais
const int btnRed      = 46;
const int btnBlue     = 47;
const int btnGrey     = 48;
const int btnStart    = 49;
const int btnPlayer   = 50;
const int irSensorPin = 2;  
const int lightRelayPin = 3;  
const int piezoPin    = A0; 

// --- 2. LÖWEN DISPLAY PINS (10x MAX7219 HYBRID SPI) ---
const int clkPin  = 4;   // ST1 Pin 20 (Clock)
const int loadPin = 5;   // ST1 Pin 18 (Load / CS)
const int dPins[5] = {6, 7, 8, 9, 10}; // D0=Pin16, D1=Pin11, D2=Pin7, D3=Pin3, D4=Pin1

// Speicher für alle Chips (5 Stränge, je 2 Chips, 8 Digits)
byte displayMem[5][2][8] = {0};

// 7-Segment Hex-Übersetzer (0-9 und Blank)
byte getChar(byte value) {
  switch(value) {
    case 0: return 0x7E; case 1: return 0x30; case 2: return 0x6D;
    case 3: return 0x79; case 4: return 0x33; case 5: return 0x5B;
    case 6: return 0x5F; case 7: return 0x70; case 8: return 0x7F;
    case 9: return 0x7B; case 15: return 0x00; // 15 = Blank (Leer)
    default: return 0x00;
  }
}

// --- 3. DART-MATRIX ARRAY ---
const String dartBoard[4][16] = {
  {"d12", "12", "d9", "9", "d14", "14", "d11", "11", "d8", "8", "-",  "t12", "t9", "t14", "t11", "t8"},
  {"d16", "16", "d7", "7", "d19", "19", "d3", "3", "d17", "17", "db", "t16", "t7", "t19", "t3", "t17"},
  {"d2",  "2",  "d15", "15", "d10", "10", "d6", "6", "d13", "13", "b",  "t2",  "t15", "t10", "t6", "t13"},
  {"d4",  "4",  "d18", "18", "d1",  "1",  "d20", "20", "d5",  "5",  "-",  "t4",  "t18", "t1",  "t20", "t5"}
};

// --- 4. TIMING VARIABLEN ---
unsigned long lastHitTime = 0;       
const int debounceDelay = 300;       

// Piezo-Setup
unsigned long piezoHitTime = 0;
bool piezoTriggered = false;
const int piezoThreshold = 15; 
const int piezoMatrixWaitTime = 100; 

// Entprell-Zeiten und Speicher für Taster/Sensoren
const int btnDebounceDelay = 200; 
const int irDebounceDelay = 500;  
unsigned long lastPressRed, lastPressBlue, lastPressGrey, lastPressStart, lastPressPlayer, lastPressIR = 0;
bool stateRed, stateBlue, stateGrey, stateStart, statePlayer, stateIR = true;
bool lastRed, lastBlue, lastGrey, lastStart, lastPlayer, lastIR = true;

// =================================================================================
// DISPLAY SPI-FUNKTIONEN (PARALLEL FÜR 5 STRÄNGE)
// =================================================================================
void shift16Parallel(byte addr, byte data[5]) {
  // Register-Adresse senden (8 Bit)
  for (int i = 7; i >= 0; i--) {
    digitalWrite(clkPin, LOW);
    for (int c = 0; c < 5; c++) { digitalWrite(dPins[c], (addr >> i) & 1); }
    delayMicroseconds(2);
    digitalWrite(clkPin, HIGH);
    delayMicroseconds(2);
  }
  // Daten-Byte senden (8 Bit)
  for (int i = 7; i >= 0; i--) {
    digitalWrite(clkPin, LOW);
    for (int c = 0; c < 5; c++) { digitalWrite(dPins[c], (data[c] >> i) & 1); }
    delayMicroseconds(2);
    digitalWrite(clkPin, HIGH);
    delayMicroseconds(2);
  }
}

void shiftOutParallel(byte addr1, byte data1[5], byte addr0, byte data0[5]) {
  digitalWrite(loadPin, LOW);
  delayMicroseconds(3);
  shift16Parallel(addr1, data1); // Chip 2 (hinten im Strang)
  shift16Parallel(addr0, data0); // Chip 1 (vorne im Strang)
  delayMicroseconds(3);
  digitalWrite(loadPin, HIGH); // Daten im Display verriegeln  
  delayMicroseconds(3);
}

void sendCommandToAll(byte addr, byte data) {
  byte dataArr[5] = {data, data, data, data, data};
  shiftOutParallel(addr, dataArr, addr, dataArr);
}

// =================================================================================
// SETUP (SYSTEM-INITIALISIERUNG)
// =================================================================================
void setup() {
  Serial.begin(115200); 

  // Matrix konfigurieren
  for (int r = 0; r < 4; r++) { pinMode(rowPins[r], OUTPUT); digitalWrite(rowPins[r], HIGH); }
  for (int c = 0; c < 16; c++) { pinMode(colPins[c], INPUT_PULLUP); }

  // Taster & Sensoren konfigurieren
  pinMode(btnRed, INPUT_PULLUP); pinMode(btnBlue, INPUT_PULLUP);
  pinMode(btnGrey, INPUT_PULLUP); pinMode(btnStart, INPUT_PULLUP);
  pinMode(btnPlayer, INPUT_PULLUP); pinMode(irSensorPin, INPUT_PULLUP);
  
  // Relais konfigurieren
  pinMode(lightRelayPin, OUTPUT); digitalWrite(lightRelayPin, LOW); 

  // Display konfigurieren
  pinMode(clkPin, OUTPUT); pinMode(loadPin, OUTPUT);
  for(int i=0; i<5; i++) { pinMode(dPins[i], OUTPUT); digitalWrite(dPins[i], LOW); }
  digitalWrite(clkPin, HIGH); digitalWrite(loadPin, HIGH);

  delay(500);

  // --- MAX7219 INITIALISIERUNG ---
  sendCommandToAll(0x09, 0x00); // Decode-Mode aus (Wir senden Rohdaten)
  sendCommandToAll(0x0B, 0x07); // Scan-Limit: 8 Digits nutzen
  sendCommandToAll(0x0A, 0x0F); // Helligkeit: Maximum
  sendCommandToAll(0x0C, 0x01); // Shutdown aus: Normalbetrieb AN

  // Boot-Sequenz: Hardware-Test für 1,5 Sekunden
  sendCommandToAll(0x0F, 0x01); 
  delay(1500);                    
  sendCommandToAll(0x0F, 0x00);   

  // Display komplett löschen (Speichermüll entfernen)
  for(int i = 0; i < 8; i++) {
    byte blank[5] = {0, 0, 0, 0, 0};
    shiftOutParallel(i + 1, blank, i + 1, blank);
  }

  // Melden, dass der Arduino einsatzbereit ist
  Serial.println("SYSTEM:READY"); 
}

// =================================================================================
// HAUPTSCHLEIFE (LOOP)
// =================================================================================
void loop() {
  unsigned long currentMillis = millis();

  // --- 1. BEFEHLE VOM RASPBERRY PI EMPFANGEN ---
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); 
    
    if (command.startsWith("DISP:") || command.startsWith("RAW:")) {
      bool isRaw = command.startsWith("RAW:");
      int firstColon = command.indexOf(':');
      int secondColon = command.indexOf(':', firstColon + 1);
      int thirdColon = command.indexOf(':', secondColon + 1);
      
      if (secondColon > 0 && thirdColon > 0) {
        int chip  = command.substring(firstColon + 1, secondColon).toInt();
        int digit = command.substring(secondColon + 1, thirdColon).toInt();
        int value = command.substring(thirdColon + 1).toInt();
        
        if (chip >= 0 && chip < 10 && digit >= 0 && digit < 8) {
          int chain = chip / 2;      
          int chipIdx = chip % 2;    
          
          if (isRaw) {
            displayMem[chain][chipIdx][digit] = (byte)value; 
          } else {
            displayMem[chain][chipIdx][digit] = getChar(value); 
          }
          
          byte d1[5], d0[5];
          for (int c = 0; c < 5; c++) {
            d1[c] = displayMem[c][1][digit];
            d0[c] = displayMem[c][0][digit];
          }
          shiftOutParallel(digit + 1, d1, digit + 1, d0);
        }
      }
    }
    else if (command == "LIGHT:ON") { digitalWrite(lightRelayPin, HIGH); }
    else if (command == "LIGHT:OFF") { digitalWrite(lightRelayPin, LOW); }
  }

  // --- 2. DART-MATRIX AUSLESEN ---
  if (currentMillis - lastHitTime > debounceDelay) {
    for (int r = 0; r < 4; r++) {
      digitalWrite(rowPins[r], LOW); 
      delayMicroseconds(10);         
      for (int c = 0; c < 16; c++) {
        if (digitalRead(colPins[c]) == LOW) { 
          String hitSegment = dartBoard[r][c];
          if (hitSegment != "-") { 
            Serial.print("HIT:"); Serial.println(hitSegment);
            lastHitTime = currentMillis;  
            piezoTriggered = false;     
          }
        }
      }
      digitalWrite(rowPins[r], HIGH); 
    }
  }

  // --- 3. PIEZO-SENSOR (FEHLWÜRFE) ---
  int piezoValue = analogRead(piezoPin);
  
  if (piezoValue >= piezoThreshold && (currentMillis - lastHitTime > debounceDelay)) {
    if (!piezoTriggered) { 
      piezoTriggered = true; 
      piezoHitTime = currentMillis; 
    }
  }
  
  if (piezoTriggered && (currentMillis - piezoHitTime > piezoMatrixWaitTime)) {
    Serial.println("MISS:1");
    piezoTriggered = false; 
    lastHitTime = currentMillis; 
  }

  // --- 4. ARCADE-TASTEN & IR-SENSOR ---
  stateRed = digitalRead(btnRed);
  if (stateRed == LOW && lastRed == HIGH) { 
    if (currentMillis - lastPressRed > btnDebounceDelay) {
      Serial.println("BTN:RED"); 
      lastPressRed = currentMillis;
    }
  }
  lastRed = stateRed;

  stateBlue = digitalRead(btnBlue);
  if (stateBlue == LOW && lastBlue == HIGH) { 
    if (currentMillis - lastPressBlue > btnDebounceDelay) {
      Serial.println("BTN:BLUE"); 
      lastPressBlue = currentMillis;
    }
  }
  lastBlue = stateBlue;

  stateGrey = digitalRead(btnGrey);
  if (stateGrey == LOW && lastGrey == HIGH) { 
    if (currentMillis - lastPressGrey > btnDebounceDelay) {
      Serial.println("BTN:GREY"); 
      lastPressGrey = currentMillis;
    }
  }
  lastGrey = stateGrey;

  stateStart = digitalRead(btnStart);
  if (stateStart == LOW && lastStart == HIGH) { 
    if (currentMillis - lastPressStart > btnDebounceDelay) {
      Serial.println("BTN:START"); 
      lastPressStart = currentMillis;
    }
  }
  lastStart = stateStart;

  statePlayer = digitalRead(btnPlayer);
  if (statePlayer == LOW && lastPlayer == HIGH) { 
    if (currentMillis - lastPressPlayer > btnDebounceDelay) {
      Serial.println("BTN:PLAYER"); 
      lastPressPlayer = currentMillis;
    }
  }
  lastPlayer = statePlayer;

  stateIR = digitalRead(irSensorPin);
  if (stateIR == LOW && lastIR == HIGH) { 
    if (currentMillis - lastPressIR > irDebounceDelay) {
      Serial.println("IR:DETECT"); 
      lastPressIR = currentMillis;
    }
  }
  lastIR = stateIR;

  // --- 5. TASTEN-COMBO (Rot + Blau + Grau für 2 Sek) ---
  static unsigned long comboTimer = 0;
  static bool comboTriggered = false;
  
  bool r = (digitalRead(btnRed) == LOW);
  bool b = (digitalRead(btnBlue) == LOW);
  bool g = (digitalRead(btnGrey) == LOW);

  if (r && b && g) {
    if (comboTimer == 0) {
      comboTimer = currentMillis;
    } else if (currentMillis - comboTimer >= 2000 && !comboTriggered) {
      Serial.println("BTN:COMBO");
      comboTriggered = true;
    }
  } else if (!r && !b && !g) {
    comboTimer = 0;
    comboTriggered = false;
  }
}
