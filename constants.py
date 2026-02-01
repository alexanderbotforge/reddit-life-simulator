# -*- coding: utf-8 -*-
# ===================== БЛОК 1: Заголовок =====================
# Reddit Life Simulator — константы и лимиты
# Версия: 1.0.4
# Описание: Глобальные константы, лимиты v1.0 и версия проекта.
# Время разработки: 2h
# Последнее обновление: 2025-02-01
#
# Changelog:
# 1.0.0 (2025-02-01) — первоначальная версия.
# 1.0.1 (2025-02-01) — PROJECT_VERSION 1.0.1.
# 1.0.2 (2025-02-01) — PROJECT_VERSION 1.0.2.
# 1.0.3 (2025-02-01) — PROJECT_VERSION 1.0.3.
# 1.0.4 (2025-02-01) — .gitignore: config/*.json для публичного репо (без реальных конфигов).
# ===================== КОНЕЦ БЛОКА 1 =====================

"""Константы и лимиты Reddit Life Simulator v1.0."""

# Версия проекта (semantic version); синхронизировать с VERSION
PROJECT_VERSION = "1.0.4"

# Лимиты действий в одной сессии (v1.0)
UPVOTES_PER_SESSION_MIN = 0
UPVOTES_PER_SESSION_MAX = 2

# Подписки: только на сабреддиты, очень редко
SUBSCRIBES_PER_SESSION_MAX = 1

# Комментарии в v1.0 отключены
COMMENTS_ENABLED = False

# Статусы аккаунта в конце дня
ACCOUNT_STATUS_ACTIVE = "active"
ACCOUNT_STATUS_PASSIVE = "passive"
ACCOUNT_STATUS_SUSPENDED = "suspended"

# Cooldown: минимальная и максимальная длительность (дни)
COOLDOWN_DAYS_MIN = 1
COOLDOWN_DAYS_MAX = 7

# Каталоги по умолчанию
DEFAULT_STATE_DIR = "state"
DEFAULT_LOGS_DIR = "logs"
DEFAULT_CONFIG_DIR = "config"

# Имена файлов состояния
STATE_ACCOUNT_SUFFIX = "_state.json"
STATE_SUMMARY_FILE = "summary.json"
