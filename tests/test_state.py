# -*- coding: utf-8 -*-
"""Тесты хранения состояния аккаунтов и сводного отчёта."""

import json
import tempfile
from pathlib import Path

import pytest

from state import (
    AccountState,
    load_account_state,
    save_account_state,
    load_summary,
    save_summary,
    state_path,
    summary_path,
    extra_normalized,
)
from constants import ACCOUNT_STATUS_ACTIVE


def test_account_state_from_dict():
    """AccountState создаётся из словаря."""
    data = {
        "account_id": "x",
        "sessions_count": 5,
        "fatigue_level": 0.3,
        "risk_level": 0.1,
    }
    state = AccountState.from_dict(data)
    assert state.account_id == "x"
    assert state.sessions_count == 5
    assert state.fatigue_level == 0.3
    assert state.risk_level == 0.1


def test_account_state_to_dict_roundtrip():
    """AccountState → to_dict → from_dict сохраняет данные."""
    state = AccountState(account_id="y", upvotes_count=2, daily_status=ACCOUNT_STATUS_ACTIVE)
    d = state.to_dict()
    state2 = AccountState.from_dict(d)
    assert state2.account_id == state.account_id
    assert state2.upvotes_count == state.upvotes_count
    assert state2.daily_status == state.daily_status


def test_load_account_state_missing_returns_empty(tmp_path):
    """Отсутствующий файл состояния — пустое состояние с account_id."""
    state = load_account_state("nonexistent", str(tmp_path))
    assert state.account_id == "nonexistent"
    assert state.sessions_count == 0
    assert state.fatigue_level == 0.0


def test_save_and_load_account_state(tmp_path):
    """Сохранение и загрузка состояния аккаунта."""
    state = AccountState(account_id="acc1", sessions_count=1, total_online_seconds=300)
    save_account_state(state, str(tmp_path))
    path = state_path("acc1", str(tmp_path))
    assert path.exists()
    loaded = load_account_state("acc1", str(tmp_path))
    assert loaded.account_id == state.account_id
    assert loaded.sessions_count == state.sessions_count
    assert loaded.total_online_seconds == state.total_online_seconds


def test_load_summary_empty(tmp_path):
    """Отсутствующий сводный файл — пустой список."""
    entries = load_summary(str(tmp_path))
    assert entries == []


def test_save_and_load_summary(tmp_path):
    """Сохранение и загрузка сводного отчёта."""
    entries = [{"account_id": "a", "date": "2025-02-01", "online_seconds": 100}]
    save_summary(entries, str(tmp_path))
    loaded = load_summary(str(tmp_path))
    assert len(loaded) == 1
    assert loaded[0]["account_id"] == "a"
    assert loaded[0]["online_seconds"] == 100


def test_state_path_different_ids_different_files(tmp_path):
    """Разные account_id дают разные пути (нет коллизии)."""
    p1 = state_path("acc 1", str(tmp_path))
    p2 = state_path("acc_1", str(tmp_path))
    assert p1 != p2
    assert p1.name != p2.name


def test_extra_normalized_dict():
    """extra_normalized возвращает dict как есть."""
    d = {"k": 1}
    assert extra_normalized(d) == d


def test_extra_normalized_non_dict_returns_empty():
    """extra_normalized для не-dict возвращает {}."""
    assert extra_normalized(None) == {}
    assert extra_normalized([]) == {}
    assert extra_normalized("x") == {}


def test_load_account_state_corrupted_json_returns_empty(tmp_path):
    """Повреждённый JSON в файле состояния — пустое состояние с account_id (логируется)."""
    path = state_path("acc_corrupt", str(tmp_path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ invalid json ", encoding="utf-8")
    state = load_account_state("acc_corrupt", str(tmp_path))
    assert state.account_id == "acc_corrupt"
    assert state.sessions_count == 0
    assert state.fatigue_level == 0.0


def test_load_summary_corrupted_json_returns_empty(tmp_path):
    """Повреждённый JSON в сводном файле — пустой список (логируется)."""
    path = summary_path(str(tmp_path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not valid json ]", encoding="utf-8")
    entries = load_summary(str(tmp_path))
    assert entries == []
