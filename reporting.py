# -*- coding: utf-8 -*-
# ===================== БЛОК 1: Заголовок =====================
# Reddit Life Simulator — отчётность
# Версия: 1.0.2
# Описание: Ежедневный агрегированный Telegram-отчёт по каждому аккаунту. Отправка в 23:58.
# Время разработки: 3h
# Последнее обновление: 2025-02-01
#
# Changelog:
# 1.0.0 (2025-02-01) — первоначальная версия (заглушка отправки в Telegram).
# 1.0.1 (2025-02-01) — DAILY_REPORT_HOUR/MINUTE=23/58, get_today_report_entries, send_daily_report.
# 1.0.2 (2025-02-01) — Реальная отправка в Telegram (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID).
# ===================== КОНЕЦ БЛОКА 1 =====================

"""Ежедневный Telegram-отчёт: время онлайна, количество действий, уровень риска. Отправка в 23:58."""

import logging
import os
from datetime import datetime, timezone
from typing import Any, List, Optional

from state import AccountState, load_summary, save_summary

logger = logging.getLogger(__name__)

# Время отправки ежедневного отчёта (по локальному/серверному времени планировщика)
DAILY_REPORT_HOUR = 23
DAILY_REPORT_MINUTE = 58


def build_daily_report_entry(state: AccountState) -> dict:
    """Сформировать одну запись отчёта по аккаунту."""
    return {
        "account_id": state.account_id,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "online_seconds": state.total_online_seconds,
        "sessions_count": state.sessions_count,
        "upvotes_count": state.upvotes_count,
        "subscribes_count": state.subscribes_count,
        "risk_level": round(state.risk_level, 2),
        "daily_status": state.daily_status,
        "cooldown_until": state.cooldown_until,
    }


def append_to_summary(state: AccountState, state_dir: Optional[str] = None) -> None:
    """Добавить запись по аккаунту в сводный файл отчётности."""
    entries = load_summary(state_dir)
    entry = build_daily_report_entry(state)
    # Обновить или добавить запись по account_id за сегодня
    date = entry["date"]
    entries = [e for e in entries if not (e.get("account_id") == state.account_id and e.get("date") == date)]
    entries.append(entry)
    save_summary(entries, state_dir)


def get_today_report_entries(state_dir: Optional[str] = None) -> List[dict]:
    """Получить записи сводного отчёта за сегодня (для отправки в 23:58)."""
    today = datetime.now(timezone.utc).date().isoformat()
    entries = load_summary(state_dir)
    return [e for e in entries if e.get("date") == today]


def send_daily_report(state_dir: Optional[str] = None) -> bool:
    """
    Сформировать и отправить ежедневный отчёт (вызывать в 23:58 по расписанию).
    Загружает сводку за сегодня и отправляет в Telegram.
    """
    entries = get_today_report_entries(state_dir)
    return send_telegram_report(entries)


def _format_report_message(entries: List[dict]) -> str:
    """Форматировать записи отчёта в текст сообщения."""
    lines = ["📊 Ежедневный отчёт Reddit Life Simulator"]
    for e in entries:
        acc = e.get("account_id", "?")
        status = e.get("daily_status", "?")
        online = e.get("online_seconds", 0)
        up = e.get("upvotes_count", 0)
        sub = e.get("subscribes_count", 0)
        risk = e.get("risk_level", 0)
        cooldown = e.get("cooldown_until", "")
        line = f"• {acc}: {status}, онлайн {online}с, upvote {up}, подписки {sub}, риск {risk}"
        if cooldown:
            line += f", cooldown до {cooldown}"
        lines.append(line)
    return "\n".join(lines)


def send_telegram_report(
    entries: List[dict],
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> bool:
    """
    Отправить агрегированный отчёт в Telegram.
    Токен и chat_id берутся из аргументов или из переменных окружения TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
    """
    if not entries:
        return False
    token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat:
        logger.warning("Telegram: не заданы TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID — отчёт не отправлен.")
        return False
    text = _format_report_message(entries)
    if len(text) > 4096:
        text = text[:4090] + "\n..."
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        import requests
        r = requests.post(url, json={"chat_id": chat, "text": text}, timeout=10)
        if not r.ok:
            logger.warning("Telegram: ошибка отправки %s — %s", r.status_code, r.text[:200])
            return False
        return True
    except Exception as e:
        logger.warning("Telegram: ошибка отправки — %s", e)
        return False
