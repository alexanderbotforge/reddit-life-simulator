# -*- coding: utf-8 -*-
"""Тесты контроля рисков и cooldown."""

from datetime import datetime, timedelta, timezone

import pytest

from risk import (
    is_in_cooldown,
    cooldown_end_iso,
    compute_cooldown_until_days,
    increase_risk_level,
)
from constants import COOLDOWN_DAYS_MIN, COOLDOWN_DAYS_MAX


def test_is_in_cooldown_none():
    """Отсутствие cooldown_until — не в cooldown."""
    assert is_in_cooldown(None) is False
    assert is_in_cooldown("") is False


def test_is_in_cooldown_future():
    """Дата в будущем — в cooldown."""
    future = (datetime.now(timezone.utc) + timedelta(days=2)).date().isoformat()
    assert is_in_cooldown(future) is True


def test_is_in_cooldown_past():
    """Дата в прошлом — не в cooldown."""
    past = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
    assert is_in_cooldown(past) is False


def test_cooldown_end_iso_format():
    """cooldown_end_iso возвращает дату в формате YYYY-MM-DD."""
    s = cooldown_end_iso(days=3)
    assert len(s) == 10
    parts = s.split("-")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_compute_cooldown_until_days_in_range():
    """Длительность cooldown в допустимом диапазоне."""
    for _ in range(20):
        days = compute_cooldown_until_days()
        assert COOLDOWN_DAYS_MIN <= days <= COOLDOWN_DAYS_MAX


def test_increase_risk_level_capped():
    """Уровень риска не превышает 1.0."""
    r = increase_risk_level(0.9, "test")
    assert r <= 1.0
    r = increase_risk_level(1.0, "test")
    assert r == 1.0


def test_increase_risk_level_rises():
    """Уровень риска увеличивается."""
    r0 = 0.2
    r1 = increase_risk_level(r0, "captcha")
    assert r1 > r0
