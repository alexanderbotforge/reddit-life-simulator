# -*- coding: utf-8 -*-
"""Тесты отчётности: ежедневный отчёт, отправка в 23:58."""

import pytest

from reporting import (
    DAILY_REPORT_HOUR,
    DAILY_REPORT_MINUTE,
    get_today_report_entries,
    send_daily_report,
    send_telegram_report,
    build_daily_report_entry,
)
from state import AccountState, load_summary, save_summary


def test_daily_report_time_constants():
    """Отчёт отправляется в 23:58."""
    assert DAILY_REPORT_HOUR == 23
    assert DAILY_REPORT_MINUTE == 58


def test_get_today_report_entries_empty(tmp_path):
    """Пустая сводка — пустой список за сегодня."""
    entries = get_today_report_entries(str(tmp_path))
    assert entries == []


def test_get_today_report_entries_filters_by_today(tmp_path):
    """get_today_report_entries возвращает только записи за сегодня."""
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date().isoformat()
    save_summary(
        [
            {"account_id": "a", "date": today, "online_seconds": 10},
            {"account_id": "b", "date": "2020-01-01", "online_seconds": 5},
        ],
        str(tmp_path),
    )
    entries = get_today_report_entries(str(tmp_path))
    assert len(entries) == 1
    assert entries[0]["account_id"] == "a"
    assert entries[0]["date"] == today


def test_send_daily_report_no_entries(tmp_path):
    """send_daily_report при отсутствии записей возвращает False."""
    assert send_daily_report(str(tmp_path)) is False


def test_send_telegram_report_no_entries():
    """send_telegram_report без entries возвращает False."""
    assert send_telegram_report([]) is False


def test_send_telegram_report_no_token_returns_false(monkeypatch):
    """Без TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID возвращает False."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    assert send_telegram_report([{"account_id": "x"}]) is False


def test_build_daily_report_entry():
    """build_daily_report_entry формирует запись с нужными полями."""
    state = AccountState(account_id="a", total_online_seconds=100, risk_level=0.5)
    entry = build_daily_report_entry(state)
    assert entry["account_id"] == "a"
    assert entry["online_seconds"] == 100
    assert entry["risk_level"] == 0.5
    assert "date" in entry
    assert "daily_status" in entry
