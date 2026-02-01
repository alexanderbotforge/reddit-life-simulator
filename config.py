# -*- coding: utf-8 -*-
# ===================== БЛОК 1: Заголовок =====================
# Reddit Life Simulator — загрузка и валидация конфигурации аккаунтов
# Версия: 1.0.3
# Описание: Конфигурационный файл на аккаунт: прокси, таймзона, язык, регион, лимиты, флаги паузы.
# Время разработки: 3h
# Последнее обновление: 2025-02-01
#
# Changelog:
# 1.0.0 (2025-02-01) — первоначальная версия.
# 1.0.1 (2025-02-01) — очередь по account_id, валидация (strip, значения по умолчанию), удалён неиспользуемый импорт.
# 1.0.2 (2025-02-01) — validate_proxy, mask_proxy_for_log (секреты не логировать).
# 1.0.3 (2025-02-01) — обработка ошибок в load_account_config (логирование и проброс).
# ===================== КОНЕЦ БЛОКА 1 =====================

"""Загрузка и валидация конфигурации аккаунтов."""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from constants import DEFAULT_CONFIG_DIR

logger = logging.getLogger(__name__)


def validate_proxy(proxy: Optional[str]) -> bool:
    """Проверить формат прокси: пусто, host:port, или http(s)/socks5 URL."""
    if not proxy or not str(proxy).strip():
        return True
    s = str(proxy).strip()
    if re.match(r"^(https?|socks5)://", s):
        return True
    if re.match(r"^[\w.-]+:\d+$", s):
        return True
    if "@" in s and re.search(r"@[\w.-]+:\d+$", s):
        return True
    return False


def mask_proxy_for_log(proxy: Optional[str]) -> str:
    """Маскировать прокси в логах (не выводить user:pass)."""
    if not proxy or not str(proxy).strip():
        return "(нет)"
    s = str(proxy).strip()
    if "@" in s:
        return "***@" + s.split("@", 1)[-1]
    if "://" in s:
        return re.sub(r"^[^:]+://[^:]+:[^@]+@", "***@", s)
    return s


@dataclass
class AccountConfig:
    """Конфигурация одного аккаунта."""

    account_id: str
    proxy: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    region: str = ""
    paused: bool = False
    profile_dir: str = ""
    cookies_file: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "account_id": self.account_id,
            "proxy": self.proxy,
            "timezone": self.timezone,
            "language": self.language,
            "region": self.region,
            "paused": self.paused,
            "profile_dir": self.profile_dir,
            "cookies_file": self.cookies_file,
            **self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AccountConfig":
        account_id = str(data.get("account_id", "")).strip()
        return cls(
            account_id=account_id,
            proxy=data.get("proxy"),
            timezone=str(data.get("timezone", "UTC")).strip() or "UTC",
            language=str(data.get("language", "en")).strip() or "en",
            region=str(data.get("region", "")).strip(),
            paused=bool(data.get("paused", False)),
            profile_dir=str(data.get("profile_dir", "")).strip(),
            cookies_file=str(data.get("cookies_file", "")).strip(),
            extra={k: v for k, v in data.items() if k not in (
                "account_id", "proxy", "timezone", "language", "region", "paused", "profile_dir", "cookies_file"
            )},
        )


def load_account_config(path: Path) -> AccountConfig:
    """Загрузить конфигурацию аккаунта из JSON-файла. При ошибке чтения/парсинга логирует и пробрасывает исключение."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AccountConfig.from_dict(data)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Не удалось загрузить конфиг из %s: %s", path, e)
        raise


def load_all_account_configs(config_dir: Optional[str] = None) -> List[AccountConfig]:
    """Загрузить все конфигурации аккаунтов из каталога (файлы *.json)."""
    config_dir = config_dir or DEFAULT_CONFIG_DIR
    path = Path(config_dir)
    if not path.exists():
        return []
    configs: List[AccountConfig] = []
    for f in path.glob("*.json"):
        try:
            configs.append(load_account_config(f))
        except (json.JSONDecodeError, OSError):
            continue
    return configs


def get_accounts_queue(config_dir: Optional[str] = None) -> List[AccountConfig]:
    """Очередь жизни: список аккаунтов для последовательной обработки (без пауз), отсортированный по account_id."""
    all_configs = load_all_account_configs(config_dir)
    queue = [c for c in all_configs if not c.paused and c.account_id]
    queue.sort(key=lambda c: c.account_id)
    return queue
