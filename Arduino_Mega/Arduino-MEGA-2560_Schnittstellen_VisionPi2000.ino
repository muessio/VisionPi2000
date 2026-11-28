// =================================================================================
// VisionPi2000 - ARDUINO MEGA KONTROLL-SOFTWARE (100% SYNCHRONES MAX7219 SPI - FIX)
// INKLUSIVE AUTONOMER LEUCHTMELDER-STEUERUNG (START & SPIELERWECHSEL)
// Version 1.6.4 (100us Matrix-Einschwingzeit, leicht angepasste Piezo-Schwelle)
// =================================================================================

const int rowPins[4]  = {22, 24, 26, 28}; 
const int colPins[16] = {30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45};
const int btnRed      = 46;
const int btnBlue     = 47;
const int btnGrey     = 48;
const int btnStart    = 49;
const int btnPlayer   = 50;
const int irSensorPin = 2;  
const int lightRelayPin = 3;  
const int piezoPin    = A0; 

// --- Pins für die Tasten-Leuchtmelder ---
const int lampStartPin  = 11; // Pin für die Lampe der Start-Taste
const int lampPlayerPin = 12; // Pin für die Lampe der Spielerwechsel-Taste
int modeLampStart  = 0;        // 0=Aus, 1=An, 2=Blinken
int modeLampPlayer = 0;        // 0=Aus, 1=An, 2=Blinken
// ----------------------------------------

const int clkPin   = 4;    
const int loadPin  = 5;    
const int dPins[5] = {6, 7, 8, 9, 10}; // D0 bis D4

// displayMem[Strang 0..4][0 = Vorderer Chip (DIN), 1 = Hinterer Chip (DOUT)][Digit 0..7]
byte displayMem[5][2][8] = {0};

char cmdBuffer[64];
int cmdIndex = 0;

const String dartBoard[4][16] = {
  {"d12", "12", "d9", "9", "d14", "14", "d11", "11", "d8", "8", "-",  "t12", "t9", "t14", "t11", "t8"},
  {"d16", "16", "d7", "7", "d19", "19", "d3", "3", "d17", "17", "db", "t16", "t7", "t19", "t3", "t17"},
  {"d2",  "2",  "d15", "15", "d10", "10", "d6", "6", "d13", "13", "b",  "t2",  "t15", "t10", "t6", "t13"},
  {"d4",  "4",  "d18", "18", "d1",  "1",  "d20", "20", "d5",  "5", "-",  "t4",  "t18", "t1",  "t20", "t5"}
};

unsigned long lastHitTime = 0;          // Zeitstempel des letzten gültigen Matrix-Treffers
unsigned long lastPiezoBlockTime = 0;   // Zeitstempel für Piezo-Sperre nach Treffer oder Fehlwurf
const int debounceDelay = 250;          // Matrix-Entprellung nach Treffer (ms)
const int piezoDebounceDelay = 500;     // Piezo-Sperrzeit nach Treffer/Fehlwurf (ms)
unsigned long piezoHitTime = 0;
unsigned long piezoFirstSpikeTime = 0;
int piezoSpikeCounter = 0;
bool piezoTriggered = false;
const int piezoThreshold = 18;          // Vorsichtig angepasst für passive Piezo-Schaltung (vorher 15)
const int piezoConfirmCount = 2;        // Mind. 2 Messungen >= piezoThreshold (filtert Einzel-Spikes)
const unsigned long piezoMatrixWaitTime = 130; // Ausreichendes Matrix-Vorrang-Fenster (ms)

const int btnDebounceDelay = 250;     // Tasten-Entprellung
unsigned long lastPressRed = 0, lastPressBlue = 0, lastPressGrey = 0, lastPressStart = 0, lastPressPlayer = 0;
bool stateRed = true, stateBlue = true, stateGrey = true, stateStart = true, statePlayer = true;
bool lastRed = true, lastBlue = true, lastGrey = true, lastStart = true, lastPlayer = true;

unsigned long lastIrChangeTime = 0;
const unsigned long irDebounceTime = 300; // Sende-Intervall (300ms), solange IR aktiv ist

unsigned long lastDisplayRefresh = 0;
const unsigned long displayRefreshInterval = 200; // Gestaffelter Register-Refresh: 1 Register pro 200 ms
byte refreshStep = 0;

inline void clockBit(byte b0, byte b1, byte b2, byte b3, byte b4) {
  digitalWrite(clkPin, LOW);
  digitalWrite(dPins[0], b0);
  digitalWrite(dPins[1], b1);
  digitalWrite(dPins[2], b2);
  digitalWrite(dPins[3], b3);
  digitalWrite(dPins[4], b4);
  delayMicroseconds(4);
  digitalWrite(clkPin, HIGH);
  delayMicroseconds(4);
  digitalWrite(clkPin, LOW);
  delayMicroseconds(2);
}

void sendCommandToAll(byte addr, byte data) {
  digitalWrite(clkPin, LOW);
  digitalWrite(loadPin, LOW);
  delayMicroseconds(5);

  for (int repeat = 0; repeat < 2; repeat++) {
    for (int i = 7; i >= 0; i--) {
      byte b = (addr >> i) & 1;
      clockBit(b, b, b, b, b);
    }
    for (int i = 7; i >= 0; i--) {
      byte b = (data >> i) & 1;
      clockBit(b, b, b, b, b);
    }
  }

  delayMicroseconds(5);
  digitalWrite(loadPin, HIGH);
  delayMicroseconds(5);
}

void refreshDisplayRegisters() {
  sendCommandToAll(0x0F, 0x00); // Display-Test Aus
  sendCommandToAll(0x09, 0x00); // Kein BCD-Decode
  sendCommandToAll(0x0B, 0x07); // Scan-Limit: alle 8 Digits
  sendCommandToAll(0x0A, 0x0F); // Maximale Helligkeit
  sendCommandToAll(0x0C, 0x01); // Normalbetrieb (kein Shutdown)
}

void updateDigitForAllStrands(int digitIndex) {
  digitalWrite(clkPin, LOW);
  digitalWrite(loadPin, LOW);
  delayMicroseconds(5);

  byte addr = digitIndex + 1;

  for (int i = 7; i >= 0; i--) {
    byte b = (addr >> i) & 1;
    clockBit(b, b, b, b, 0); 
  }
  for (int i = 7; i >= 0; i--) {
    clockBit(
      (displayMem[0][1][digitIndex] >> i) & 1,
      (displayMem[1][1][digitIndex] >> i) & 1,
      (displayMem[2][1][digitIndex] >> i) & 1,
      (displayMem[3][1][digitIndex] >> i) & 1,
      0
    );
  }

  for (int i = 7; i >= 0; i--) {
    byte b = (addr >> i) & 1;
    clockBit(b, b, b, b, b);
  }
  for (int i = 7; i >= 0; i--) {
    clockBit(
      (displayMem[0][0][digitIndex] >> i) & 1,
      (displayMem[1][0][digitIndex] >> i) & 1,
      (displayMem[2][0][digitIndex] >> i) & 1,
      (displayMem[3][0][digitIndex] >> i) & 1,
      (displayMem[4][0][digitIndex] >> i) & 1
    );
  }

  delayMicroseconds(5);
  digitalWrite(loadPin, HIGH);
  delayMicroseconds(5);
}

void clearAllDisplays() {
  refreshDisplayRegisters();
  for (int i = 0; i < 8; i++) {
    for (int c = 0; c < 5; c++) {
      displayMem[c][0][i] = 0;
      displayMem[c][1][i] = 0;
    }
    updateDigitForAllStrands(i);
  }
}

void fillAllDisplays() {
  refreshDisplayRegisters();
  for (int i = 0; i < 8; i++) {
    for (int c = 0; c < 5; c++) {
      displayMem[c][0][i] = 0xFF;
      displayMem[c][1][i] = 0xFF;
    }
    updateDigitForAllStrands(i);
  }
}

void processSerialCommand(String command) {
  command.trim();
  if (command.length() == 0) return;

  if (command == "LIGHT:ON") {
    digitalWrite(lightRelayPin, HIGH);
  }
  else if (command == "LIGHT:OFF") {
    digitalWrite(lightRelayPin, LOW);
  }
  else if (command.startsWith("LAMP:START:")) {
    modeLampStart = command.substring(11).toInt();
  }
  else if (command.startsWith("LAMP:PLAYER:")) {
    modeLampPlayer = command.substring(12).toInt();
  }
  else if (command == "CLEAR") {
    clearAllDisplays();
  }
  else if (command == "FILL" || command == "TEST:ON") {
    fillAllDisplays();
  }
  else if (command == "TEST:OFF") {
    clearAllDisplays();
  }
  else if (command.startsWith("RAW:")) {
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
        
        if (chain == 4) {
          displayMem[4][0][digit] = (byte)value; 
        } else {
          displayMem[chain][chipIdx][digit] = (byte)value; 
        }
        
        updateDigitForAllStrands(digit);
      }
    }
  }
}

void setup() {
  Serial.begin(115200); 
  for (int r = 0; r < 4; r++) { pinMode(rowPins[r], OUTPUT); digitalWrite(rowPins[r], HIGH); }
  for (int c = 0; c < 16; c++) { pinMode(colPins[c], INPUT_PULLUP); }
  
  pinMode(btnRed, INPUT_PULLUP); pinMode(btnBlue, INPUT_PULLUP);
  pinMode(btnGrey, INPUT_PULLUP); pinMode(btnStart, INPUT_PULLUP);
  pinMode(btnPlayer, INPUT_PULLUP); pinMode(irSensorPin, INPUT_PULLUP);
  
  pinMode(lightRelayPin, OUTPUT); 
  digitalWrite(lightRelayPin, LOW); 

  pinMode(lampStartPin, OUTPUT);
  pinMode(lampPlayerPin, OUTPUT);
  digitalWrite(lampStartPin, LOW);
  digitalWrite(lampPlayerPin, LOW);
  
  pinMode(clkPin, OUTPUT); pinMode(loadPin, OUTPUT);
  for(int i=0; i<5; i++) { pinMode(dPins[i], OUTPUT); digitalWrite(dPins[i], LOW); }
  digitalWrite(clkPin, LOW); 
  digitalWrite(loadPin, HIGH);
  delay(500);

  refreshDisplayRegisters();
  clearAllDisplays();
  Serial.println("SYSTEM:READY"); 
}

void loop() {
  unsigned long currentMillis = millis();

  // Gestaffeltes Auffrischen der MAX7219-Steuerregister (1 Register alle 200 ms)
  if (currentMillis - lastDisplayRefresh >= displayRefreshInterval) {
    switch (refreshStep) {
      case 0: sendCommandToAll(0x0F, 0x00); break; // Display-Test Aus
      case 1: sendCommandToAll(0x09, 0x00); break; // Kein BCD-Decode
      case 2: sendCommandToAll(0x0B, 0x07); break; // Scan-Limit: alle 8 Digits
      case 3: sendCommandToAll(0x0A, 0x0F); break; // Maximale Helligkeit
      case 4: sendCommandToAll(0x0C, 0x01); break; // Normalbetrieb (kein Shutdown)
    }
    refreshStep = (refreshStep + 1) % 5;
    lastDisplayRefresh = currentMillis;
  }

  bool blinkState2Hz = (currentMillis / 250) % 2;

  if (modeLampStart == 0) digitalWrite(lampStartPin, LOW);
  else if (modeLampStart == 1) digitalWrite(lampStartPin, HIGH);
  else if (modeLampStart == 2) digitalWrite(lampStartPin, blinkState2Hz);

  if (modeLampPlayer == 0) digitalWrite(lampPlayerPin, LOW);
  else if (modeLampPlayer == 1) digitalWrite(lampPlayerPin, HIGH);
  else if (modeLampPlayer == 2) digitalWrite(lampPlayerPin, blinkState2Hz);

  // Max. 1 seriellen Befehl pro loop() abarbeiten, damit der Matrix-Scan nicht blockiert wird
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (cmdIndex > 0) {
        cmdBuffer[cmdIndex] = '\0';
        processSerialCommand(String(cmdBuffer));
        cmdIndex = 0;
        break;
      }
    } else if (cmdIndex < 62) {
      cmdBuffer[cmdIndex++] = c;
    }
  }

  // 1. Matrix-Scan (hat Vorrang und verwirft ein offenes Piezo-Wartefenster)
  if (currentMillis - lastHitTime > debounceDelay) {
    bool hitFound = false;
    for (int r = 0; r < 4 && !hitFound; r++) {
      digitalWrite(rowPins[r], LOW); 
      delayMicroseconds(100);        // Erhöhte Einschwingzeit für hochohmige Folienkontakte
      for (int c = 0; c < 16; c++) {
        if (digitalRead(colPins[c]) == LOW) { 
          String hitSegment = dartBoard[r][c];
          if (hitSegment != "-") { 
            Serial.print("HIT:"); Serial.println(hitSegment);
            lastHitTime = currentMillis;
            lastPiezoBlockTime = currentMillis;
            piezoTriggered = false;     
            piezoSpikeCounter = 0;
            piezoHitTime = 0;
            hitFound = true;
            break;
          }
        }
      }
      digitalWrite(rowPins[r], HIGH); 
    }
  }

  // 2. Piezo-Auswertung mit Einschlag-Bestätigung (filtert Einzel-Spikes, 500 ms Sperre)
  if (currentMillis - lastPiezoBlockTime > piezoDebounceDelay) {
    int piezoValue = analogRead(piezoPin);
    if (!piezoTriggered) {
      if (piezoValue >= piezoThreshold) {
        if (piezoSpikeCounter == 0) {
          piezoFirstSpikeTime = currentMillis;
        }
        piezoSpikeCounter++;
        if (piezoSpikeCounter >= piezoConfirmCount) {
          piezoTriggered = true;
          piezoHitTime = currentMillis;
          piezoSpikeCounter = 0;
        }
      } else if (piezoSpikeCounter > 0 && (currentMillis - piezoFirstSpikeTime > 15)) {
        piezoSpikeCounter = 0;
      }
    }
  } else {
    piezoTriggered = false;
    piezoSpikeCounter = 0;
    piezoHitTime = 0;
  }

  // 3. Fehlwurf erst melden, wenn das 130-ms-Matrix-Vorrang-Fenster ohne Matrixtreffer abläuft
  if (piezoTriggered && (currentMillis - piezoHitTime >= piezoMatrixWaitTime)) {
    Serial.println("MISS:1");
    piezoTriggered = false; 
    piezoSpikeCounter = 0;
    piezoHitTime = 0;
    lastPiezoBlockTime = currentMillis;
  }

  stateRed = digitalRead(btnRed);
  if (stateRed == LOW && lastRed == HIGH) { 
    if (currentMillis - lastPressRed > btnDebounceDelay) { Serial.println("BTN:RED"); lastPressRed = currentMillis; }
  }
  lastRed = stateRed;

  stateBlue = digitalRead(btnBlue);
  if (stateBlue == LOW && lastBlue == HIGH) { 
    if (currentMillis - lastPressBlue > btnDebounceDelay) { Serial.println("BTN:BLUE"); lastPressBlue = currentMillis; }
  }
  lastBlue = stateBlue;

  stateGrey = digitalRead(btnGrey);
  if (stateGrey == LOW && lastGrey == HIGH) { 
    if (currentMillis - lastPressGrey > btnDebounceDelay) { Serial.println("BTN:GREY"); lastPressGrey = currentMillis; }
  }
  lastGrey = stateGrey;

  stateStart = digitalRead(btnStart);
  if (stateStart == LOW && lastStart == HIGH) { 
    if (currentMillis - lastPressStart > btnDebounceDelay) { Serial.println("BTN:START"); lastPressStart = currentMillis; }
  }
  lastStart = stateStart;

  statePlayer = digitalRead(btnPlayer);
  if (statePlayer == LOW && lastPlayer == HIGH) { 
    if (currentMillis - lastPressPlayer > btnDebounceDelay) { Serial.println("BTN:PLAYER"); lastPressPlayer = currentMillis; }
  }
  lastPlayer = statePlayer;

  bool currentIrState = digitalRead(irSensorPin);
  if (currentIrState == LOW) {
    if (currentMillis - lastIrChangeTime >= irDebounceTime) {
      Serial.println("IR:DETECT");
      lastIrChangeTime = currentMillis;
    }
  }

  static unsigned long comboTimer = 0;
  static bool comboTriggered = false;
  if ((digitalRead(btnRed) == LOW) && (digitalRead(btnBlue) == LOW) && (digitalRead(btnGrey) == LOW)) {
    if (comboTimer == 0) { comboTimer = currentMillis; }
    else if (currentMillis - comboTimer >= 2000 && !comboTriggered) {
      Serial.println("BTN:COMBO");
      comboTriggered = true;
    }
  } else {
    comboTimer = 0;
    comboTriggered = false;
  }
}
