/*
 * Роборука на Arduino Uno (без Shield)
 * 8 сервоприводов SG90
 * Управление через Bluetooth HC-05
 * 
 * Подключение серво:
 * D3  → Серво #0 (Большой палец)
 * D5  → Серво #1 (Указательный)
 * D6  → Серво #2 (Средний)
 * D9  → Серво #3 (Безымянный)
 * D10 → Серво #4 (Мизинец)
 * D11 → Серво #5 (Запястье)
 * A0  → Серво #6 (Локоть)
 * A1  → Серво #7 (Плечо)
 */

#include <Servo.h>

// Сервоприводы
Servo servos[8];

// Пины на Arduino Uno
const int servoPins[8] = {3, 5, 6, 9, 10, 11, A0, A1};

// Текущие позиции
int positions[8] = {90, 90, 90, 90, 90, 90, 90, 90};

// Названия
const char* servoNames[8] = {
  "Thumb", "Index", "Middle", "Ring", 
  "Pinky", "Wrist", "Elbow", "Shoulder"
};

void setup() {
  Serial.begin(9600);
  
  // Инициализация сервоприводов
  for (int i = 0; i < 8; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(positions[i]);
    delay(100);
  }
  
  Serial.println("READY");
  Serial.println("Robot Arm - Arduino Uno");
  Serial.println("Commands: SET:a,b,c,d,e,f,g,h | HOME | GRIP | OPEN | STATUS");
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    if (cmd.length() > 0) {
      processCommand(cmd);
    }
  }
}

void processCommand(String cmd) {
  if (cmd.startsWith("SET:")) {
    parseSetCommand(cmd.substring(4));
  }
  else if (cmd == "HOME") {
    moveToAll(90);
    Serial.println("HOME_OK");
  }
  else if (cmd == "GRIP") {
    int grip[8] = {45, 30, 30, 30, 30, 90, 120, 90};
    moveTo(grip);
    Serial.println("GRIP_OK");
  }
  else if (cmd == "OPEN") {
    moveToAll(90);
    Serial.println("OPEN_OK");
  }
  else if (cmd == "STATUS") {
    Serial.print("POS:");
    for (int i = 0; i < 8; i++) {
      Serial.print(positions[i]);
      if (i < 7) Serial.print(",");
    }
    Serial.println();
  }
  else if (cmd == "TEST") {
    testServos();
  }
  else if (cmd == "HELP") {
    Serial.println("Commands:");
    Serial.println("  SET:a,b,c,d,e,f,g,h - Angles (0-180)");
    Serial.println("  HOME - All to 90°");
    Serial.println("  GRIP - Close grip");
    Serial.println("  OPEN - Open hand");
    Serial.println("  STATUS - Current positions");
    Serial.println("  TEST - Test servos");
  }
  else {
    Serial.println("Unknown. Send HELP for list.");
  }
}

void parseSetCommand(String data) {
  int values[8];
  int idx = 0;
  int start = 0;
  
  for (int i = 0; i <= data.length() && idx < 8; i++) {
    if (i == data.length() || data.charAt(i) == ',') {
      values[idx++] = constrain(data.substring(start, i).toInt(), 0, 180);
      start = i + 1;
    }
  }
  
  if (idx == 8) {
    moveTo(values);
    Serial.println("SET_OK");
  } else {
    Serial.println("ERROR: Need 8 values");
  }
}

void moveTo(int targets[8]) {
  int steps = 20;
  
  for (int step = 0; step < steps; step++) {
    for (int i = 0; i < 8; i++) {
      int diff = targets[i] - positions[i];
      if (abs(diff) > 0) {
        positions[i] += diff / steps;
        servos[i].write(positions[i]);
      }
    }
    delay(15);
  }
  
  for (int i = 0; i < 8; i++) {
    positions[i] = targets[i];
    servos[i].write(positions[i]);
  }
  delay(100);
}

void moveToAll(int angle) {
  int targets[8];
  for (int i = 0; i < 8; i++) {
    targets[i] = angle;
  }
  moveTo(targets);
}

void testServos() {
  Serial.println("Testing servos...");
  
  Serial.println("Moving to 0°...");
  moveToAll(0);
  delay(1000);
  
  Serial.println("Moving to 90°...");
  moveToAll(90);
  delay(1000);
  
  Serial.println("Moving to 180°...");
  moveToAll(180);
  delay(1000);
  
  Serial.println("Moving to 90°...");
  moveToAll(90);
  
  Serial.println("Test complete!");
}
