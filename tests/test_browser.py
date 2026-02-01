# -*- coding: utf-8 -*-
"""Тесты браузерной эмуляции (заглушка v1.0)."""

import pytest

from config import AccountConfig
from browser import run_session, SessionResult, detect_risk_in_page


def test_run_session_returns_session_result():
    """run_session возвращает SessionResult."""
    cfg = AccountConfig(account_id="test", timezone="UTC")
    result = run_session(cfg)
    assert isinstance(result, SessionResult)
    assert result.online_seconds >= 0
    assert result.upvotes >= 0
    assert result.subscribes >= 0


def test_run_session_stub_no_risk_by_default():
    """Заглушка v1.0 не детектирует риск по умолчанию."""
    cfg = AccountConfig(account_id="test")
    result = run_session(cfg)
    assert result.risk_detected is False
    assert result.risk_reason is None


def test_detect_risk_in_page_returns_tuple():
    """detect_risk_in_page возвращает (bool, Optional[str])."""
    detected, reason = detect_risk_in_page()
    assert isinstance(detected, bool)
    assert reason is None or isinstance(reason, str)


def test_detect_risk_stub_no_risk():
    """Заглушка detect_risk_in_page не обнаруживает риск."""
    detected, _ = detect_risk_in_page()
    assert detected is False
