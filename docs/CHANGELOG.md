# Changelog — Reddit Life Simulator

Журнал изменений разработки. Версия проекта и время разработки см. в [VERSION](../VERSION).

---

## [1.0.4] — 2025-02-01

### Подготовка к публикации на GitHub

- **.gitignore:** добавлен `config/*.json` — реальные конфиги аккаунтов (account_id, proxy, profile_dir) не коммитятся. В репо только шаблоны `*.json.example`.
- Уточнён комментарий: в репо остаются только примеры `config/*.json.example`.

---

## [1.0.3] — 2025-02-01

### Исправлено и улучшено

- **Документация:** NEXT_STEPS.md — Telegram отмечен как реализованный; architecture.md — нумерация разделов 5→6 (Ограничения), в CLI добавлены `--config-dir`, `--state-dir`; docs/README.md — раздел «Версионирование» (синхронизация VERSION и constants.PROJECT_VERSION); CODE_REVIEW_ISSUES.md — пункт 3.2 отмечен как документированный.
- **browser.py:** try/finally для гарантированного вызова `context.close()` при исключении в сессии.
- **state.py:** обработка ошибок при `save_account_state` и `save_summary` (логирование и проброс OSError/TypeError); версия заголовка 1.0.2.
- **config.py:** обработка ошибок в `load_account_config` (логирование и проброс JSONDecodeError/OSError).
- **risk.py:** логирование причины риска (`reason`) в `increase_risk_level`.

### Тесты

- **test_state.py:** тесты на повреждённый JSON — `test_load_account_state_corrupted_json_returns_empty`, `test_load_summary_corrupted_json_returns_empty`.
- **test_behavior.py:** фиксация `random.seed(42)` в тестах, зависящих от случайности, для воспроизводимости.
- **test_config.py:** `test_load_account_config_invalid_json_raises` — невалидный JSON приводит к JSONDecodeError.

---

## [1.0.2] — 2025-02-01

### Добавлено

- **Браузерная эмуляция (Playwright):** реальный браузер с профилем на аккаунт, прокси, Reddit, скролл, паузы, upvote (1–2 за сессию), очень редко подписка на сабреддит, детекция рисков (капча, редирект, таймаут). Переменная `RLS_SKIP_BROWSER=1` отключает браузер в тестах.
- **Реальная отправка Telegram:** `send_telegram_report` отправляет отчёт через Bot API; токен и chat_id из `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
- **Ритм по таймзоне аккаунта:** `should_skip_session_today` и `max_session_duration_seconds` принимают `timezone_str` (будни/выходные по таймзоне аккаунта).
- **Режим демона:** `--daemon` и `--daemon-interval-minutes` — цикл очередь жизни и отчёт в 23:58.
- **Валидация прокси и секреты:** `validate_proxy`, `mask_proxy_for_log` в config; при неверном прокси сессия пропускается; прокси в логах маскируется.
- Тесты: `validate_proxy`, `mask_proxy_for_log`, `max_session_duration_accepts_timezone`, `send_telegram_report_no_token_returns_false`; conftest с `RLS_SKIP_BROWSER=1`.

### Зависимости

- playwright>=1.40.0, requests>=2.28.0, python-dotenv>=1.0.0.

### Документация

- docs/README.md: Playwright install, Telegram env, daemon, структура кода.
- **.env:** добавлены `.env.example` (шаблон переменных), загрузка `.env` при старте через python-dotenv; `.gitignore` (`.env` не коммитить).

---

## [1.0.1] — 2025-02-01

### Добавлено

- **Отчёт в 23:58:** Ежедневный отчёт отправляется при вызове `python rls.py --send-daily-report` (запускать в 23:58 по расписанию). В `reporting.py`: константы `DAILY_REPORT_HOUR=23`, `DAILY_REPORT_MINUTE=58`, функции `get_today_report_entries()`, `send_daily_report()`.
- Тесты: `test_reporting.py` (отчёт, 23:58, фильтр по сегодня), `test_get_accounts_queue_sorted_by_account_id`, `test_main_send_daily_report_returns_zero`, тесты `state_path` (нет коллизии), `extra_normalized`.

### Исправлено

- **last_session_at:** обновляется в `rls.py` после каждой сессии.
- **Лимит upvote за сессию:** в `behavior.max_upvotes_for_session` возвращается лимит именно за сессию (1–2), без привязки к глобальному счётчику.
- **Коллизия имён в state_path:** разные `account_id` дают разные файлы (хэш-суффикс); обратная совместимость со старым форматом (миграция при загрузке).
- **Обработка ошибок:** при битом JSON/ошибке чтения в `load_account_state` и `load_summary` возвращается пустое состояние/пустой список и пишется предупреждение в лог.
- **extra в состоянии:** нормализация `extra` в `AccountState.from_dict` (только dict, иначе `{}`).
- Удалены неиспользуемые импорты в `rls.py` и `config.py`.
- Очередь жизни сортируется по `account_id`.
- Валидация конфига: `account_id`, `timezone`, `language`, `region` — strip и значения по умолчанию.

### Документация

- docs/README.md: раздел про отчёт в 23:58 и `--send-daily-report`.
- docs/CODE_REVIEW_ISSUES.md: отмечены исправленные пункты.

---

## [1.0.0] — 2025-02-01

### Добавлено

- **rls.py** — главная точка входа: очередь жизни (один аккаунт в момент времени), CLI с `--config-dir`, `--state-dir`, `--dry-run`.
- **constants.py** — версия проекта 1.0.0, лимиты v1.0 (upvote/подписки за сессию, статусы, cooldown), каталоги по умолчанию.
- **config.py** — загрузка конфигурации аккаунтов из JSON, `AccountConfig`, `get_accounts_queue()` (исключение paused).
- **state.py** — состояние аккаунта (`AccountState`), загрузка/сохранение по аккаунту, сводный файл отчётности.
- **browser.py** — заглушка браузерной эмуляции: `run_session()`, `SessionResult`, `detect_risk_in_page()` (v1.0 без реального браузера).
- **behavior.py** — поведенческая модель: усталость, пропуск сессии, длительность сессии, лимит upvote, применение усталости после сессии.
- **risk.py** — cooldown (длительность, дата окончания), проверка `is_in_cooldown()`, увеличение уровня риска.
- **reporting.py** — формирование записи ежедневного отчёта, добавление в сводный файл, заглушка отправки в Telegram.
- **requirements.txt** — зависимость pytest для тестов.
- **tests/** — тесты для constants, config, state, behavior, risk, browser, rls (38 тестов).
- **docs/README.md** — описание структуры кода и запуска.
- **docs/CHANGELOG.md** — журнал изменений.
- **VERSION** — файл с версией проекта и накопленным временем разработки.

### Изменено

- Использование `datetime.now(timezone.utc)` вместо устаревшего `datetime.utcnow()` в behavior, risk, reporting и тестах.

### Документация

- Внутренняя база знаний (knowledge_base) создана ранее; структура кода и главный файл rls.py отражены в docs/README.md.

---

Формат версий: [Semantic Versioning](https://semver.org/).  
Даты в формате YYYY-MM-DD.
