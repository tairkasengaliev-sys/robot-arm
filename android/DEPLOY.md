# 🚀 Публикация приложения онлайн

## Способ 1: GitHub Pages (БЕСПЛАТНО) ⭐ РЕКОМЕНДУЕТСЯ

### Шаг 1: Создай репозиторий на GitHub

1. Зайди на https://github.com
2. Войди в свой аккаунт
3. Нажми **"+"** → **"New repository"**
4. Название: `robot-arm`
5. **Public** репозиторий
6. Нажми **"Create repository"**

### Шаг 2: Загрузи файлы

В терминале:

```bash
cd /home/tarixxk/industrial_ai_hub

# Инициализация Git
git init

# Добавление файлов
git add android/app.html
git add android/manifest.json
git add android/sw.js
git add android/index.html
git add .github/workflows/deploy.yml

# Коммит
git commit -m "Роборука приложение"

# Добавь удалённый репозиторий (замени username на свой)
git remote add origin https://github.com/username/robot-arm.git

# Отправка
git branch -M main
git push -u origin main
```

### Шаг 3: Включи GitHub Pages

1. Зайди в репозиторий на GitHub
2. **Settings** → **Pages**
3. **Source:** Deploy from a branch
4. **Branch:** main → **Save**

### Шаг 4: Жди ~2 минуты

Твоё приложение будет доступно по ссылке:
```
https://username.github.io/robot-arm/
```

### Шаг 5: Установи на телефон

1. Открой ссылку на телефоне
2. **Chrome** → ⋮ → **"Установить приложение"**
3. Готово! 🎉

---

## Способ 2: Netlify (БЫСТРО)

### Вариант A: Drag & Drop

1. Зайди на https://app.netlify.com/drop
2. Перетащи папку `android/` в окно
3. Получишь ссылку вида: `https://random-name.netlify.app`

### Вариант B: Через CLI

```bash
# Установка Netlify CLI
npm install -g netlify-cli

# Деплой
cd /home/tarixxk/industrial_ai_hub/android
netlify deploy --prod --dir=.
```

---

## Способ 3: Vercel

```bash
# Установка Vercel
npm install -g vercel

# Деплой
cd /home/tarixxk/industrial_ai_hub/android
vercel --prod
```

---

## Способ 4: Cloudflare Pages

1. Зайди на https://pages.cloudflare.com
2. **Create a project**
3. Подключи GitHub репозиторий
4. **Deploy**

---

## 📱 Установка на телефон (когда сайт онлайн)

### Android (Chrome):
1. Открой ссылку в Chrome
2. Нажми **⋮ (три точки)**
3. **"Установить приложение"** или **"Добавить на гл. экран"**
4. Подтверди

### iPhone (Safari):
1. Открой ссылку в Safari
2. Нажми **📤 (поделиться)**
3. **"На экран «Домой»"**
4. Подтверди

---

## ✅ Чек-лист

- [ ] Файлы в папке `android/`
- [ ] Репозиторий создан на GitHub
- [ ] Файлы загружены (`git push`)
- [ ] GitHub Pages включён в Settings
- [ ] Ссылка работает
- [ ] На телефоне открыл ссылку
- [ ] Установил как приложение

---

## 🔗 Ссылки

| Хостинг | Ссылка | Время |
|---------|--------|-------|
| GitHub Pages | `username.github.io/repo` | 1-2 мин |
| Netlify | `random.netlify.app` | 30 сек |
| Vercel | `random.vercel.app` | 30 сек |
| Cloudflare | `random.pages.dev` | 1 мин |

---

## 🛠️ Если что-то не так

**404 ошибка:**
- Проверь что `index.html` в корне папки
- Подожди 2-3 минуты после деплоя

**Не устанавливается:**
- Открой в Chrome (не Firefox/Safari)
- Проверь HTTPS (требуется для PWA)

**MediaPipe не грузится:**
- Проверь интернет
- CDN могут блокироваться, скачай локально

---

## 📞 Быстрая команда для деплоя

```bash
cd /home/tarixxk/industrial_ai_hub

# Если уже есть репозиторий
git add android/
git commit -m "Update app"
git push

# Жди 2 минуты и открывай ссылку!
```
