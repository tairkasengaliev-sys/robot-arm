# Android-приложение для роборуки 🦾

## 📱 Возможности

- **Распознавание руки** через камеру телефона (MediaPipe)
- **Управление сервоприводами** по Bluetooth
- **Ручное управление** через слайдеры
- **Быстрые команды**: Домой, Захват, Открыть

## 🔧 Требования

- Android Studio Hedgehog (2023.1.1) или новее
- Android SDK 24+
- Телефон с камерой и Bluetooth

## 📦 Сборка APK

### Способ 1: Android Studio
1. Откройте папку `android/` в Android Studio
2. Скачайте модель MediaPipe:
   - https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
   - Положите в `app/src/main/assets/hand_landmarker.task`
3. Build → Build Bundle(s) / APK(s) → Build APK(s)

### Способ 2: Командная строка
```bash
cd android

# Скачать модель
mkdir -p app/src/main/assets
wget https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task -O app/src/main/assets/hand_landmarker.task

# Сборка
./gradlew assembleDebug

# APK будет в: app/build/outputs/apk/debug/app-debug.apk
```

## 📲 Установка на телефон

1. Включите "Неизвестные источники" в настройках телефона
2. Подключите телефон по USB
3. ```bash
   adb install app/build/outputs/apk/debug/app-debug.apk
   ```
4. Или отправьте APK на телефон и установите вручную

## 🎮 Использование

1. **Запустите приложение**
2. **Разрешите доступ** к камере и Bluetooth
3. **Подключитесь к Arduino**:
   - Нажмите "BT" → выберите устройство
   - Arduino должен быть с Bluetooth модулем (HC-05/HC-06)
4. **Покажите руку в камеру** → роборука повторяет движения

## 🔌 Схема подключения Arduino + Bluetooth

```
Arduino Nano/Uno:
- TX (D1) → RX Bluetooth HC-05
- RX (D0) → TX Bluetooth HC-05
- 5V → VCC Bluetooth HC-05
- GND → GND Bluetooth HC-05

Сервоприводы:
- Как в основной инструкции (robot_arm.md)
```

## 📁 Структура проекта

```
android/
├── app/
│   ├── src/main/
│   │   ├── java/com/robotarm/
│   │   │   └── MainActivity.kt      # Основной код
│   │   ├── res/
│   │   │   ├── layout/
│   │   │   │   └── activity_main.xml  # UI
│   │   │   └── values/
│   │   │       ├── strings.xml
│   │   │       └── themes.xml
│   │   ├── assets/
│   │   │   └── hand_landmarker.task  # MediaPipe модель
│   │   └── AndroidManifest.xml
│   └── build.gradle.kts
└── build.gradle.kts
```

## 🛠️ Настройка

### Изменение чувствительности
В `MainActivity.kt`, функция `calculateServoAngles()`:
- `maxOpen = 0.15f` — чувствительность пальцев
- Коэффициенты 60, 40 для запястья/локтя

### Добавление новых команд
В `sendCommand()` добавьте обработку своих команд

## 🐛 Решение проблем

**Камера не работает:**
- Проверьте разрешения в настройках приложения
- Перезапустите приложение

**Bluetooth не подключается:**
- Включите Bluetooth на телефоне
- Проверьте, что Arduino с Bluetooth модулем включён
- Расстояние < 10 метров

**Рука не распознаётся:**
- Хорошее освещение
- Покажите ладонь полностью
- Расстояние 20-50 см от камеры

## 📊 Как это работает

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│   Камера    │ ──→ │  MediaPipe   │ ──→ │   Android    │ ──→ │  Bluetooth  │
│  (телефон)  │     │  Hand Tracker│     │  (углы)      │     │  (HC-05)    │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
                                                                   │
                                                                   ▼
                                                            ┌─────────────┐
                                                            │   Arduino   │
                                                            │ (сервоприводы)│
                                                            └─────────────┘
```

## 🚀 Следующие шаги

- [ ] Сохранение пресетов позиций
- [ ] Управление жестами (сжатие кулака = захват)
- [ ] Обратная связь (вибрация при захвате)
- [ ] WiFi управление (ESP32 вместо Bluetooth)
