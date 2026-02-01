# -*- coding: utf-8 -*-
"""Тесты главного модуля rls: очередь жизни, dry-run."""

import json
from pathlib import Path

import pytest

# Импорт главного модуля (корень проекта в PYTHONPATH при запуске pytest из корня)
from config import get_accounts_queue
from state import load_account_state, load_summary, save_account_state, AccountState
from constants import DEFAULT_CONFIG_DIR, DEFAULT_STATE_DIR

# Импорт rls после подготовки путей
import rls


def test_run_life_cycle_empty_queue(tmp_path):
    """Пустая очередь — выход без ошибок."""
    rls.run_life_cycle(config_dir=str(tmp_path), state_dir=str(tmp_path), dry_run=True)


def test_run_life_cycle_dry_run_one_account(tmp_path):
    """Один аккаунт в очереди, dry_run: сессия не запускается, состояние создаётся/обновляется."""
    config_dir = tmp_path / "config"
    state_dir = tmp_path / "state"
    config_dir.mkdir()
    state_dir.mkdir()
    (config_dir / "acc1.json").write_text(
        json.dumps({"account_id": "acc1", "timezone": "UTC", "paused": False}), encoding="utf-8"
    )
    rls.run_life_cycle(config_dir=str(config_dir), state_dir=str(state_dir), dry_run=True)
    # В dry_run может сработать should_skip_session_today (случайность) или нет — главное без исключений
    # Проверим, что сводный файл мог появиться или каталог состояния доступен
    state = load_account_state("acc1", str(state_dir))
    assert state.account_id == "acc1"


def test_main_returns_zero(tmp_path):
    """CLI main возвращает 0 (успех)."""
    import sys
    backup = sys.argv
    empty_config = tmp_path / "cfg"
    empty_config.mkdir()
    sys.argv = ["rls", "--dry-run", "--config-dir", str(empty_config)]
    try:
        code = rls.main()
        assert code == 0
    finally:
        sys.argv = backup


def test_main_send_daily_report_returns_zero(tmp_path):
    """CLI --send-daily-report возвращает 0."""
    import sys
    backup = sys.argv
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    sys.argv = ["rls", "--send-daily-report", "--state-dir", str(state_dir)]
    try:
        code = rls.main()
        assert code == 0
    finally:
        sys.argv = backup
