#!/bin/bash
# Скрипт сборки Android APK

set -e

echo "🔧 Сборка Android-приложения для роборуки..."

cd /home/tarixxk/industrial_ai_hub/android

# Создание директории для assets
mkdir -p app/src/main/assets

# Загрузка модели MediaPipe Hand Landmarker
echo "📥 Загрузка модели MediaPipe..."
MODEL_URL="https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH="app/src/main/assets/hand_landmarker.task"

if [ ! -f "$MODEL_PATH" ]; then
    curl -L -o "$MODEL_PATH" "$MODEL_URL"
    echo "✓ Модель загружена"
else
    echo "✓ Модель уже существует"
fi

# Проверка Gradle
if ! command -v gradle &> /dev/null; then
    echo "⚠️ Gradle не найден. Используем gradlew..."
    GRADLE_CMD="./gradlew"
else
    GRADLE_CMD="gradle"
fi

# Сборка Debug APK
echo "📦 Сборка APK..."
$GRADLE_CMD assembleDebug

# Результат
echo ""
echo "✅ Сборка завершена!"
echo ""
echo "📱 APK файл:"
echo "   app/build/outputs/apk/debug/app-debug.apk"
echo ""
echo "📲 Установка на устройство:"
echo "   adb install app/build/outputs/apk/debug/app-debug.apk"
echo ""
