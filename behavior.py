# -*- coding: utf-8 -*-
# ===================== БЛОК 1: Заголовок =====================
# Reddit Life Simulator — поведенческая модель
# Версия: 1.0.2
# Описание: Сессии, усталость, календарный ритм (будни/выходные) по таймзоне аккаунта, лимиты действий.
# Время разработки: 3h
# Последнее обновление: 2025-02-01
#
# Changelog:
# 1.0.0 (2025-02-01) — первоначальная версия.
# 1.0.1 (2025-02-01) — max_upvotes_for_session: лимит за сессию (1–2), без привязки к глобальному счётчику.
# 1.0.2 (2025-02-01) — ритм по таймзоне аккаунта: should_skip_session_today, max_session_duration_seconds принимают timezone_str.
# ===================== КОНЕЦ БЛОКА 1 =====================

"""Поведенческая модель: усталость, ритм жизни по таймзоне аккаунта, длительность сессии, лимиты действий."""

import random
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from constants import UPVOTES_PER_SESSION_MAX
from state import AccountState


def _now_in_tz(timezone_str: Optional[str]) -> datetime:
    """Текущее время в таймзоне аккаунта (для будни/выходные и времени суток)."""
    if not timezone_str or timezone_str.strip() == "UTC":
        return datetime.now(timezone.utc)
    try:
        return datetime.now(ZoneInfo(timezone_str.strip()))
    except Exception:
        return datetime.now(timezone.utc)


def should_skip_session_today(state: AccountState, timezone_str: Optional[str] = None) -> bool:
    """
    Решить, пропускать ли сессию сегодня (дни без активности допустимы).
    Учитывается усталость и случайность. timezone_str — таймзона аккаунта для «сегодня».
    """
    if state.fatigue_level >= 0.8:
        return random.random() < 0.5
    if state.fatigue_level >= 0.5:
        return random.random() < 0.2
    return random.random() < 0.05


def max_session_duration_seconds(state: AccountState, timezone_str: Optional[str] = None) -> int:
    """
    Максимальная длительность сессии в секундах с учётом усталости и времени суток.
    Будни/выходные считаются по таймзоне аккаунта (timezone_str).
    """
    base = 600
    if state.fatigue_level >= 0.7:
        base = int(base * 0.3)
    elif state.fatigue_level >= 0.4:
        base = int(base * 0.6)
    now = _now_in_tz(timezone_str)
    if now.weekday() >= 5:
        base = int(base * 1.5)
    return max(60, base + random.randint(-120, 180))


def max_upvotes_for_session(state: AccountState) -> int:
    """Максимум upvote в рамках одной сессии (v1.0: не более 1–2 за сессию)."""
    return random.randint(1, UPVOTES_PER_SESSION_MAX)


def apply_fatigue_after_session(
    state: AccountState,
    online_seconds: int,
    upvotes: int,
    subscribes: int,
) -> float:
    """
    Обновить уровень усталости после сессии.
    Возвращает новый fatigue_level (0.0 .. 1.0).
    """
    delta = 0.0
    delta += online_seconds / 3600.0 * 0.05
    delta += (upvotes + subscribes) * 0.02
    new_fatigue = min(1.0, state.fatigue_level + delta)
    # Естественное снижение усталости со временем (упрощённо — небольшой декремент)
    decay = 0.02
    return max(0.0, new_fatigue - decay)
