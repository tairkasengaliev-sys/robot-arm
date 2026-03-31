/*
 * Роборука - 5 пальцев (кисть)
 * Arduino Uno
 * 
 * Подключение:
 * D3  → Большой палец
 * D5  → Указательный
 * D6  → Средний
 * D9  → Безымянный
 * D10 → Мизинец
 */

#include <Servo.h>

// 5 сервоприводов для пальцев
Servo servos[5];

// Пины на Arduino Uno
const int servoPins[5] = {3, 5, 6, 9, 10};

// Названия пальцев
const char* fingerNames[5] = {
  "Thumb", "Index", "Middle", "Ring", "Pinky"
};

// Текущие позиции (90° = открытая ладонь)
int positions[5] = {90, 90, 90, 90, 90};

// Объявление функций (чтобы компилятор видел)
void moveTo(int targets[5], int duration);
void openHand();
void grip();
void wave();
void testServos();
void parseSetCommand(String data);
void parseFingerCommand(String data);
void processCommand(String cmd);
void printHelp();

void setup() {
  Serial.begin(9600);
  
  Serial.println("=== Robot Hand - 5 Fingers ===");
  Serial.println("Initializing servos...");
  
  // Инициализация сервоприводов
  for (int i = 0; i < 5; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(positions[i]);
    delay(100);
    Serial.print(fingerNames[i]);
    Serial.println(" OK");
  }
  
  Serial.println("\nREADY!");
  Serial.println("Commands: OPEN | GRIP | WAVE | SET:a,b,c,d,e | STATUS");
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
  else if (cmd == "WAVE") {
    wave();
    Serial.println("WAVE_OK");
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
  else if (cmd.startsWith("FINGER:")) {
    parseFingerCommand(cmd.substring(7));
  }
  else if (cmd == "HELP") {
    printHelp();
  }
  else if (cmd == "TEST") {
    testServos();
  }
  else {
    Serial.println("Unknown command. Send HELP for list.");
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

// Помахать рукой
void wave() {
  Serial.println("Waving...");
  
  for (int wave = 0; wave < 3; wave++) {
    // Открыть
    int open[5] = {90, 90, 90, 90, 10};
    moveTo(open, 300);
    delay(200);
    
    // Закрыть
    int close[5] = {90, 90, 90, 90, 80};
    moveTo(close, 300);
    delay(200);
  }
  
  openHand();
}

// Установка всех позиций
void moveTo(int targets[5], int duration) {
  int steps = 20;
  int delayMs = duration / steps;
  
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
  delay(100);
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
    Serial.println("ERROR: Need 5 values (thumb,index,middle,ring,pinky)");
  }
}

// Управление отдельным пальцем: FINGER:num,angle
void parseFingerCommand(String data) {
  int commaIndex = data.indexOf(',');
  if (commaIndex > 0) {
    int fingerNum = data.substring(0, commaIndex).toInt();
    int angle = data.substring(commaIndex + 1).toInt();
    
    if (fingerNum >= 0 && fingerNum < 5) {
      angle = constrain(angle, 0, 180);
      positions[fingerNum] = angle;
      servos[fingerNum].write(angle);
      Serial.print("FINGER ");
      Serial.print(fingerNum);
      Serial.print(" (");
      Serial.print(fingerNames[fingerNum]);
      Serial.print(") = ");
      Serial.print(angle);
      Serial.println("° OK");
    } else {
      Serial.println("ERROR: Finger number must be 0-4");
    }
  } else {
    Serial.println("ERROR: Use FINGER:num,angle");
  }
}

// Тест сервоприводов
void testServos() {
  Serial.println("\n=== Servo Test ===");
  
  // Все в 0°
  Serial.println("Moving all to 0°...");
  int zero[5] = {0, 0, 0, 0, 0};
  moveTo(zero, 1500);
  delay(1000);
  
  // Все в 90°
  Serial.println("Moving all to 90°...");
  int center[5] = {90, 90, 90, 90, 90};
  moveTo(center, 1500);
  delay(1000);
  
  // Все в 180°
  Serial.println("Moving all to 180°...");
  int max[5] = {180, 180, 180, 180, 180};
  moveTo(max, 1500);
  delay(1000);
  
  // Все в 90°
  Serial.println("Moving all to 90°...");
  moveTo(center, 1500);
  
  Serial.println("\nTest complete!");
}

// Помощь
void printHelp() {
  Serial.println("\n=== Commands ===");
  Serial.println("OPEN        - Open hand (all 90°)");
  Serial.println("GRIP        - Close grip");
  Serial.println("WAVE        - Wave hand");
  Serial.println("STATUS      - Show current positions");
  Serial.println("SET:a,b,c,d,e - Set angles (0-180)");
  Serial.println("            (thumb,index,middle,ring,pinky)");
  Serial.println("FINGER:n,a  - Set single finger (n=0-4, a=0-180)");
  Serial.println("TEST        - Test all servos");
  Serial.println("HELP        - Show this help");
  Serial.println();
  Serial.println("Finger numbers:");
  Serial.println("  0 = Thumb (D3)");
  Serial.println("  1 = Index (D5)");
  Serial.println("  2 = Middle (D6)");
  Serial.println("  3 = Ring (D9)");
  Serial.println("  4 = Pinky (D10)");
  Serial.println();
}
