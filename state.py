# -*- coding: utf-8 -*-
# ===================== БЛОК 1: Заголовок =====================
# Reddit Life Simulator — хранение состояния аккаунтов
# Версия: 1.0.2
# Описание: Состояние по аккаунту (сессии, усталость, действия, риски, паузы) и сводный файл для отчётности.
# Время разработки: 3h
# Последнее обновление: 2025-02-01
#
# Changelog:
# 1.0.0 (2025-02-01) — первоначальная версия.
# 1.0.1 (2025-02-01) — state_path с хэшем (нет коллизии), extra_normalized, обработка ошибок, миграция старого формата.
# 1.0.2 (2025-02-01) — обработка ошибок при save_account_state и save_summary (логирование и проброс).
# ===================== КОНЕЦ БЛОКА 1 =====================

"""Хранение состояния аккаунтов и сводный отчёт."""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

from constants import (
    ACCOUNT_STATUS_ACTIVE,
    DEFAULT_STATE_DIR,
    STATE_ACCOUNT_SUFFIX,
    STATE_SUMMARY_FILE,
)


@dataclass
class AccountState:
    """Состояние одного аккаунта."""

    account_id: str
    sessions_count: int = 0
    total_online_seconds: int = 0
    upvotes_count: int = 0
    subscribes_count: int = 0
    fatigue_level: float = 0.0
    risk_level: float = 0.0
    cooldown_until: Optional[str] = None
    last_session_at: Optional[str] = None
    daily_status: str = ACCOUNT_STATUS_ACTIVE
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "AccountState":
        return cls(
            account_id=str(data.get("account_id", "")),
            sessions_count=int(data.get("sessions_count", 0)),
            total_online_seconds=int(data.get("total_online_seconds", 0)),
            upvotes_count=int(data.get("upvotes_count", 0)),
            subscribes_count=int(data.get("subscribes_count", 0)),
            fatigue_level=float(data.get("fatigue_level", 0.0)),
            risk_level=float(data.get("risk_level", 0.0)),
            cooldown_until=data.get("cooldown_until"),
            last_session_at=data.get("last_session_at"),
            daily_status=str(data.get("daily_status", ACCOUNT_STATUS_ACTIVE)),
            extra=extra_normalized(data.get("extra")),
        )


def extra_normalized(value: Any) -> dict:
    """Нормализовать extra к dict (для совместимости с битым JSON)."""
    if isinstance(value, dict):
        return value
    return {}


def _state_path_legacy(account_id: str, state_dir: str) -> Path:
    """Старый формат пути (без хэша) — для обратной совместимости."""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in account_id)
    return Path(state_dir) / f"{safe}{STATE_ACCOUNT_SUFFIX}"


def state_path(account_id: str, state_dir: Optional[str] = None) -> Path:
    """Путь к файлу состояния аккаунта. Разные account_id дают разные файлы (хэш-суффикс)."""
    state_dir = state_dir or DEFAULT_STATE_DIR
    base = "".join(c if c.isalnum() or c in "-_" else "_" for c in account_id)[:50]
    suffix = hashlib.sha256(account_id.encode()).hexdigest()[:8]
    return Path(state_dir) / f"{base}_{suffix}{STATE_ACCOUNT_SUFFIX}"


def load_account_state(account_id: str, state_dir: Optional[str] = None) -> AccountState:
    """Загрузить состояние аккаунта. Если файла нет или ошибка чтения — пустое состояние."""
    state_dir = state_dir or DEFAULT_STATE_DIR
    path = state_path(account_id, state_dir)
    legacy_path = _state_path_legacy(account_id, state_dir)
    for p in (path, legacy_path):
        if not p.exists():
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            state = AccountState.from_dict(data)
            if p == legacy_path:
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
                logger.info("Миграция состояния %s в новый формат файла.", account_id)
            return state
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Не удалось загрузить состояние %s из %s: %s", account_id, p, e)
    return AccountState(account_id=account_id)


def save_account_state(state: AccountState, state_dir: Optional[str] = None) -> None:
    """Сохранить состояние аккаунта. При ошибке записи логирует и пробрасывает исключение."""
    path = state_path(state.account_id, state_dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
    except (OSError, TypeError) as e:
        logger.error("Не удалось сохранить состояние %s в %s: %s", state.account_id, path, e)
        raise


def summary_path(state_dir: Optional[str] = None) -> Path:
    """Путь к сводному файлу для отчётности."""
    state_dir = state_dir or DEFAULT_STATE_DIR
    return Path(state_dir) / STATE_SUMMARY_FILE


def load_summary(state_dir: Optional[str] = None) -> List[dict]:
    """Загрузить сводный отчёт (список записей по аккаунтам). При ошибке — пустой список."""
    path = summary_path(state_dir)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Не удалось загрузить сводку: %s", e)
        return []


def save_summary(entries: List[dict], state_dir: Optional[str] = None) -> None:
    """Сохранить сводный отчёт. При ошибке записи логирует и пробрасывает исключение."""
    path = summary_path(state_dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
    except (OSError, TypeError) as e:
        logger.error("Не удалось сохранить сводку в %s: %s", path, e)
        raise
