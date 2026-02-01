# -*- coding: utf-8 -*-
"""Тесты загрузки и валидации конфигурации аккаунтов."""

import json
import tempfile
from pathlib import Path

import pytest

from config import (
    AccountConfig,
    load_account_config,
    load_all_account_configs,
    get_accounts_queue,
    validate_proxy,
    mask_proxy_for_log,
)


def test_account_config_from_dict():
    """AccountConfig создаётся из словаря."""
    data = {
        "account_id": "test1",
        "proxy": "http://proxy:8080",
        "timezone": "Europe/Moscow",
        "language": "en",
        "region": "US",
        "paused": False,
    }
    cfg = AccountConfig.from_dict(data)
    assert cfg.account_id == "test1"
    assert cfg.proxy == "http://proxy:8080"
    assert cfg.timezone == "Europe/Moscow"
    assert cfg.language == "en"
    assert cfg.region == "US"
    assert cfg.paused is False


def test_account_config_to_dict_roundtrip():
    """AccountConfig → to_dict → from_dict сохраняет данные."""
    cfg = AccountConfig(account_id="a1", timezone="UTC", paused=True)
    d = cfg.to_dict()
    cfg2 = AccountConfig.from_dict(d)
    assert cfg2.account_id == cfg.account_id
    assert cfg2.timezone == cfg.timezone
    assert cfg2.paused == cfg.paused


def test_load_account_config(tmp_path):
    """Загрузка конфига из JSON-файла."""
    path = tmp_path / "acc1.json"
    path.write_text(
        json.dumps({"account_id": "acc1", "timezone": "UTC", "language": "en"}, ensure_ascii=False),
        encoding="utf-8",
    )
    cfg = load_account_config(path)
    assert cfg.account_id == "acc1"
    assert cfg.timezone == "UTC"


def test_load_all_account_configs_empty_dir(tmp_path):
    """Пустой каталог конфигов — пустой список."""
    configs = load_all_account_configs(str(tmp_path))
    assert configs == []


def test_load_all_account_configs_two_files(tmp_path):
    """Два JSON-файла — два конфига."""
    (tmp_path / "a.json").write_text(json.dumps({"account_id": "a"}), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps({"account_id": "b", "paused": True}), encoding="utf-8")
    configs = load_all_account_configs(str(tmp_path))
    ids = [c.account_id for c in configs]
    assert "a" in ids
    assert "b" in ids
    assert len(configs) == 2


def test_get_accounts_queue_excludes_paused(tmp_path):
    """Очередь жизни не включает аккаунты с paused=True."""
    (tmp_path / "a.json").write_text(json.dumps({"account_id": "a", "paused": False}), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps({"account_id": "b", "paused": True}), encoding="utf-8")
    queue = get_accounts_queue(str(tmp_path))
    assert len(queue) == 1
    assert queue[0].account_id == "a"


def test_validate_proxy():
    """validate_proxy принимает пусто, host:port, URL."""
    assert validate_proxy(None) is True
    assert validate_proxy("") is True
    assert validate_proxy("host:8080") is True
    assert validate_proxy("http://proxy:8080") is True
    assert validate_proxy("socks5://host:1080") is True
    assert validate_proxy("user:pass@host:8080") is True
    assert validate_proxy("invalid") is False


def test_mask_proxy_for_log():
    """mask_proxy_for_log маскирует учётные данные."""
    assert "(нет)" in mask_proxy_for_log(None)
    assert "***@" in mask_proxy_for_log("user:pass@host:8080")
    assert "host:8080" in mask_proxy_for_log("host:8080")


def test_get_accounts_queue_sorted_by_account_id(tmp_path):
    """Очередь жизни отсортирована по account_id."""
    (tmp_path / "z.json").write_text(json.dumps({"account_id": "z"}), encoding="utf-8")
    (tmp_path / "a.json").write_text(json.dumps({"account_id": "a"}), encoding="utf-8")
    (tmp_path / "m.json").write_text(json.dumps({"account_id": "m"}), encoding="utf-8")
    queue = get_accounts_queue(str(tmp_path))
    assert [c.account_id for c in queue] == ["a", "m", "z"]


def test_load_account_config_invalid_json_raises(tmp_path):
    """Невалидный JSON в файле конфига — исключение после логирования."""
    path = tmp_path / "bad.json"
    path.write_text("{ invalid ", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load_account_config(path)
