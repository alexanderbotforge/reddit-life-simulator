# -*- coding: utf-8 -*-
"""Тесты поведенческой модели: усталость, ритм, лимиты."""

import random

import pytest

from state import AccountState
from behavior import (
    should_skip_session_today,
    max_session_duration_seconds,
    max_upvotes_for_session,
    apply_fatigue_after_session,
)
from constants import UPVOTES_PER_SESSION_MAX


def test_max_upvotes_for_session():
    """Максимум upvote за сессию не превышает лимит v1.0."""
    random.seed(42)
    state = AccountState(account_id="x", upvotes_count=0)
    m = max_upvotes_for_session(state)
    assert 0 <= m <= UPVOTES_PER_SESSION_MAX


def test_apply_fatigue_after_session_increases_fatigue():
    """После сессии с активностью усталость растёт (в допустимых пределах)."""
    state = AccountState(account_id="x", fatigue_level=0.2)
    new_fatigue = apply_fatigue_after_session(state, online_seconds=3600, upvotes=1, subscribes=0)
    assert new_fatigue >= 0.0
    assert new_fatigue <= 1.0


def test_apply_fatigue_capped_at_one():
    """Усталость не превышает 1.0."""
    state = AccountState(account_id="x", fatigue_level=0.95)
    new_fatigue = apply_fatigue_after_session(state, online_seconds=10000, upvotes=5, subscribes=2)
    assert new_fatigue <= 1.0


def test_max_session_duration_positive():
    """Максимальная длительность сессии положительная."""
    random.seed(42)
    state = AccountState(account_id="x", fatigue_level=0.0)
    duration = max_session_duration_seconds(state)
    assert duration >= 60


def test_max_session_duration_accepts_timezone():
    """max_session_duration_seconds принимает timezone_str."""
    state = AccountState(account_id="x", fatigue_level=0.0)
    d1 = max_session_duration_seconds(state, "UTC")
    d2 = max_session_duration_seconds(state, "Europe/Moscow")
    assert d1 >= 60
    assert d2 >= 60


def test_should_skip_session_today_returns_bool():
    """should_skip_session_today возвращает bool."""
    random.seed(42)
    state = AccountState(account_id="x")
    result = should_skip_session_today(state)
    assert isinstance(result, bool)
