# -*- coding: utf-8 -*-
"""Тесты констант и лимитов."""

import pytest

from constants import (
    PROJECT_VERSION,
    UPVOTES_PER_SESSION_MAX,
    SUBSCRIBES_PER_SESSION_MAX,
    COMMENTS_ENABLED,
    ACCOUNT_STATUS_ACTIVE,
    ACCOUNT_STATUS_PASSIVE,
    ACCOUNT_STATUS_SUSPENDED,
    COOLDOWN_DAYS_MIN,
    COOLDOWN_DAYS_MAX,
    DEFAULT_STATE_DIR,
    DEFAULT_LOGS_DIR,
    DEFAULT_CONFIG_DIR,
)


def test_project_version_format():
    """Версия проекта в формате MAJOR.MINOR.PATCH."""
    parts = PROJECT_VERSION.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_upvotes_per_session_max():
    """В v1.0 не более 1–2 upvote за сессию."""
    assert 1 <= UPVOTES_PER_SESSION_MAX <= 2


def test_subscribes_per_session_max():
    """Подписки очень редки — не более 1 за сессию."""
    assert SUBSCRIBES_PER_SESSION_MAX >= 0


def test_comments_disabled_in_v1():
    """Комментарии в v1.0 отключены."""
    assert COMMENTS_ENABLED is False


def test_account_statuses():
    """Статусы аккаунта уникальны и непустые."""
    statuses = (ACCOUNT_STATUS_ACTIVE, ACCOUNT_STATUS_PASSIVE, ACCOUNT_STATUS_SUSPENDED)
    assert len(statuses) == len(set(statuses))
    assert all(isinstance(s, str) and s for s in statuses)


def test_cooldown_days_range():
    """Cooldown от суток до нескольких дней."""
    assert COOLDOWN_DAYS_MIN >= 1
    assert COOLDOWN_DAYS_MAX >= COOLDOWN_DAYS_MIN


def test_default_dirs_non_empty():
    """Каталоги по умолчанию заданы."""
    assert DEFAULT_STATE_DIR
    assert DEFAULT_LOGS_DIR
    assert DEFAULT_CONFIG_DIR
