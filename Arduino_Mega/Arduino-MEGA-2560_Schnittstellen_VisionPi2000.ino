// =================================================================================
// VisionPi2000 - ARDUINO MEGA KONTROLL-SOFTWARE (PARALLEL DISPLAY ARCHITECTURE)
// Inkl. Matrix, Taster, Piezo, IR, Relais und Custom MAX7219 Bit-Banging
// =================================================================================

// --- 1. PIN-DEFINITIONEN ---
// Matrix
const int rowPins[4]  = {22, 24, 26, 28}; 
const int colPins[16] = {30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45};

// Taster, Sensoren & Relais
const int btnRed      = 46;
const int btnBlue     = 47;
const int btnGrey     = 48;
const int btnStart    = 49;
const int btnPlayer   = 50;
const int irSensorPin = 2;  
const int lightRelayPin = 3;  
const int piezoPin    = A0; 

// --- 2. LÖWEN DISPLAY PINS (PARALLEL SPI) ---
const int clkPin  = 4;   // ST1 Pin 19
const int loadPin = 5;   // ST1 Pin 17
const int dPins[5] = {6, 7, 8, 9, 10}; // ST1 Pins: 15, 11, 7, 3, 1

// Speicher für alle Chips (5 Stränge, je 2 Chips, 8 Digits)
byte displayMem[5][2][8] = {0};

// 7-Segment Hex-Übersetzer (0-9 und Blank)
byte getChar(byte value) {
  switch(value) {
    case 0: return 0x7E; case 1: return 0x30; case 2: return 0x6D;
    case 3: return 0x79; case 4: return 0x33; case 5: return 0x5B;
    case 6: return 0x5F; case 7: return 0x70; case 8: return 0x7F;
    case 9: return 0x7B; case 15: return 0x00; // 15 = Blank
    default: return 0x00;
  }
}

// --- 3. DART-MATRIX ARRAY ---
const String dartBoard[4][16] = {
  {"d12", "12", "d9", "9", "d14", "14", "d11", "11", "d8", "8", "-",  "b",  "t9", "t14", "t11", "t8"},
  {"d16", "16", "d7", "7", "d19", "19", "d3", "3", "d17", "17", "db", "t16", "t7", "t19", "t3", "t17"},
  {"d2",  "2",  "d15", "15", "d10", "10", "d6", "6", "d13", "13", "b",  "t2", "t15", "t10", "t6", "t13"},
  {"d4",  "4",  "d18", "18", "d1",  "1",  "d20", "20", "d5",  "5",  "-",  "t4", "t18", "t1",  "t20", "t5"}
};

// --- 4. TIMING VARIABLEN ---
unsigned long lastHitTime = 0;       
const int debounceDelay = 300;       
unsigned long piezoHitTime = 0;
bool piezoTriggered = false;
const int piezoThreshold = 150;      
const int piezoMatrixWaitTime = 100; 

// NEU: Entprell-Zeiten und Speicher für Taster/Sensoren
const int btnDebounceDelay = 200; // 200ms Sperrzeit für mechanische Taster
const int irDebounceDelay = 500;  // 500ms Sperrzeit für IR-Sensor
unsigned long lastPressRed = 0;
unsigned long lastPressBlue = 0;
unsigned long lastPressGrey = 0;
unsigned long lastPressStart = 0;
unsigned long lastPressPlayer = 0;
unsigned long lastPressIR = 0;

bool stateRed, stateBlue, stateGrey, stateStart, statePlayer, stateIR = true;
bool lastRed, lastBlue, lastGrey, lastStart, lastPlayer, lastIR = true;

// =================================================================================
// EIGENE SPI-FUNKTIONEN FÜR PARALLELE MAX7219 CHIPS
// =================================================================================
void shift16Parallel(byte addr, byte data[5]) {
  // Adresse takten (8 Bit)
  for (int i = 7; i >= 0; i--) {
    digitalWrite(clkPin, LOW);
    for (int c = 0; c < 5; c++) { digitalWrite(dPins[c], (addr >> i) & 1); }
    digitalWrite(clkPin, HIGH);
  }
  // Daten takten (8 Bit)
  for (int i = 7; i >= 0; i--) {
    digitalWrite(clkPin, LOW);
    for (int c = 0; c < 5; c++) { digitalWrite(dPins[c], (data[c] >> i) & 1); }
    digitalWrite(clkPin, HIGH);
  }
}

void shiftOutParallel(byte addr1, byte data1[5], byte addr0, byte data0[5]) {
  digitalWrite(loadPin, LOW);
  shift16Parallel(addr1, data1); // Geht in Chip 1 (den hinteren)
  shift16Parallel(addr0, data0); // Bleibt in Chip 0 (den vorderen)
  digitalWrite(loadPin, HIGH);   // Latch / Übernehmen
}

void sendCommandToAll(byte addr, byte data) {
  byte dataArr[5] = {data, data, data, data, data};
  shiftOutParallel(addr, dataArr, addr, dataArr);
}

void setup() {
  Serial.begin(115200); 

  // Matrix Init
  for (int r = 0; r < 4; r++) { pinMode(rowPins[r], OUTPUT); digitalWrite(rowPins[r], HIGH); }
  for (int c = 0; c < 16; c++) { pinMode(colPins[c], INPUT_PULLUP); }

  // Taster & Sensoren Init
  pinMode(btnRed, INPUT_PULLUP); pinMode(btnBlue, INPUT_PULLUP);
  pinMode(btnGrey, INPUT_PULLUP); pinMode(btnStart, INPUT_PULLUP);
  pinMode(btnPlayer, INPUT_PULLUP); pinMode(irSensorPin, INPUT_PULLUP);
  
  pinMode(lightRelayPin, OUTPUT); digitalWrite(lightRelayPin, LOW); 

  // Display Pins Init
  pinMode(clkPin, OUTPUT); pinMode(loadPin, OUTPUT);
  for(int i=0; i<5; i++) { pinMode(dPins[i], OUTPUT); digitalWrite(dPins[i], LOW); }
  digitalWrite(clkPin, HIGH); digitalWrite(loadPin, HIGH);

  // MAX7219 Boot-Sequenz für alle 10 Chips gleichzeitig
  sendCommandToAll(0x0F, 0x00); // Testmodus aus
  sendCommandToAll(0x09, 0x00); // Decode-Mode aus (wir senden Rohdaten)
  sendCommandToAll(0x0B, 0x07); // Scan-Limit (Alle 8 Digits an)
  sendCommandToAll(0x0A, 0x08); // Helligkeit Mittel
  sendCommandToAll(0x0C, 0x01); // Wakeup

  // Display leeren
  for(int i = 0; i < 8; i++) {
    byte blank[5] = {0,0,0,0,0};
    shiftOutParallel(i + 1, blank, i + 1, blank);
  }

  Serial.println("SYSTEM:READY"); 
}

void loop() {
  unsigned long currentMillis = millis();

  // ---------------------------------------------------------
  // 1. BEFEHLE VOM PI EMPFANGEN (DISPLAY & LICHT)
  // ---------------------------------------------------------
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    // Prüfen, ob es ein normaler (DISP) oder ein roher (RAW) Befehl ist
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
          int chain = chip / 2;      // Rechnet Chip (0-9) auf Datenstrang (0-4) um
          int chipIdx = chip % 2;    // Rechnet Chip auf Position (0 oder 1) um
          
          // ENTSCHEIDUNG: Übersetzen oder Rohwert eintragen
          if (isRaw) {
            displayMem[chain][chipIdx][digit] = (byte)value; 
          } else {
            displayMem[chain][chipIdx][digit] = getChar(value); 
          }
          
          // Dieses eine Digit für alle Chips über alle Stränge updaten
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

  // ---------------------------------------------------------
  // 2. DART-MATRIX AUSLESEN
  // ---------------------------------------------------------
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

  // ---------------------------------------------------------
  // 3. PIEZO FEHLWURFSENSOR
  // ---------------------------------------------------------
  int piezoValue = analogRead(piezoPin);
  if (piezoValue > piezoThreshold && (currentMillis - lastHitTime > debounceDelay)) {
    if (!piezoTriggered) { piezoTriggered = true; piezoHitTime = currentMillis; }
  }
  if (piezoTriggered && (currentMillis - piezoHitTime > piezoMatrixWaitTime)) {
    Serial.println("MISS:1");
    piezoTriggered = false; lastHitTime = currentMillis; 
  }

  // ---------------------------------------------------------
  // 4. ARCADE-TASTEN & IR-SENSOR (Blockierungsfrei entprellt)
  // ---------------------------------------------------------
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
}
