# -*- coding: utf-8 -*-
# ===================== БЛОК 1: Заголовок =====================
# Reddit Life Simulator — главная точка входа (RLS)
# Версия: 1.0.3
# Описание: Очередь жизни, браузер (Playwright), Telegram-отчёт, ритм по таймзоне, демон. Отчёт в 23:58.
# Время разработки: 4h
# Последнее обновление: 2025-02-01
#
# Changelog:
# 1.0.0 (2025-02-01) — первоначальная версия.
# 1.0.1 (2025-02-01) — last_session_at, --send-daily-report (23:58), run_send_daily_report.
# 1.0.2 (2025-02-01) — таймзона в behavior, state_dir/max_upvotes в run_session, --daemon, маскировка прокси в логах.
# 1.0.3 (2025-02-01) — версия проекта 1.0.3 (исправления из CODE_REVIEW).
# ===================== КОНЕЦ БЛОКА 1 =====================

"""
Reddit Life Simulator (RLS) — автономная система имитации «жизни» Reddit-аккаунтов.
Главный файл: запуск очереди жизни, один активный аккаунт в момент времени.
"""

# Загрузка .env до остальных импортов (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID и др.)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from constants import (
    ACCOUNT_STATUS_ACTIVE,
    ACCOUNT_STATUS_PASSIVE,
    ACCOUNT_STATUS_SUSPENDED,
    DEFAULT_CONFIG_DIR,
    DEFAULT_LOGS_DIR,
    DEFAULT_STATE_DIR,
    PROJECT_VERSION,
)
from config import get_accounts_queue, mask_proxy_for_log, validate_proxy
from state import load_account_state, save_account_state, AccountState
from browser import run_session
from behavior import (
    should_skip_session_today,
    max_session_duration_seconds,
    max_upvotes_for_session,
    apply_fatigue_after_session,
)
from risk import is_in_cooldown, cooldown_end_iso, increase_risk_level, compute_cooldown_until_days
from reporting import append_to_summary, send_daily_report, DAILY_REPORT_HOUR, DAILY_REPORT_MINUTE

# Логирование
LOG_DIR = Path(DEFAULT_LOGS_DIR)
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "rls.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("rls")


def run_life_cycle(
    config_dir: str = DEFAULT_CONFIG_DIR,
    state_dir: str = DEFAULT_STATE_DIR,
    dry_run: bool = False,
    headless: bool = True,
) -> None:
    """
    Запустить один цикл очереди жизни: для каждого аккаунта (без паузы) загрузить состояние,
    при необходимости пропустить сессию или cooldown, иначе запустить одну сессию браузера,
    обновить состояние и сохранить.
    """
    queue = get_accounts_queue(config_dir)
    if not queue:
        logger.warning("Очередь жизни пуста (нет конфигов или все на паузе).")
        return
    logger.info("Очередь жизни: %d аккаунт(ов). Версия %s", len(queue), PROJECT_VERSION)
    for acc_config in queue:
        account_id = acc_config.account_id
        state = load_account_state(account_id, state_dir)
        if is_in_cooldown(state.cooldown_until):
            logger.info("Аккаунт %s в cooldown до %s — пропуск.", account_id, state.cooldown_until)
            state.daily_status = ACCOUNT_STATUS_SUSPENDED
            save_account_state(state, state_dir)
            append_to_summary(state, state_dir)
            continue
        if should_skip_session_today(state, acc_config.timezone):
            logger.info("Аккаунт %s — пропуск сессии сегодня (усталость/случайность).", account_id)
            state.daily_status = ACCOUNT_STATUS_PASSIVE
            save_account_state(state, state_dir)
            append_to_summary(state, state_dir)
            continue
        if dry_run:
            logger.info("Dry-run: аккаунт %s — сессия не запускается.", account_id)
            continue
        if not validate_proxy(acc_config.proxy):
            logger.warning("Аккаунт %s — неверный формат прокси %s, пропуск сессии.", account_id, mask_proxy_for_log(acc_config.proxy))
            continue
        max_duration = max_session_duration_seconds(state, acc_config.timezone)
        max_upvotes = max_upvotes_for_session(state)
        logger.info("Аккаунт %s: запуск сессии браузера (макс. %d с, до %d upvote)%s.", account_id, max_duration, max_upvotes, "" if headless else " [окно браузера видимо]")
        result = run_session(
            acc_config,
            max_duration_seconds=max_duration,
            state_dir=state_dir,
            max_upvotes=max_upvotes,
            headless=headless,
        )
        state.sessions_count += 1
        state.total_online_seconds += result.online_seconds
        state.upvotes_count += result.upvotes
        state.subscribes_count += result.subscribes
        state.fatigue_level = apply_fatigue_after_session(
            state, result.online_seconds, result.upvotes, result.subscribes
        )
        if result.risk_detected:
            state.risk_level = increase_risk_level(state.risk_level, result.risk_reason or "unknown")
            state.cooldown_until = cooldown_end_iso(compute_cooldown_until_days())
            state.daily_status = ACCOUNT_STATUS_SUSPENDED
            logger.warning("Аккаунт %s: риск '%s', cooldown до %s", account_id, result.risk_reason, state.cooldown_until)
            if (result.risk_reason or "").lower() == "captcha":
                logger.info("Подсказка: войдите в Reddit вручную один раз (python rls.py --no-headless), решите капчу, дождитесь главной; затем закройте и запускайте симулятор снова.")
        else:
            state.daily_status = ACCOUNT_STATUS_ACTIVE
        state.last_session_at = datetime.now(timezone.utc).isoformat()
        save_account_state(state, state_dir)
        append_to_summary(state, state_dir)
        logger.info(
            "Аккаунт %s: сессия завершена, онлайн %d с, upvote %d, подписки %d.",
            account_id, result.online_seconds, result.upvotes, result.subscribes,
        )


def run_daemon(
    config_dir: str = DEFAULT_CONFIG_DIR,
    state_dir: str = DEFAULT_STATE_DIR,
    interval_minutes: int = 60,
) -> None:
    """
    Режим демона: в цикле запускать очередь жизни и в 23:58 отправлять ежедневный отчёт.
    """
    import time as _time
    logger.info("Демон запущен: интервал %d мин, отчёт в %02d:%02d.", interval_minutes, DAILY_REPORT_HOUR, DAILY_REPORT_MINUTE)
    while True:
        now = datetime.now(timezone.utc)
        if now.hour == DAILY_REPORT_HOUR and now.minute >= DAILY_REPORT_MINUTE:
            run_send_daily_report(state_dir)
            _time.sleep(120)
            continue
        run_life_cycle(config_dir=config_dir, state_dir=state_dir, dry_run=False)
        _time.sleep(interval_minutes * 60)


def run_send_daily_report(state_dir: str = DEFAULT_STATE_DIR) -> bool:
    """Отправить ежедневный отчёт (вызывать в 23:58 по расписанию, например cron)."""
    ok = send_daily_report(state_dir)
    if ok:
        logger.info("Ежедневный отчёт отправлен (записи за сегодня).")
    else:
        logger.warning("Ежедневный отчёт не отправлен (нет записей за сегодня).")
    return ok


def main() -> int:
    """Точка входа CLI."""
    parser = argparse.ArgumentParser(description="Reddit Life Simulator — очередь жизни аккаунтов.")
    parser.add_argument("--config-dir", default=DEFAULT_CONFIG_DIR, help="Каталог конфигов аккаунтов")
    parser.add_argument("--state-dir", default=DEFAULT_STATE_DIR, help="Каталог состояния и отчётов")
    parser.add_argument("--dry-run", action="store_true", help="Не запускать браузер, только логика очереди")
    parser.add_argument(
        "--send-daily-report",
        action="store_true",
        help="Отправить ежедневный Telegram-отчёт (запускать в 23:58 по расписанию)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Режим демона: цикл очередь жизни + отчёт в 23:58",
    )
    parser.add_argument(
        "--daemon-interval-minutes",
        type=int,
        default=60,
        help="Интервал цикла демона в минутах (по умолчанию 60)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Показать окно браузера (иначе браузер работает в фоне без окна)",
    )
    args = parser.parse_args()
    if args.send_daily_report:
        run_send_daily_report(state_dir=args.state_dir)
        return 0
    if args.daemon:
        run_daemon(
            config_dir=args.config_dir,
            state_dir=args.state_dir,
            interval_minutes=max(1, args.daemon_interval_minutes),
        )
        return 0
    headless = os.environ.get("RLS_HEADLESS", "1") == "1" and not args.no_headless
    run_life_cycle(config_dir=args.config_dir, state_dir=args.state_dir, dry_run=args.dry_run, headless=headless)
    return 0


if __name__ == "__main__":
    sys.exit(main())
