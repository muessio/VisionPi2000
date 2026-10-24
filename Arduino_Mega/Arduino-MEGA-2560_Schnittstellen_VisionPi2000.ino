// =================================================================================
// VisionPi2000 - ARDUINO MEGA KONTROLL-SOFTWARE (FINALER FIX FÜR STRANG 4 / U9)
// =================================================================================

const int rowPins[4]  = {22, 24, 26, 28}; 
const int colPins[16] = {30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 23, 42, 43, 44, 45};
const int btnRed      = 46;
const int btnBlue     = 47;
const int btnGrey     = 48;
const int btnStart    = 49;
const int btnPlayer   = 50;
const int irSensorPin = 2;  
const int lightRelayPin = 3;  
const int piezoPin    = A0; 

const int clkPin   = 4;   
const int loadPin  = 5;   
const int dPins[5] = {6, 7, 8, 9, 10}; // D0 bis D4

byte displayMem[5][2][8] = {0};

const String dartBoard[4][16] = {
  {"d12", "12", "d9", "9", "d14", "14", "d11", "11", "d8", "8", "-",  "t12", "t9", "t14", "t11", "t8"},
  {"d16", "16", "d7", "7", "d19", "19", "d3", "3", "d17", "17", "db", "t16", "t7", "t19", "t3", "t17"},
  {"d2",  "2",  "d15", "15", "d10", "10", "d6", "6", "d13", "13", "b",  "t2",  "t15", "t10", "t6", "t13"},
  {"d4",  "4",  "d18", "18", "d1",  "1",  "d20", "20", "d5",  "5",  "-",  "t4",  "t18", "t1",  "t20", "t5"}
};

unsigned long lastHitTime = 0;       
const int debounceDelay = 300;       
unsigned long piezoHitTime = 0;
bool piezoTriggered = false;
const int piezoThreshold = 15; 
const int piezoMatrixWaitTime = 100; 

const int btnDebounceDelay = 200; 
unsigned long lastPressRed, lastPressBlue, lastPressGrey, lastPressStart, lastPressPlayer = 0;
bool stateRed, stateBlue, stateGrey, stateStart, statePlayer = true;
bool lastRed, lastBlue, lastGrey, lastStart, lastPlayer = true;

bool lastIrState = HIGH;
unsigned long lastIrChangeTime = 0;
const unsigned long irDebounceTime = 300;

void sendCommandToAll(byte addr, byte data) {
  digitalWrite(loadPin, LOW);
  delayMicroseconds(3);
  for (int repeat = 0; repeat < 2; repeat++) {
    for (int i = 7; i >= 0; i--) {
      digitalWrite(clkPin, LOW);
      for (int c = 0; c < 5; c++) { digitalWrite(dPins[c], (addr >> i) & 1); }
      delayMicroseconds(1);
      digitalWrite(clkPin, HIGH);
      delayMicroseconds(1);
    }
    for (int i = 7; i >= 0; i--) {
      digitalWrite(clkPin, LOW);
      for (int c = 0; c < 5; c++) { digitalWrite(dPins[c], (data >> i) & 1); }
      delayMicroseconds(1);
      digitalWrite(clkPin, HIGH);
      delayMicroseconds(1);
    }
  }
  digitalWrite(loadPin, HIGH);
}

void updateDigitForAllStrands(int digitIndex) {
  digitalWrite(loadPin, LOW);
  delayMicroseconds(3);

  byte addr = digitIndex + 1;

  // --- SCHRITT 1: Adresse senden ---
  // Stränge 0-3 (2 Chips) bekommen die Adresse zweimal. Strang 4 (U9, 1 Chip) bekommt sie einmal im 2. Slot.
  for (int i = 7; i >= 0; i--) {
    digitalWrite(clkPin, LOW);
    for (int c = 0; c < 4; c++) { digitalWrite(dPins[c], (addr >> i) & 1); }
    digitalWrite(dPins[4], LOW); // Strang 4 wartet im 1. Slot
    delayMicroseconds(1);
    digitalWrite(clkPin, HIGH);
    delayMicroseconds(1);
  }

  for (int i = 7; i >= 0; i--) {
    digitalWrite(clkPin, LOW);
    for (int c = 0; c < 4; c++) { digitalWrite(dPins[c], (addr >> i) & 1); }
    digitalWrite(dPins[4], (addr >> i) & 1); // Strang 4 bekommt hier seine Adresse
    delayMicroseconds(1);
    digitalWrite(clkPin, HIGH);
    delayMicroseconds(1);
  }

  // --- SCHRITT 2: Daten für Chip 1 (Hinterer Chip in Kette für 0-3) ---
  for (int i = 7; i >= 0; i--) {
    digitalWrite(clkPin, LOW);
    for (int c = 0; c < 4; c++) { digitalWrite(dPins[c], (displayMem[c][1][digitIndex] >> i) & 1); }
    digitalWrite(dPins[4], LOW);
    delayMicroseconds(1);
    digitalWrite(clkPin, HIGH);
    delayMicroseconds(1);
  }

  // --- SCHRITT 3: Daten für Chip 0 (Vorderer Chip für 0-3 bzw. U9 für Strang 4) ---
  for (int i = 7; i >= 0; i--) {
    digitalWrite(clkPin, LOW);
    for (int c = 0; c < 4; c++) { digitalWrite(dPins[c], (displayMem[c][0][digitIndex] >> i) & 1); }
    digitalWrite(dPins[4], (displayMem[4][0][digitIndex] >> i) & 1); // U9 Daten
    delayMicroseconds(1);
    digitalWrite(clkPin, HIGH);
    delayMicroseconds(1);
  }

  digitalWrite(loadPin, HIGH);
  delayMicroseconds(3);
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
  
  pinMode(clkPin, OUTPUT); pinMode(loadPin, OUTPUT);
  for(int i=0; i<5; i++) { pinMode(dPins[i], OUTPUT); digitalWrite(dPins[i], LOW); }
  digitalWrite(clkPin, HIGH); digitalWrite(loadPin, HIGH);
  delay(500);

  sendCommandToAll(0x09, 0x00); 
  sendCommandToAll(0x0B, 0x07); 
  sendCommandToAll(0x0A, 0x0F); 
  sendCommandToAll(0x0C, 0x01); 

  sendCommandToAll(0x0F, 0x01); 
  delay(1500);                    
  sendCommandToAll(0x0F, 0x00);   

  for (int i = 0; i < 8; i++) {
    for (int c = 0; c < 5; c++) {
      displayMem[c][0][i] = 0;
      displayMem[c][1][i] = 0;
    }
    updateDigitForAllStrands(i);
  }
  Serial.println("SYSTEM:READY"); 
}

void loop() {
  unsigned long currentMillis = millis();

  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); 
    
    if (command.startsWith("RAW:")) {
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
          displayMem[chain][chipIdx][digit] = (byte)value; 
          
          updateDigitForAllStrands(digit);
        }
      }
    }
    else if (command == "LIGHT:ON") { digitalWrite(lightRelayPin, HIGH); }
    else if (command == "LIGHT:OFF") { digitalWrite(lightRelayPin, LOW); }
  }

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
  if (currentIrState == HIGH && lastIrState == LOW) {
    if (currentMillis - lastIrChangeTime > irDebounceTime) {
      Serial.println("IR:DETECT");
      lastIrChangeTime = currentMillis;
    }
  }
  lastIrState = currentIrState;

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
