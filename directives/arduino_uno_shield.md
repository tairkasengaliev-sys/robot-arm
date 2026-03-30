# 🦾 Роборука на Arduino Uno + Sensor Shield V5.0

## 📋 Комплектация

| Компонент | Кол-во | Цена (₽) | Примечание |
|-----------|--------|----------|------------|
| **Arduino Uno R3** | 1 | 400-600 | Можно клон |
| **Sensor Shield V5.0** | 1 | 200-350 | Плата расширения |
| **Сервопривод SG90** | 8 | 1200-1600 | 9g микро |
| **Bluetooth HC-05** | 1 | 250-400 | Или HC-06 |
| **БП 5V 3A** | 1 | 300-500 | Для серво |
| **Провода Dupont** | 40+ | 150-250 | M-M, M-F |
| **ИТОГО** | | **~2500-3700₽** | |

---

## 🔌 Sensor Shield V5.0 — возможности

```
┌─────────────────────────────────────────────────────────┐
│              Sensor Shield V5.0                         │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  ANALOG IN (I2C)                                │   │
│  │  A0 ─┬─ VCC ─┬─ GND    ← I2C для дисплеев       │   │
│  │  A1 ─┤       └────────  ← Можно для серво       │   │
│  │  A2 ─┤  VCC ─┬─ GND                              │   │
│  │  A3 ─┤       └────────  ← Серво 6,7             │   │
│  │  A4 ─┤  VCC ─┬─ GND    ← SDA (I2C)              │   │
│  │  A5 ─┘       └────────  ← SCL (I2C)             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  DIGITAL (с PWM ~)                              │   │
│  │  D0 ─┬─ TX ───┐  ← Bluetooth RX                 │   │
│  │  D1 ─┤─ RX ───┤  ← Bluetooth TX                 │   │
│  │  D2 ─┤        │                                  │   │
│  │  D3 ─┼~ PWM ──┤  ← Серво 0 (большой)            │   │
│  │  D4 ─┤        │                                  │   │
│  │  D5 ─┼~ PWM ──┤  ← Серво 1 (указательный)       │   │
│  │  D6 ─┼~ PWM ──┤  ← Серво 2 (средний)            │   │
│  │  D7 ─┤        │                                  │   │
│  │  D8 ─┤        │                                  │   │
│  │  D9 ─┼~ PWM ──┤  ← Серво 3 (безымянный)         │   │
│  │  D10─┼~ PWM ──┤  ← Серво 4 (мизинец)            │   │
│  │  D11─┼~ PWM ──┤  ← Серво 5 (запястье)           │   │
│  │  D12─┤        │                                  │   │
│  │  D13─┤ LED    │                                  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  ПИТАНИЕ                                        │   │
│  │  VIN ────→ 7-12V (вход)                         │   │
│  │  5V  ────→ 5V выход (не для серво!)             │   │
│  │  3.3V ───→ 3.3V выход                           │   │
│  │  GND ────→ Общий                                │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Преимущества Sensor Shield:
- ✅ **Удобные разъёмы** для серво (3 пина: GND-VCC-SIG)
- ✅ **I2C разъём** для дисплеев, датчиков
- ✅ **Подписаны пины**
- ✅ **Не нужна макетная плата**
- ✅ **Компактное подключение**

---

## 🔌 Схема подключения

### Полная схема:

```
                    ┌─────────────────────┐
                    │   Arduino Uno R3    │
                    │                     │
                    │  ┌───────────────┐  │
                    │  │Sensor Shield  │  │
                    │  │    V5.0       │  │
                    │  └───────────────┘  │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   ┌────┴────┐           ┌────┴────┐           ┌────┴────┐
   │ SG90 #0 │           │ SG90 #1 │           │ SG90 #2 │
   │ D3      │           │ D5      │           │ D6      │
   │ Большой │           │ Указат. │           │ Средний │
   └────┬────┘           └────┬────┘           └────┬────┘
        │                      │                      │
   ┌────┴────┐           ┌────┴────┐           ┌────┴────┐
   │ SG90 #3 │           │ SG90 #4 │           │ SG90 #5 │
   │ D9      │           │ D10     │           │ D11     │
   │ Безым.  │           │ Мизинец │           │ Запястье│
   └────┬────┘           └────┬────┘           └────┬────┘
        │                      │                      │
   ┌────┴────┐           ┌────┴────┐                 │
   │ SG90 #6 │           │ SG90 #7 │                 │
   │ A0      │           │ A1      │                 │
   │ Локоть  │           │ Плечо   │                 │
   └────┬────┘           └────┬────┘                 │
        │                      │                      │
        └──────────────────────┴──────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │   БП 5V 3A (V+)     │
                    │   GND ──────────────┼──→ GND Arduino
                    └─────────────────────┘

        ┌──────────────────────────────────┐
        │   Bluetooth HC-05                │
        │   VCC ──→ 5V (от Arduino)        │
        │   GND ──→ GND                    │
        │   TX  ──→ D0 (RX Arduino)        │
        │   RX  ──→ D1 (TX Arduino)        │
        └──────────────────────────────────┘
```

### Подключение по пинам:

| Серво | Пин на Shield | Функция |
|-------|---------------|---------|
| #0 | D3 | Большой палец |
| #1 | D5 | Указательный |
| #2 | D6 | Средний |
| #3 | D9 | Безымянный |
| #4 | D10 | Мизинец |
| #5 | D11 | Запястье |
| #6 | A0 | Локоть |
| #7 | A1 | Плечо |

---

## 💻 Прошивка для Uno + Shield V5.0

### robot_arm_uno.ino

```cpp
/*
 * Роборука на Arduino Uno + Sensor Shield V5.0
 * 8 сервоприводов SG90
 * Управление через Bluetooth HC-05
 */

#include <Servo.h>

// Сервоприводы
Servo servos[8];

// Пины на Sensor Shield V5.0
const int servoPins[8] = {3, 5, 6, 9, 10, 11, A0, A1};

// Текущие позиции
int positions[8] = {90, 90, 90, 90, 90, 90, 90, 90};

// Названия для отладки
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
  Serial.println("Robot Arm Uno + Shield V5.0");
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
    // Захват
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
    Serial.println("  SET:a,b,c,d,e,f,g,h - Установить углы (0-180)");
    Serial.println("  HOME - Все в 90°");
    Serial.println("  GRIP - Захват");
    Serial.println("  OPEN - Открыть");
    Serial.println("  STATUS - Текущие позиции");
    Serial.println("  TEST - Тест серво");
  }
  else {
    Serial.println("Unknown command. Send HELP for list.");
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
  // Плавное движение за 20 шагов
  int steps = 20;
  int delays = 15;
  
  for (int step = 0; step < steps; step++) {
    for (int i = 0; i < 8; i++) {
      int diff = targets[i] - positions[i];
      if (abs(diff) > 0) {
        positions[i] += diff / steps;
        servos[i].write(positions[i]);
      }
    }
    delay(delays);
  }
  
  // Финальная позиция
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
  
  // Все в 0°
  Serial.println("Moving to 0°...");
  moveToAll(0);
  delay(1000);
  
  // Все в 90°
  Serial.println("Moving to 90°...");
  moveToAll(90);
  delay(1000);
  
  // Все в 180°
  Serial.println("Moving to 180°...");
  moveToAll(180);
  delay(1000);
  
  // Все в 90°
  Serial.println("Moving to 90°...");
  moveToAll(90);
  
  Serial.println("Test complete!");
}
```

---

## 🔧 Настройка Bluetooth HC-05

### Подключение:

```
HC-05      Sensor Shield V5.0
──────     ──────────────────
VCC   ────→ 5V (на цифровом пине)
GND   ────→ GND
TX    ────→ D0 (RX Uno)
RX    ────→ D1 (TX Uno)
KEY   ────→ Не подключать (или к 3.3V для режима AT)
```

### Сопряжение:

1. **Пароль:** `1234` или `0000`
2. **Имя устройства:** `HC-05`
3. **Baud rate:** `9600`

### Проверка связи:

```cpp
// Echo тест
void setup() {
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    Serial.write(Serial.read());
  }
}
```

Отправь команду из терминала — должна вернуться.

---

## 📱 Подключение Android приложения

### Через Termux (Python):

```bash
# Установка
pkg install python pyserial

# Скрипт подключения
python -c "
import serial
ser = serial.Serial('/dev/ttyACM0', 9600)
ser.write(b'SET:90,90,90,90,90,90,90,90\n')
print(ser.readline())
"
```

### Через приложение:

1. Открой https://tairkasengaliev-sys.github.io/robot-arm/
2. Нажми 📡 (Bluetooth)
3. Выбери `HC-05`
4. Введи пароль `1234`
5. Готово!

---

## ⚡ Питание

### ⚠️ ВАЖНО:

```
❌ НЕ ПРАВИЛЬНО:
БП 5V → 5V пин Arduino → Серво
         ↑
    Сгорит регулятор!

✅ ПРАВИЛЬНО:
БП 5V 3A ──┬──→ V+ всех серво (на Shield)
           │
           └──→ GND ──┬─→ GND Arduino
                      │
USB ──────────────────┴─→ Arduino (для логики)
```

### Схема питания:

```
БП 5V 3A
   │
   ├─→ V+ (питание серво через Shield)
   │
   └─→ GND ──┬─→ GND на Shield
             │
             └─→ GND Arduino (общий!)

USB кабель ──→ Arduino DC jack (5V для логики)
```

### Ток потребления:

| Состояние | Ток |
|-----------|-----|
| 1 серво без нагрузки | 100-200 mA |
| 1 серво под нагрузкой | 500-700 mA |
| 8 серво максимум | 4-5 A |

**Рекомендация:** БП **5V 3A минимум**

---

## 🧪 Тестирование

### 1. Проверка подключения:

```cpp
void setup() {
  Serial.begin(9600);
  for (int i = 0; i < 8; i++) {
    servos[i].attach(servoPins[i]);
  }
}

void loop() {
  // Поочерёдно двигаем каждое серво
  for (int i = 0; i < 8; i++) {
    Serial.print("Servo ");
    Serial.println(i);
    
    servos[i].write(0);
    delay(500);
    servos[i].write(90);
    delay(500);
    servos[i].write(180);
    delay(500);
    servos[i].write(90);
    delay(500);
  }
}
```

### 2. Проверка Bluetooth:

Открой Serial Monitor (9600 baud):
- Отправь: `STATUS`
- Ответ: `POS:90,90,90,90,90,90,90,90`

### 3. Проверка с телефона:

1. Подключись к HC-05
2. Отправь: `HOME`
3. Ответ: `HOME_OK`
4. Все серво в 90°

---

## 🛠️ Настройка сервоприводов

### Если серво дрожит:

1. Проверь питание (нужно 5V стабильно)
2. Добавь конденсатор 470uF на V+/GND
3. Проверь общий GND

### Если не двигается:

1. Проверь подключение (3 пина: GND-VCC-SIG)
2. Проверь пин в коде
3. Может серво бракованное

### Калибровка:

```cpp
// Найди мин/макс для своего серво
#define SERVOMIN 10  // Может быть 5-15
#define SERVOMAX 170 // Может быть 165-175

// В setup():
servos[0].write(SERVOMIN);
delay(1000);
servos[0].write(SERVOMAX);
delay(1000);
servos[0].write(90);
```

---

## 📐 Конструкция

### Крепление серво на Shield:

```
┌─────────────────────────────────────┐
│  Arduino Uno + Sensor Shield        │
│                                     │
│  ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ │
│  │0│ │1│ │2│ │3│ │4│ │5│ │6│ │7│ │ ← Серво
│  └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ │
│   D3 D5 D6 D9 D10D11A0 A1          │
│                                     │
│        HC-05 ───┐                  │
│                 │                  │
│  ┌──────────────┴──────────────┐   │
│  │      БП 5V 3A               │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Размещение:

- Arduino + Shield — в основании руки
- БП — рядом (можно отдельно)
- HC-05 — сверху для лучшего сигнала

---

## 🎯 Сравнение: Nano vs Uno + Shield

| Параметр | Nano | Uno + Shield V5.0 |
|----------|------|-------------------|
| Удобство | Нужна макетка | Готовые разъёмы |
| Пины | Мало | Много + подписаны |
| Цена | Дешевле | +200₽ за Shield |
| Надёжность | Провода | Надёжные коннекторы |
| Расширяемость | Ограничено | I2C, UART ready |
| Для новичков | Сложнее | ✅ Легче |

**Рекомендация:** Uno + Shield для надёжности! 👍

---

## 🛒 Где купить

| Товар | AliExpress | ЧипДип | Ozon |
|-------|------------|--------|------|
| Arduino Uno R3 | 400₽ | 800₽ | 600₽ |
| Sensor Shield V5.0 | 200₽ | 400₽ | 300₽ |
| SG90 ×8 | 1200₽ | 1600₽ | 1400₽ |
| HC-05 | 250₽ | 400₽ | 350₽ |
| БП 5V 3A | 300₽ | 500₽ | 400₽ |

**Итого на AliExpress:** ~2350₽ + доставка

---

## 📞 Команды для управления

| Команда | Формат | Пример | Ответ |
|---------|--------|--------|-------|
| SET | `SET:a,b,c,d,e,f,g,h` | `SET:90,45,30,30,30,90,120,90` | `SET_OK` |
| HOME | `HOME` | `HOME` | `HOME_OK` |
| GRIP | `GRIP` | `GRIP` | `GRIP_OK` |
| OPEN | `OPEN` | `OPEN` | `OPEN_OK` |
| STATUS | `STATUS` | `STATUS` | `POS:90,90,...` |
| TEST | `TEST` | `TEST` | Запуск теста |
| HELP | `HELP` | `HELP` | Список команд |

---

## 🚀 Быстрый старт

1. **Собери схему** по подключению выше
2. **Загрузи прошивку** robot_arm_uno.ino
3. **Подключи питание** (USB + БП 5V)
4. **Сопряги HC-05** с телефоном (пароль 1234)
5. **Открой приложение** и подключись
6. **Покажи руку** в камеру!

Готово! 🎉
