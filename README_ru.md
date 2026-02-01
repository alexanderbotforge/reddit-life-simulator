# Reddit Life Simulator

> 🇬🇧 English version: [README.md](README.md)

[![Made by Alexander BotForge](https://img.shields.io/badge/Made%20by-Alexander%20BotForge-blue.svg)](https://github.com/alexanderbotforge)

Автономная система долгосрочной имитации «жизни» Reddit-аккаунтов. Поведение аккаунтов визуально и поведенчески неотличимо от человеческого.

## Быстрый старт

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # заполните TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
cp config/account1.json.example config/account1.json   # настройте аккаунт
python rls.py --dry-run   # тест без браузера
python rls.py --config-dir config --state-dir state   # запуск с браузером
```

## Документация

Полная документация: **[docs/README.md](docs/README.md)**

- Установка, Playwright, переменные окружения
- Вход в Reddit (cookies, профиль Chrome)
- CLI: `--dry-run`, `--daemon`, `--send-daily-report`
- Тесты: `python -m pytest tests/ -v`

## Лицензия

MIT
