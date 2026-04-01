# 🚀 Деплой Relay сервера на Railway

## Шаг 1: Установи Railway CLI

```bash
# Linux/Mac
curl -fsSL https://railway.app/install.sh | bash

# Или через npm
npm install -g @railway/cli
```

## Шаг 2: Авторизуйся

```bash
railway login
```

## Шаг 3: Задеплой Relay

```bash
cd /home/tarixxk/industrial_ai_hub/relay

# Инициализация проекта
railway init

# Деплой
railway up
```

## Шаг 4: Узнай URL

```bash
railway domain
```

Получишь что-то вроде: `robot-relay-xyz.railway.app`

## Шаг 5: Обнови URL в файлах

**web_control.html** (строка ~140):
```javascript
const RELAY_URL = "wss://robot-relay-xyz.railway.app";
```

**laptop_client.py** (строка ~18):
```python
RELAY_URL = "wss://robot-relay-xyz.railway.app"
```

## Шаг 6: Запусти ноутбук клиент

```bash
# Установи зависимости
pip3 install websocket-client pyserial

# Запусти
cd /home/tarixxk/industrial_ai_hub/relay
python3 laptop_client.py
```

## Шаг 7: Открой веб-интерфейс

Открой `web_control.html` в браузере (можно прямо с GitHub Pages):

```bash
# Или скопируй в основной проект
cp relay/web_control.html ../web_control.html
```

---

## 📊 Архитектура

```
┌─────────────┐     WebSocket      ┌─────────────┐
│   Телефон   │ ◄────────────────► │   Railway   │
│   (браузер) │     wss://         │   (Relay)   │
└─────────────┘                    └──────┬──────┘
                                          │
                            WebSocket     │
                            ┌─────────────┘
                            │
                     ┌──────▼──────┐     USB      ┌─────────────┐
                     │   Ноутбук   │ ◄──────────► │   Arduino   │
                     │  (клиент)   │              │   (серво)   │
                     └─────────────┘              └─────────────┘
```

---

## ✅ Проверка

1. **Relay на Railway:** ✅ (зелёный статус)
2. **Ноутбук клиент:** ✅ (пишет "Relay: подключено")
3. **Веб-интерфейс:** ✅ (видит "Ноутбук онлайн")
4. **Arduino:** ✅ (серво двигаются)

---

## 🐛 Решение проблем

**Relay не подключается:**
```bash
# Проверь логи на Railway
railway logs
```

**Ноутбук не видит Arduino:**
```bash
# Проверь порт
ls /dev/ttyUSB* /dev/ttyACM*
```

**Веб не видит Relay:**
- Открой консоль браузера (F12)
- Проверь WebSocket подключение

---

## 💰 Railway тарифы

- **Бесплатно:** $5/мес кредит (хватит для Relay)
- **Платно:** от $5/мес

Relay потребляет мало ресурсов, хватит бесплатного!
