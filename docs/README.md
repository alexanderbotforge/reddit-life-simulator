# Reddit Life Simulator — документация

**Версия проекта:** 1.0.3  
**Последнее обновление:** 2025-02-01  

---

## О проекте

Reddit Life Simulator (RLS) — автономная система долгосрочной имитации «жизни» Reddit-аккаунтов. Поведение аккаунтов визуально и поведенчески неотличимо от человеческого. Подробнее см. [tehzadanie.txt](../tehzadanie.txt) и [knowledge_base](../knowledge_base/).

---

## Структура кода (корень проекта)

| Файл | Назначение |
|------|------------|
| **rls.py** | Главная точка входа: очередь жизни, CLI (`--config-dir`, `--state-dir`, `--dry-run`, `--send-daily-report`, `--daemon`). |
| **constants.py** | Константы и лимиты v1.0 (версия, upvote/подписки за сессию, статусы, cooldown, каталоги). |
| **config.py** | Конфигурация аккаунтов: загрузка JSON, очередь жизни, валидация прокси, маскировка в логах. |
| **state.py** | Состояние по аккаунту и сводный файл для отчётности. |
| **browser.py** | Браузерная эмуляция (Playwright): профиль, прокси, Reddit, скролл, upvote, подписка, детекция рисков. |
| **behavior.py** | Поведенческая модель: усталость, ритм по таймзоне аккаунта, длительность сессии, лимиты действий. |
| **risk.py** | Контроль рисков: cooldown, накопительный уровень риска. |
| **reporting.py** | Ежедневный отчёт и отправка в Telegram (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID). |

---

## Запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Установка браузера для Playwright (один раз)
playwright install chromium

# Запуск одного цикла очереди жизни (dry-run — без браузера)
python rls.py --dry-run

# Запуск с реальным браузером (нужны конфиги аккаунтов в config/)
python rls.py --config-dir config --state-dir state

# Показать окно браузера (иначе браузер в фоне) — чтобы видеть, что происходит
python rls.py --no-headless

# Ежедневный отчёт в 23:58 (cron: 58 23 * * * ...)
python rls.py --send-daily-report

# Режим демона: цикл очередь жизни + отчёт в 23:58
python rls.py --daemon --daemon-interval-minutes 60
```

**Переменные окружения (env):** Скопируйте `.env.example` в `.env` и заполните. При запуске `rls.py` файл `.env` подхватывается автоматически (через python-dotenv).

- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — для отправки ежедневного отчёта в Telegram.
- `RLS_SKIP_BROWSER=1` — не запускать реальный браузер (для тестов).
- `RLS_HEADLESS=0` — показывать окно браузера (или флаг `--no-headless`).
- `RLS_USE_CHROME=1` — попытка использовать системный Google Chrome (часто сразу закрывается, тогда автоматически используется Chromium).

**Отчёт в 23:58:** Ежедневный Telegram-отчёт формируется и отправляется при вызове `python rls.py --send-daily-report`. Запускайте в **23:58** по расписанию или используйте `--daemon`.

Конфиги аккаунтов — JSON-файлы в `config/` (по умолчанию): `account_id`, `proxy`, `timezone`, `language`, `region`, `paused`, `profile_dir`, `cookies_file` (опционально).

---

## Вход в Reddit (авторизация)

**Не вводите логин и пароль в окне симулятора** — Reddit часто отклоняет вход из автоматизированного браузера и может ограничить аккаунт. Используйте один из способов ниже.

**Рекомендуемый способ — cookies из файла (надёжно):**

1. Войдите в Reddit в обычном Chrome.
2. Установите расширение для экспорта cookies (например [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie) или аналог).
3. На reddit.com экспортируйте cookies в JSON и сохраните файл, например `state/reddit_cookies_Altruistic-Base522.json`.
4. В конфиге аккаунта укажите `"cookies_file": "state/reddit_cookies_Altruistic-Base522.json"`.
5. При запуске симулятор подставит cookies — Reddit откроется уже залогиненным.

Формат JSON: массив объектов с полями `name`, `value`, `domain` (например `.reddit.com`), `path` (например `/`).

**Экспериментально — профиль Chrome (profile_dir):**

Можно указать в конфиге `profile_dir` путём к папке **User Data** вашего Chrome (например `C:\Users\ВашеИмя\AppData\Local\Google\Chrome\User Data`). Симулятор попытается использовать этот профиль. Ограничения: Chrome нужно закрыть перед запуском; при `RLS_USE_CHROME=1` системный Chrome часто сразу закрывается и используется Chromium; поведение и «тот же» профиль не гарантированы. Надёжнее использовать **cookies_file**.

**По умолчанию** (если не указаны `cookies_file` и не используется готовый Chrome-профиль): симулятор создаёт свой профиль в `state/browser_profiles/<account_id>`. Reddit открывается без входа (гость). Для работы от имени аккаунта нужен либо `cookies_file`, либо рабочий `profile_dir`.

---

## Тесты

```bash
python -m pytest tests/ -v
```

Все тесты должны проходить после любого изменения кода.

---

## Версионирование

Версия проекта задаётся в **двух местах**: в `constants.PROJECT_VERSION` и в файле [VERSION](../VERSION). При каждом релизе или значимом изменении необходимо обновлять **оба** значения и время разработки в VERSION. См. также [.cursorrules](../.cursorrules) и [docs/CHANGELOG.md](CHANGELOG.md).

---

## Публикация на GitHub (публичный репо)

Перед `git push` убедитесь, что **не** попадёт в репо:

| Исключено | Назначение |
|-----------|------------|
| `.env` | Токены Telegram, секреты — только `.env.example` в репо |
| `config/*.json` | Реальные конфиги аккаунтов (account_id, proxy, profile_dir) — только `*.json.example` |
| `state/` | Состояние аккаунтов, сессии, сводки |
| `logs/` | Логи работы |
| `.venv/`, `__pycache__/` | Виртуальное окружение, кэш Python |

В репо должны быть: `.env.example`, `config/account1.json.example`, код, тесты, `docs/`, `knowledge_base/`, `VERSION`.

---

## Документация и база знаний

- [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md) — контекст проекта и ссылки на knowledge_base.
- [knowledge_base/](../knowledge_base/) — архитектура, компоненты, логика, требования, решения, глоссарий, рекомендации для ИИ.
- [docs/CHANGELOG.md](CHANGELOG.md) — журнал изменений разработки.
