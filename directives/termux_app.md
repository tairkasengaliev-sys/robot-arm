# Роборука на Android через Termux 🦾📱

## 📲 Установка на Android

### Шаг 1: Установить Termux
Скачайте **Termux** из F-Droid (не из Play Store - там устаревшая версия):
- https://f-droid.org/packages/com.termux/

### Шаг 2: Установка зависимостей

Откройте Termux и выполните:

```bash
# Обновление пакетов
pkg update && pkg upgrade

# Установка Python и зависимостей
pkg install python opencv-python-headless numpy

# Установка библиотек
pip install mediapipe pyserial

# Скачивание скрипта
cd ~
mkdir -p industrial_ai_hub
# Скопируйте robot_arm_mobile.py в эту папку
```

### Шаг 3: Разрешения

```bash
# Дать доступ к камере
termux-setup-storage
pkg install termux-api
termux-camera-info
```

## 🚀 Запуск

```bash
cd ~/industrial_ai_hub
python robot_arm_mobile.py
```

## 📋 Функции

| Клавиша | Действие |
|---------|----------|
| `Q` | Выход |
| `H` | Домашняя позиция |
| `G` | Захват |
| `O` | Открыть ладонь |
| `C` | Подключить Arduino |

## 🔌 Подключение к Arduino

### Вариант 1: USB OTG кабель
```
Телефон → USB OTG → Arduino USB кабель → Arduino
```

Порт: `/dev/ttyACM0`

### Вариант 2: Bluetooth HC-05/HC-06
```bash
# Сопряжение в Termux
termux-bluetooth
# Или через настройки Android

# Подключение
rfcomm connect /dev/rfcomm0 <MAC_адрес>
```

Порт: `/dev/rfcomm0`

## 📺 Интерфейс

```
┌─────────────────────────────────┐
│  [Камера с рукой]    🦾 РОБОРУКА│
│                       👍 Большой│
│  Рука видна         ☝️ Указат...│
│                       🖕 Средний│
│                       ...       │
│                                 │
│  Q - Выход           CONNECTED  │
│  H - Домой                      │
│  G - Захват                     │
│  O - Открыть                    │
│  C - Подключить                 │
└─────────────────────────────────┘
```

## 🛠️ Настройка

### Если камера не работает:
Измените в скрипте строку:
```python
cap = cv2.VideoCapture(1)  # Попробовать 0 или 1
```

### Если Arduino не подключается:
Проверьте порт:
```bash
ls /dev/tty*
```

### Настройка чувствительности:
В функции `calculate_angles()`:
- `max_open = 0.15` - чувствительность пальцев
- Коэффициенты 60, 40 для запястья/локтя

## 📦 requirements.txt для Termux

```
mediapipe>=0.10.0
pyserial>=3.5
numpy>=1.24.0
opencv-python-headless>=4.8.0
```

## 🔋 Оптимизация батареи

Для экономии батареи уменьшите разрешение камеры:
```python
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
```

## 🎯 Как это работает

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Камера  │ ──→ │ MediaPipe│ ──→ │  Python  │ ──→ │ Arduino  │
│ Android  │     │  Hands   │     │  (углы)  │     │ (серво)  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

1. Камера телефона захватывает видео
2. MediaPipe распознаёт 21 точку руки
3. Python вычисляет углы для 8 сервоприводов
4. Команды отправляются на Arduino через USB/Bluetooth

## 🐛 Решение проблем

**"No module named 'mediapipe'"**
```bash
pip install mediapipe
```

**"Permission denied"**
```bash
# Дать разрешения в настройках Android
Настройки → Приложения → Termux → Разрешения → Камера, USB
```

**"Cannot open camera"**
```bash
# Закройте другие приложения использующие камеру
# Перезапустите Termux
```

## 📈 Тестирование без Arduino

Запустите скрипт без подключения - он будет работать в режиме симуляции:
```
[SIM] SET:90,90,90,90,90,90,90,90
```

## 🚀 Следующие шаги

- [ ] Добавить сохранение пресетов
- [ ] Управление жестами (кулак = захват)
- [ ] Голосовые команды
- [ ] WiFi управление через ESP32
