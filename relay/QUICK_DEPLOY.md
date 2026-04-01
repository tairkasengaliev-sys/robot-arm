# 🚀 Быстрый деплой Relay на Railway

## 📋 Шаг 1: Создай репозиторий для Relay

```bash
# Создай НОВЫЙ репозиторий на GitHub
# Например: robot-arm-relay

cd /home/tarixxk/industrial_ai_hub

# Создай папку для relay репозитория
mkdir -p ~/robot-arm-relay
cd ~/robot-arm-relay

# Скопируй файлы
cp ../industrial_ai_hub/relay/relay.js .
cp ../industrial_ai_hub/relay/package.json .

# Инициализируй Git
git init
git add .
git commit -m "Relay server"

# Создай репозиторий на github.com и выполни:
# git remote add origin https://github.com/username/robot-arm-relay.git
# git push -u origin main
```

---

## 📋 Шаг 2: Задеплой на Railway

1. **Зайди на** https://railway.app
2. **New Project** → **Deploy from GitHub**
3. **Выбери репозиторий** `robot-arm-relay`
4. **Жди** (~1 минута)
5. **Скопируй URL**:
   - Settings → Domains
   - Или: `railway logs` в CLI
   - URL вида: `wss://robot-arm-relay-xyz.up.railway.app`

---

## 📋 Шаг 3: Обнови URL

### В web_control.html:

```bash
cd /home/tarixxk/industrial_ai_hub
```

Найди строку (примерно 140):
```javascript
const RELAY_URL = "wss://твой-relay.railway.app";
```

Замени на свой:
```javascript
const RELAY_URL = "wss://robot-arm-relay-xyz.up.railway.app";
```

### В laptop_client.py (или client.py):

Найди строку (примерно 18):
```python
RELAY_URL = "wss://твой-relay.railway.app"
```

Замени на свой URL.

---

## 📋 Шаг 4: Запусти клиент на ноутбуке

```bash
# Установи зависимости
pip3 install websocket-client pyserial

# Запусти
cd /home/tarixxk/industrial_ai_hub/relay
python3 laptop_client.py
```

Или используй новый `client.py`:

```bash
# Создай client.py в relay/
cd /home/tarixxk/industrial_ai_hub/relay

# Запусти
python3 client.py
```

---

## 📋 Шаг 5: Открой веб-интерфейс

### Вариант A: Локально
```bash
# Просто открой файл в браузере
firefox web_control.html
# или
google-chrome web_control.html
```

### Вариант B: GitHub Pages
```bash
# Скопируй в корень проекта
cp relay/web_control.html ../web_control.html

# Закоммить и запуш
cd ..
git add web_control.html
git commit -m "Update web control"
git push
```

Открой: https://username.github.io/robot-arm/web_control.html

---

## ✅ Проверка

1. **Relay на Railway:** ✅ (зелёный в Railway dashboard)
2. **Клиент запущен:** ✅ (пишет "✅ Онлайн!")
3. **Веб-интерфейс:** ✅ (видит "Ноутбук онлайн ✅")
4. **Arduino подключена:** ✅ (серво двигаются)

---

## 🎯 Команды для проверки

```bash
# Проверить Relay
curl https://robot-arm-relay-xyz.up.railway.app

# Проверить клиента (в другом терминале)
wscat -c wss://robot-arm-relay-xyz.up.railway.app

# Посмотреть логи Railway
railway logs
```

---

## 🐛 Если что-то не так

**Relay не работает:**
```bash
railway login
railway logs
```

**Клиент не подключается:**
- Проверь URL (должен быть `wss://`)
- Проверь firewall
- Попробуй `ping railway.app`

**Веб не видит клиента:**
- Открой консоль (F12)
- Проверь WebSocket статус
- Перезагрузи страницу

---

## 💡 Советы

- Railway бесплатно даёт $5 кредитов/мес (хватит на Relay)
- Relay сервер почти не использует ресурсы
- Можно добавить переменные окружения в Railway

---

## 📞 Структура

```
robot-arm-relay (GitHub)
├── relay.js       # Relay сервер
└── package.json   # Зависимости

industrial_ai_hub (GitHub)
├── relay/
│   ├── laptop_client.py  # Клиент на ноутбуке
│   └── web_control.html  # Веб-интерфейс
└── arduino/
    └── robot_hand_5fingers.ino  # Прошивка
```

Всё! 🎉
