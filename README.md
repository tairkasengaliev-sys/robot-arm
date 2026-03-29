# Industrial AI Hub

Проект с 3-слойной архитектурой для надежной автоматизации задач.

## Структура

```
industrial_ai_hub/
├── directives/      # Layer 1: Инструкции (SOP в Markdown)
├── execution/       # Layer 3: Детерминированные Python скрипты
├── .tmp/            # Временные файлы (не коммитить)
├── .env             # Переменные окружения и API ключи
├── credentials.json # Google OAuth credentials
├── token.json       # Google OAuth token (автогенерируется)
└── AGENTS.md        # Основная документация
```

## Архитектура

| Layer | Назначение | Расположение |
|-------|------------|--------------|
| **1. Directive** | Что делать (цели, inputs/outputs) | `directives/*.md` |
| **2. Orchestration** | Принятие решений (AI агент) | — |
| **3. Execution** | Как делать (детерминированный код) | `execution/*.py` |

## Быстрый старт

1. Настройте `.env` с вашими API ключами
2. Добавьте Google OAuth credentials в `credentials.json`
3. Создайте директиву в `directives/`
4. Запустите соответствующий скрипт из `execution/`

## Принципы

- **Проверка инструментов**: Сначала проверяй `execution/`, потом пиши новый скрипт
- **Self-annealing**: Ошибки → фикс → обновление инструмента → тест → обновление директивы
- **Живые директивы**: Обновляй директивы по мере получения опыта

## Deliverables vs Intermediates

- **Deliverables**: Google Sheets, Slides (облачные, доступные пользователю)
- **Intermediates**: `.tmp/` (временные, регенерируемые)
