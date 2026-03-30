# 🦾 Роборука с PCA9685 (16 сервоприводов)

## 📋 Преимущества PCA9685

| Без PCA9685 | С PCA9685 |
|-------------|-----------|
| 8 пинов Arduino | 2 пина (I2C) |
| Нагрузка на Arduino | Разгрузка |
| Дёрганье при нагрузке | Плавная работа |
| Макс 8-10 серво | До 62 серво! |
| Нет точности | 12-bit точность |

---

## 💰 Бюджет с PCA9685

| Компонент | Кол-во | Цена (₽) |
|-----------|--------|----------|
| **PCA9685 плата** | 1 | 250-350 |
| Arduino Nano | 1 | 250-400 |
| SG90 серво | 8 | 1200-1600 |
| БП 5V 3A | 1 | 300-500 |
| Провода, плата | 1 | 200-300 |
| **ИТОГО** | | **~2200-3150₽** |

---

## 🔌 Схема подключения

```
                    ┌─────────────────┐
                    │   PCA9685       │
                    │   16 каналов    │
                    │                 │
        ┌───────────┤ VCC   → 5V      │
        │           │ GND   → GND     │
        │           │ SCL   → A5      │
        │           │ SDA   → A4      │
        │           │                 │
        │           │ V+    → БП 5V   │──→ Питание серво
        │           │ GND   → БП GND  │
        │           │                 │
        │           │ 0-15  → Серво   │──→ 16 каналов
        │           └─────────────────┘
        │
        │    ┌─────────────────┐
        │    │  Arduino Nano   │
        │    │                 │
        │    │  A4 (SDA) ──────┤
        │    │  A5 (SCL) ──────┤
        │    │  5V ────────────┤ (для логики)
        │    │  GND ───────────┤
        │    └─────────────────┘
        │
        │    ┌─────────────────┐
        │    │   БП 5V 3A+     │
        │    │   (для серво)   │
        │    └─────────────────┘
```

### I2C адреса:
- **A4** = SDA (данные)
- **A5** = SCL (такт)
- Можно подключить **до 62 плат** (адреса 0x40-0x7F)

---

## 💻 Прошивка с PCA9685

### robot_arm_pca.ino

```cpp
/*
 * Роборука с PCA9685 (16 каналов)
 * Управление через Bluetooth
 */

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// I2C адрес PCA9685 (по умолчанию 0x40)
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

// Настройки серво
#define SERVOMIN  150  // Минимальная длительность (мкс × 4096 / 20000)
#define SERVOMAX  600  // Максимальная длительность
#define USMIN     500  // 500 мкс
#define USMAX     2500 // 2500 мкс
#define FREQUENCY 50   // 50 Hz для серво

// Позиции (8 серво)
int positions[8] = {90, 90, 90, 90, 90, 90, 90, 90};

// Назначение каналов PCA9685
const int servoChannels[8] = {0, 1, 2, 3, 4, 5, 6, 7};

void setup() {
  Serial.begin(9600);
  
  // Инициализация PCA9685
  pwm.begin();
  pwm.setPWMFreq(FREQUENCY);
  
  // Установка начальных позиций
  for (int i = 0; i < 8; i++) {
    setServoAngle(servoChannels[i], positions[i]);
  }
  
  delay(1000);
  Serial.println("READY");
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    if (cmd.startsWith("SET:")) {
      parseSetCommand(cmd.substring(4));
      Serial.println("OK");
    }
    else if (cmd == "HOME") {
      moveToAll(90);
      Serial.println("HOME");
    }
    else if (cmd == "GRIP") {
      // Захват
      setServoAngle(0, 45);   // Большой
      setServoAngle(1, 30);   // Указательный
      setServoAngle(2, 30);   // Средний
      setServoAngle(3, 30);   // Безымянный
      setServoAngle(4, 30);   // Мизинец
      setServoAngle(5, 90);   // Запястье
      setServoAngle(6, 120);  // Локоть
      setServoAngle(7, 90);   // Плечо
      Serial.println("GRIP");
    }
    else if (cmd == "OPEN") {
      moveToAll(90);
      Serial.println("OPEN");
    }
    else if (cmd.startsWith("POS:")) {
      // Индивидуальная позиция: POS:channel,angle
      parsePosCommand(cmd.substring(4));
      Serial.println("OK");
    }
    else if (cmd == "STATUS") {
      Serial.print("POS:");
      for (int i = 0; i < 8; i++) {
        Serial.print(positions[i]);
        if (i < 7) Serial.print(",");
      }
      Serial.println();
    }
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
    for (int i = 0; i < 8; i++) {
      positions[i] = values[i];
      setServoAngle(servoChannels[i], values[i]);
    }
  }
}

void parsePosCommand(String data) {
  int commaIndex = data.indexOf(',');
  if (commaIndex > 0) {
    int channel = data.substring(0, commaIndex).toInt();
    int angle = data.substring(commaIndex + 1).toInt();
    
    if (channel >= 0 && channel < 8) {
      positions[channel] = constrain(angle, 0, 180);
      setServoAngle(channel, positions[channel]);
    }
  }
}

void setServoAngle(uint8_t channel, uint8_t angle) {
  // Конвертация угла в длительность импульса
  uint16_t pulse = map(angle, 0, 180, SERVOMIN, SERVOMAX);
  pwm.setPWM(channel, 0, pulse);
}

void moveToAll(int angle) {
  for (int i = 0; i < 8; i++) {
    positions[i] = angle;
    setServoAngle(servoChannels[i], angle);
  }
}

// Плавное движение к позиции
void moveToSmooth(int targets[8], int duration = 1000) {
  int steps = 20;
  int delayMs = duration / steps;
  int startPositions[8];
  
  // Сохраняем текущие позиции
  for (int i = 0; i < 8; i++) {
    startPositions[i] = positions[i];
  }
  
  // Интерполяция
  for (int step = 0; step <= steps; step++) {
    for (int i = 0; i < 8; i++) {
      int pos = startPositions[i] + (targets[i] - startPositions[i]) * step / steps;
      positions[i] = pos;
      setServoAngle(servoChannels[i], pos);
    }
    delay(delayMs);
  }
}
```

### Библиотеки:
```
В Arduino IDE:
Sketch → Include Library → Manage Libraries
Найти: "Adafruit PWM Servo Driver"
Установить
```

---

## 🔧 Настройка PCA9685

### Калибровка сервоприводов

```cpp
// Тест: найти мин/макс для каждого серво
void calibrateServo(int channel) {
  Serial.println("Калибровка серво на канале " + String(channel));
  
  // Минимум
  Serial.println("Минимум (0°)...");
  pwm.setPWM(channel, 0, SERVOMIN);
  delay(2000);
  
  // Максимум
  Serial.println("Максимум (180°)...");
  pwm.setPWM(channel, 0, SERVOMAX);
  delay(2000);
  
  // Центр
  Serial.println("Центр (90°)...");
  pwm.setPWM(channel, 0, (SERVOMIN + SERVOMAX) / 2);
}
```

### Подстройка SERVO_MIN/MAX:

Разные серво имеют разные диапазоны. Настрой:

```cpp
// Для SG90 обычно:
#define SERVOMIN  135  // 0° (может быть 120-150)
#define SERVOMAX  590  // 180° (может быть 570-620)

// Тестируй и подбирай под свои серво
```

---

## 📐 Расширение до 16 серво

```cpp
// Добавь ещё 8 серво
const int servoChannels[16] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15};
int positions[16] = {90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90};

// Назначение:
// 0-7: Правая рука
// 8-15: Левая рука (или вторая рука)
```

### Две руки:

```
PCA9685 #1 (0x40):
  Каналы 0-7  → Правая рука

PCA9685 #2 (0x41):
  Каналы 0-7  → Левая рука
```

**Адреса для второй платы:**
- Замкни контакты A0 на плате (адрес 0x41)
- Или A1 (0x42), A2 (0x43), A0+A1 (0x44) и т.д.

---

## 🎯 Продвинутые функции

### 1. Сохранение позиций в EEPROM

```cpp
#include <EEPROM.h>

#define EEPROM_ADDR 0

void savePositions() {
  for (int i = 0; i < 8; i++) {
    EEPROM.write(EEPROM_ADDR + i, positions[i]);
  }
  Serial.println("Позиции сохранены");
}

void loadPositions() {
  for (int i = 0; i < 8; i++) {
    positions[i] = EEPROM.read(EEPROM_ADDR + i);
    setServoAngle(servoChannels[i], positions[i]);
  }
  Serial.println("Позиции загружены");
}
```

### 2. Предустановки (пресеты)

```cpp
// Пресеты
int preset_home[8] = {90, 90, 90, 90, 90, 90, 90, 90};
int preset_grip[8] = {45, 30, 30, 30, 30, 90, 120, 90};
int preset_point[8] = {90, 10, 90, 90, 90, 90, 90, 90};
int preset_wave[8] = {90, 90, 90, 90, 10, 90, 90, 90};

void usePreset(int preset[8]) {
  moveToSmooth(preset, 1500);
}

// В loop():
if (cmd == "PRESET:HOME") usePreset(preset_home);
if (cmd == "PRESET:GRIP") usePreset(preset_grip);
if (cmd == "PRESET:POINT") usePreset(preset_point);
if (cmd == "PRESET:WAVE") usePreset(preset_wave);
```

### 3. Запись и воспроизведение последовательностей

```cpp
#define MAX_STEPS 100

struct Step {
  int positions[8];
  int duration;
};

Step sequence[MAX_STEPS];
int stepCount = 0;
bool isRecording = false;

void startRecording() {
  stepCount = 0;
  isRecording = true;
  Serial.println("Запись началась");
}

void stopRecording() {
  isRecording = false;
  Serial.println("Запись остановлена: " + String(stepCount) + " шагов");
}

void recordStep(int duration) {
  if (isRecording && stepCount < MAX_STEPS) {
    for (int i = 0; i < 8; i++) {
      sequence[stepCount].positions[i] = positions[i];
    }
    sequence[stepCount].duration = duration;
    stepCount++;
  }
}

void playSequence() {
  Serial.println("Воспроизведение...");
  for (int i = 0; i < stepCount; i++) {
    moveToSmooth(sequence[i].positions, sequence[i].duration);
  }
  Serial.println("Воспроизведение завершено");
}
```

---

## 🔌 Подключение к Android приложению

Обновлённое приложение уже поддерживает PCA9685!

**Команды:**
- `SET:a,b,c,d,e,f,g,h` — 8 углов (0-180)
- `POS:ch,angle` — один канал
- `HOME` — все в 90°
- `GRIP` — захват
- `OPEN` — открыть
- `STATUS` — текущие позиции

---

## 📊 Сравнение: Arduino vs PCA9685

| Параметр | Arduino напрямую | PCA9685 |
|----------|------------------|---------|
| Пинов | 8 | 2 (I2C) |
| Нагрузка CPU | Высокая | Низкая |
| Точность | 8-bit | 12-bit |
| Макс серво | ~10 | 62 (с каскадом) |
| Плавность | Средняя | Отличная |
| Цена | 0₽ | +250₽ |

---

## 🛒 Где купить PCA9685

| Магазин | Цена | Ссылка |
|---------|------|--------|
| AliExpress | 250₽ | [ссылка](https://aliexpress.com/item/32835359294.html) |
| ЧипДип | 450₽ | [ссылка](https://chipdip.ru/product/pca9685) |
| Ozon | 350₽ | [ссылка](https://ozon.ru/product/pca9685) |

---

## ⚡ Схема питания (важно!)

```
БП 5V 3A ──┬──→ PCA9685 V+
           │
           ├──→ Серво VCC (все 8)
           │
           └──→ GND ──┬─→ PCA9685 GND
                      │
                      └─→ Arduino GND

USB ──→ Arduino 5V (для логики)

I2C:
Arduino A4 (SDA) ──→ PCA9685 SDA
Arduino A5 (SCL) ──→ PCA9685 SCL
```

**НЕ подключай:**
- ❌ V+ PCA9685 к 5V Arduino
- ✅ Только к внешнему БП!

---

## 🎯 Итог

**С PCA9685:**
- ✅ Плавная работа
- ✅ Не нагружает Arduino
- ✅ Можно добавить ещё серво
- ✅ Точная настройка
- ✅ Пресеты и последовательности

**Цена вопроса:** +250₽ к бюджету

**Рекомендую!** 👍
