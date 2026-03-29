/*
 * Роборука на Arduino - управление сервоприводами
 * 
 * Схема подключения:
 * - Сервопривод 1: Большой палец (pin 3)
 * - Сервопривод 2: Указательный палец (pin 5)
 * - Сервопривод 3: Средний палец (pin 6)
 * - Сервопривод 4: Безымянный палец (pin 9)
 * - Сервопривод 5: Мизинец (pin 10)
 * - Сервопривод 6: Запястье (pin 11)
 * - Сервопривод 7: Локоть (pin A0)
 * - Сервопривод 8: Плечо (pin A1)
 * 
 * Управление через Serial (Python скрипт)
 */

#include <Servo.h>

// Сервоприводы
Servo thumb;      // Большой палец
Servo index;      // Указательный
Servo middle;     // Средний
Servo ring;       // Безымянный
Servo pinky;      // Мизинец
Servo wrist;      // Запястье
Servo elbow;      // Локоть
Servo shoulder;   // Плечо

// Позиции
int pos_thumb = 90;
int pos_index = 90;
int pos_middle = 90;
int pos_ring = 90;
int pos_pinky = 90;
int pos_wrist = 90;
int pos_elbow = 90;
int pos_shoulder = 90;

// Границы углов
const int MIN_ANGLE = 0;
const int MAX_ANGLE = 180;

void setup() {
  Serial.begin(9600);
  
  // Подключение сервоприводов
  thumb.attach(3);
  index.attach(5);
  middle.attach(6);
  ring.attach(9);
  pinky.attach(10);
  wrist.attach(11);
  elbow.attach(A0);
  shoulder.attach(A1);
  
  // Начальная позиция - "открытая ладонь"
  moveToPosition(90, 90, 90, 90, 90, 90, 90, 90);
  
  Serial.println("READY");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    // Парсинг команды: "TH,IN,MI,RI,PI,WR,EL,SH"
    parseCommand(command);
  }
}

void parseCommand(String cmd) {
  if (cmd.startsWith("SET:")) {
    cmd = cmd.substring(4);
    
    int positions[8];
    int index = 0;
    int start = 0;
    
    for (int i = 0; i <= cmd.length() && index < 8; i++) {
      if (i == cmd.length() || cmd.charAt(i) == ',') {
        String val = cmd.substring(start, i);
        positions[index++] = val.toInt();
        start = i + 1;
      }
    }
    
    if (index == 8) {
      moveToPosition(
        positions[0], positions[1], positions[2], positions[3],
        positions[4], positions[5], positions[6], positions[7]
      );
      Serial.println("OK");
    }
  }
  else if (cmd == "HOME") {
    moveToPosition(90, 90, 90, 90, 90, 90, 90, 90);
    Serial.println("HOME_OK");
  }
  else if (cmd == "GRIP") {
    // Захват - все пальцы сжимаются
    moveToPosition(45, 30, 30, 30, 30, 90, 90, 90);
    Serial.println("GRIP_OK");
  }
  else if (cmd == "OPEN") {
    // Открыть ладонь
    moveToPosition(90, 90, 90, 90, 90, 90, 90, 90);
    Serial.println("OPEN_OK");
  }
  else if (cmd == "STATUS") {
    Serial.printf("POS:%d,%d,%d,%d,%d,%d,%d,%d\n",
      pos_thumb, pos_index, pos_middle, pos_ring,
      pos_pinky, pos_wrist, pos_elbow, pos_shoulder);
  }
}

void moveToPosition(int t, int i, int m, int r, int p, int w, int e, int s) {
  // Ограничение углов
  t = constrain(t, MIN_ANGLE, MAX_ANGLE);
  i = constrain(i, MIN_ANGLE, MAX_ANGLE);
  m = constrain(m, MIN_ANGLE, MAX_ANGLE);
  r = constrain(r, MIN_ANGLE, MAX_ANGLE);
  p = constrain(p, MIN_ANGLE, MAX_ANGLE);
  w = constrain(w, MIN_ANGLE, MAX_ANGLE);
  e = constrain(e, MIN_ANGLE, MAX_ANGLE);
  s = constrain(s, MIN_ANGLE, MAX_ANGLE);
  
  // Плавное движение
  int steps = 20;
  int d_thumb = (t - pos_thumb) / steps;
  int d_index = (i - pos_index) / steps;
  int d_middle = (m - pos_middle) / steps;
  int d_ring = (r - pos_ring) / steps;
  int d_pinky = (p - pos_pinky) / steps;
  int d_wrist = (w - pos_wrist) / steps;
  int d_elbow = (e - pos_elbow) / steps;
  int d_shoulder = (s - pos_shoulder) / steps;
  
  for (int step = 0; step < steps; step++) {
    pos_thumb += d_thumb;
    pos_index += d_index;
    pos_middle += d_middle;
    pos_ring += d_ring;
    pos_pinky += d_pinky;
    pos_wrist += d_wrist;
    pos_elbow += d_elbow;
    pos_shoulder += d_shoulder;
    
    thumb.write(pos_thumb);
    index.write(pos_index);
    middle.write(pos_middle);
    ring.write(pos_ring);
    pinky.write(pos_pinky);
    wrist.write(pos_wrist);
    elbow.write(pos_elbow);
    shoulder.write(pos_shoulder);
    
    delay(15);
  }
  
  // Финальная позиция
  pos_thumb = t;
  pos_index = i;
  pos_middle = m;
  pos_ring = r;
  pos_pinky = p;
  pos_wrist = w;
  pos_elbow = e;
  pos_shoulder = s;
  
  thumb.write(pos_thumb);
  index.write(pos_index);
  middle.write(pos_middle);
  ring.write(pos_ring);
  pinky.write(pos_pinky);
  wrist.write(pos_wrist);
  elbow.write(pos_elbow);
  shoulder.write(pos_shoulder);
  
  delay(100);
}
