#!/bin/bash
# Автоматический деплой роборуки на GitHub Pages
# Запуск: ./deploy.sh

set -e

echo "=========================================="
echo "🦾 Деплой приложения Роборука"
echo "=========================================="
echo ""

# Проверка Git
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен. Установи: sudo apt install git"
    exit 1
fi

# Проверка GitHub CLI
if command -v gh &> /dev/null; then
    HAS_GH=true
    echo "✓ GitHub CLI найден"
else
    HAS_GH=false
    echo "⚠ GitHub CLI не найден (опционально)"
fi

echo ""
echo "📁 Проект: /home/tarixxk/industrial_ai_hub"
echo ""

cd /home/tarixxk/industrial_ai_hub

# Проверка репозитория
if git remote -v | grep -q origin; then
    echo "✓ Репозиторий уже настроен"
    REMOTE_URL=$(git remote get-url origin)
    echo "  URL: $REMOTE_URL"
else
    echo "⚠ Репозиторий не настроен"
    echo ""
    
    if [ "$HAS_GH" = true ]; then
        echo "📝 Введите название репозитория (например: robot-arm):"
        read REPO_NAME
        
        if [ -z "$REPO_NAME" ]; then
            REPO_NAME="robot-arm"
        fi
        
        echo ""
        echo "📤 Создание репозитория на GitHub..."
        gh repo create "$REPO_NAME" --public --source=. --remote=origin --push
        
        echo ""
        echo "✅ Репозиторий создан!"
        echo ""
        
        # Включение GitHub Pages через API
        echo "🔧 Настройка GitHub Pages..."
        REPO_OWNER=$(gh api user | jq -r .login)
        gh api \
            --method PUT \
            /repos/$REPO_OWNER/$REPO_NAME/pages \
            -f source='{"branch":"main","path":"/"}' || true
        
        echo ""
        echo "=========================================="
        echo "🎉 Деплой завершён!"
        echo "=========================================="
        echo ""
        echo "📱 Ссылка на приложение (через 2-3 мин):"
        echo "   https://$REPO_OWNER.github.io/$REPO_NAME/"
        echo ""
        echo "📲 Установка на телефон:"
        echo "   1. Открой ссылку в Chrome"
        echo "   2. ⋮ → 'Установить приложение'"
        echo "   3. Готово!"
        echo ""
        exit 0
    else
        echo "❌ Нужен GitHub CLI для автоматического создания"
        echo ""
        echo "📦 Установка: sudo apt install gh"
        echo "   или: brew install gh"
        echo ""
        echo "🔐 Авторизация: gh auth login"
        echo ""
        echo "Или создай репозиторий вручную на github.com"
        echo "Затем выполни:"
        echo ""
        echo "   git remote add origin https://github.com/USERNAME/REPO.git"
        echo "   git push -u origin main"
        echo ""
        exit 1
    fi
fi

# Если репозиторий уже есть - просто пушим
echo ""
echo "📤 Отправка изменений на GitHub..."
git push -u origin main

echo ""
echo "=========================================="
echo "🎉 Готово!"
echo "=========================================="
echo ""
echo "📱 Проверь репозиторий на GitHub:"
echo "   Settings → Pages → Включи main branch"
echo ""
echo "🔗 Ссылка появится через 2-3 минуты"
echo ""
