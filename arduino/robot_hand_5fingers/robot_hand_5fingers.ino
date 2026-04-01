/*
 * Роборука - 5 пальцев
 * Arduino Uno
 * 
 * Подключение:
 * D3  → Большой палец
 * D5  → Указательный
 * D6  → Средний
 * D9  → Безымянный
 * D10 → Мизинец
 * 
 * Управление через Serial (USB или Bluetooth HC-05)
 */

#include <Servo.h>

// 5 сервоприводов для пальцев
Servo servos[5];

// Пины на Arduino Uno
const int servoPins[5] = {3, 5, 6, 9, 10};

// Названия пальцев
const char* fingerNames[5] = {"Thumb", "Index", "Middle", "Ring", "Pinky"};

// Текущие позиции (90° = открытая ладонь)
int positions[5] = {90, 90, 90, 90, 90};

// Флаг первой инициализации
bool initialized = false;

void setup() {
  Serial.begin(9600);
  
  // Даём время на подключение
  delay(1000);
  
  Serial.println("=== Robot Hand - 5 Fingers ===");
  Serial.println("Initializing servos...");
  
  // Инициализация сервоприводов
  for (int i = 0; i < 5; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(positions[i]);
    delay(100);
    Serial.print("  ");
    Serial.print(fingerNames[i]);
    Serial.println(" OK");
  }
  
  initialized = true;
  
  Serial.println("\n✓ READY!");
  Serial.println("\nCommands:");
  Serial.println("  OPEN        - Open hand");
  Serial.println("  GRIP        - Close grip");
  Serial.println("  HOME        - All to 90°");
  Serial.println("  SET:a,b,c,d,e - Set angles");
  Serial.println("  STATUS      - Current positions");
  Serial.println();
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
  if (cmd == "OPEN") {
    openHand();
    Serial.println("OPEN_OK");
  }
  else if (cmd == "GRIP") {
    grip();
    Serial.println("GRIP_OK");
  }
  else if (cmd == "HOME") {
    moveToAll(90);
    Serial.println("HOME_OK");
  }
  else if (cmd == "STATUS") {
    Serial.print("POS:");
    for (int i = 0; i < 5; i++) {
      Serial.print(positions[i]);
      if (i < 4) Serial.print(",");
    }
    Serial.println();
  }
  else if (cmd.startsWith("SET:")) {
    parseSetCommand(cmd.substring(4));
  }
  else if (cmd == "TEST") {
    testServos();
  }
  else if (cmd == "HELP") {
    printHelp();
  }
  else {
    Serial.println("Unknown. Send HELP for list.");
  }
}

// Открыть ладонь (все в 90°)
void openHand() {
  int open[5] = {90, 90, 90, 90, 90};
  moveTo(open, 500);
}

// Захват (сжать пальцы)
void grip() {
  int grip[5] = {45, 20, 20, 20, 20};
  moveTo(grip, 800);
}

// Установка всех позиций
void moveTo(int targets[5], int duration = 1000) {
  int steps = 20;
  int delayMs = max(1, duration / steps);
  
  for (int step = 0; step < steps; step++) {
    for (int i = 0; i < 5; i++) {
      int diff = targets[i] - positions[i];
      if (abs(diff) > 0) {
        positions[i] += diff / steps;
        servos[i].write(positions[i]);
      }
    }
    delay(delayMs);
  }
  
  // Финальная позиция
  for (int i = 0; i < 5; i++) {
    positions[i] = targets[i];
    servos[i].write(positions[i]);
  }
  delay(50);
}

void moveToAll(int angle) {
  int targets[5];
  for (int i = 0; i < 5; i++) {
    targets[i] = angle;
  }
  moveTo(targets, 800);
}

// Парсинг команды SET:a,b,c,d,e
void parseSetCommand(String data) {
  int values[5];
  int idx = 0;
  int start = 0;
  
  for (int i = 0; i <= data.length() && idx < 5; i++) {
    if (i == data.length() || data.charAt(i) == ',') {
      values[idx++] = constrain(data.substring(start, i).toInt(), 0, 180);
      start = i + 1;
    }
  }
  
  if (idx == 5) {
    moveTo(values, 800);
    Serial.println("SET_OK");
  } else {
    Serial.println("ERROR: Need 5 values");
    Serial.print("Got: ");
    Serial.println(idx);
  }
}

// Тест сервоприводов
void testServos() {
  Serial.println("\n=== Servo Test ===");
  
  // Все в 0°
  Serial.println("Moving to 0°...");
  int zero[5] = {0, 0, 0, 0, 0};
  moveTo(zero, 1500);
  delay(1000);
  
  // Все в 90°
  Serial.println("Moving to 90°...");
  int center[5] = {90, 90, 90, 90, 90};
  moveTo(center, 1500);
  delay(1000);
  
  // Все в 180°
  Serial.println("Moving to 180°...");
  int max[5] = {180, 180, 180, 180, 180};
  moveTo(max, 1500);
  delay(1000);
  
  // Все в 90°
  Serial.println("Moving to 90°...");
  moveTo(center, 1500);
  
  Serial.println("\nTest complete!");
}

// Помощь
void printHelp() {
  Serial.println("\n=== Commands ===");
  Serial.println("OPEN        - Open hand (all 90°)");
  Serial.println("GRIP        - Close grip");
  Serial.println("HOME        - All to 90°");
  Serial.println("STATUS      - Show current positions");
  Serial.println("SET:a,b,c,d,e - Set angles (0-180)");
  Serial.println("TEST        - Test all servos");
  Serial.println("HELP        - Show this help");
  Serial.println();
  Serial.println("Pins:");
  Serial.println("  D3  → Thumb");
  Serial.println("  D5  → Index");
  Serial.println("  D6  → Middle");
  Serial.println("  D9  → Ring");
  Serial.println("  D10 → Pinky");
  Serial.println();
}
