# -*- coding: utf-8 -*-
# ===================== БЛОК 1: Заголовок =====================
# Reddit Life Simulator — контроль рисков и cooldown
# Версия: 1.0.1
# Описание: Обнаружение рисков (капча, редиректы, задержки), cooldown и накопительный уровень риска.
# Время разработки: 1.5h
# Последнее обновление: 2025-02-01
#
# Changelog:
# 1.0.0 (2025-02-01) — первоначальная версия.
# 1.0.1 (2025-02-01) — логирование reason в increase_risk_level.
# ===================== КОНЕЦ БЛОКА 1 =====================

"""Контроль рисков: обнаружение, cooldown, накопительное состояние риска."""

import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from constants import COOLDOWN_DAYS_MAX, COOLDOWN_DAYS_MIN

logger = logging.getLogger(__name__)


def compute_cooldown_until_days() -> int:
    """Длительность cooldown в днях (от суток до нескольких дней)."""
    return random.randint(COOLDOWN_DAYS_MIN, COOLDOWN_DAYS_MAX)


def cooldown_end_iso(days: Optional[int] = None) -> str:
    """Дата окончания cooldown в ISO-формате."""
    days = days or compute_cooldown_until_days()
    end = datetime.now(timezone.utc) + timedelta(days=days)
    return end.date().isoformat()


def is_in_cooldown(cooldown_until: Optional[str]) -> bool:
    """Проверить, находится ли аккаунт в cooldown."""
    if not cooldown_until:
        return False
    try:
        end = datetime.strptime(cooldown_until, "%Y-%m-%d").date()
        return datetime.now(timezone.utc).date() <= end
    except (ValueError, TypeError):
        return False


def increase_risk_level(current: float, reason: str) -> float:
    """
    Увеличить накопительный уровень риска (0.0 .. 1.0).
    Причина риска логируется для отладки и аудита.
    """
    logger.info("Увеличение уровня риска: причина=%s, текущий=%.2f", reason, current)
    return min(1.0, current + 0.15)
