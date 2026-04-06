# zen-ref-agent — простой MVP (без автопубликации)

Этот проект помогает готовить черновики статей про AI для Дзена.

Важно:
- ✅ Есть только CLI-команды (терминал).
- ✅ Есть ручная проверка через Telegram.
- ❌ Нет автопубликации.
- ❌ Нет web-панели.
- ❌ Нет browser automation.

---

## 1) Что делает проект

1. Читает RSS-новости по AI/tech.
2. Сохраняет новости в SQLite.
3. Генерирует идеи статей.
4. Ставит риск (`low` / `medium` / `high`).
5. Создает черновик статьи.
6. Отправляет черновик в Telegram на ручной review.

---

## 2) Самый простой запуск (для новичка)

### Шаг 1. Откройте терминал в папке проекта

Папка должна быть `referral-agent`.

### Шаг 2. Создайте виртуальное окружение

**Linux/macOS**
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Шаг 3. Установите зависимости

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 4. Создайте файл `.env`

```bash
cp .env.example .env
```

Windows:
```powershell
copy .env.example .env
```

### Шаг 5. Откройте `.env` и заполните значения

Обязательные поля:
- `OPENAI_API_KEY` — ключ OpenAI (если пусто, будет fallback-режим)
- `OPENAI_MODEL` — модель, например `gpt-4o-mini`
- `TELEGRAM_BOT_TOKEN` — токен Telegram-бота
- `TELEGRAM_CHAT_ID` — id чата для отправки черновика
- `DB_PATH` — путь к SQLite базе (можно оставить по умолчанию)

См. пример в `.env.example`.

---

## 3) Все CLI-команды

### 3.1 Импорт новостей + генерация идей

```bash
python -m app.cli research
```

Что делает:
- Инициализирует SQLite-схему.
- Забирает RSS-новости.
- Сохраняет `source_items`.
- Генерирует и сохраняет `ideas`.

### 3.2 Показать идеи

```bash
python -m app.cli list-ideas
```

### 3.3 Создать черновик из идеи

```bash
python -m app.cli draft --idea-id 1
```

### 3.4 Отправить черновик в Telegram

```bash
python -m app.cli send-telegram --draft-id 1
```

---

## 4) Как понять, что всё работает

### Проверка RSS импорта
1. Запустите: `python -m app.cli research`
2. Убедитесь, что в выводе есть строки вида:
   - `Прочитано элементов из RSS: ...`
   - `Сохранено source_items: ...`

### Проверка генерации идей
1. Запустите: `python -m app.cli list-ideas`
2. Должен появиться список с `risk=...` и заголовками идей.

### Проверка создания черновика
1. Возьмите `idea_id` из `list-ideas`.
2. Запустите: `python -m app.cli draft --idea-id N`
3. Должно появиться: `Черновик создан. draft_id=..., risk=...`

### Проверка отправки в Telegram
1. Убедитесь, что в `.env` заполнены `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`.
2. Запустите: `python -m app.cli send-telegram --draft-id N`
3. Проверьте, что сообщение пришло в нужный чат.

---

## 5) Финальный чеклист (коротко)

- **Что редактировать первым:** файл `.env`.
- **Какую команду запускать первой:** `python -m app.cli research`.
- **Как проверить импорт RSS:** в выводе `research` должны быть счетчики `source_items`.
- **Как проверить генерацию идей:** команда `python -m app.cli list-ideas` показывает список идей.
- **Как проверить Telegram:** команда `python -m app.cli send-telegram --draft-id N` и сообщение в чате.

---

## 6) Ограничения MVP

- Нет автопостинга в Дзен.
- Нет web UI.
- Нет массового спама или агрессивных продаж.
- Публикация — только вручную после проверки человеком.
