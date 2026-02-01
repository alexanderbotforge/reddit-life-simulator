# -*- coding: utf-8 -*-
# ===================== БЛОК 1: Заголовок =====================
# Reddit Life Simulator — браузерная эмуляция
# Версия: 1.0.3
# Описание: Реальный браузер (Playwright) с профилем на аккаунт, прокси, Reddit, скролл, upvote, детекция рисков.
# Время разработки: 3h
# Последнее обновление: 2025-02-01
#
# Changelog:
# 1.0.0 (2025-02-01) — первоначальная версия (заглушка).
# 1.0.2 (2025-02-01) — Playwright: профиль, прокси, Reddit, скролл, upvote, подписка, детекция рисков.
# 1.0.3 (2025-02-01) — try/finally для гарантированного context.close() при исключении.
# ===================== КОНЕЦ БЛОКА 1 =====================

"""Браузерная эмуляция: реальный браузер (Playwright) с профилем на аккаунт."""

import json
import logging
import os
import random
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple

from config import AccountConfig
from constants import DEFAULT_STATE_DIR, UPVOTES_PER_SESSION_MAX, SUBSCRIBES_PER_SESSION_MAX

logger = logging.getLogger(__name__)

REDDIT_URL = "https://www.reddit.com/"
RISK_LOAD_TIMEOUT_MS = 45000
MIN_VIEW_SECONDS_BEFORE_UPVOTE = 3
SCROLL_PAUSE_MIN = 1
SCROLL_PAUSE_MAX = 8


@dataclass
class SessionResult:
    """Результат одной сессии браузера."""

    online_seconds: int = 0
    upvotes: int = 0
    subscribes: int = 0
    risk_detected: bool = False
    risk_reason: Optional[str] = None
    extra: dict = field(default_factory=dict)


def _normalize_proxy(proxy: Optional[str]) -> Optional[dict]:
    """Привести прокси к формату Playwright: {"server": "http://host:port"} или с user/pass."""
    if not proxy or not str(proxy).strip():
        return None
    s = str(proxy).strip()
    if re.match(r"^https?://", s) or re.match(r"^socks5://", s):
        return {"server": s}
    if ":" in s and "@" in s:
        return {"server": "http://" + s.split("@")[-1]}
    if ":" in s:
        return {"server": "http://" + s}
    return {"server": "http://" + s + ":80"}


def _profile_dir(account_config: AccountConfig, state_dir: Optional[str] = None) -> Path:
    """Каталог профиля браузера для аккаунта."""
    if account_config.profile_dir:
        return Path(account_config.profile_dir)
    state_dir = state_dir or DEFAULT_STATE_DIR
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in account_config.account_id)[:30]
    return Path(state_dir) / "browser_profiles" / safe


def _load_cookies_from_file(cookies_path: str) -> List[dict]:
    """
    Загрузить cookies из JSON-файла (экспорт из Chrome через расширение EditThisCookie / Get cookies.txt и т.п.).
    Формат: [{"name": "...", "value": "...", "domain": ".reddit.com", "path": "/"}, ...]
    """
    path = Path(cookies_path)
    if not path.is_file():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Не удалось загрузить cookies из %s: %s", cookies_path, e)
        return []
    if not isinstance(data, list):
        return []
    cookies = []
    for c in data:
        if not isinstance(c, dict) or "name" not in c or "value" not in c:
            continue
        domain = c.get("domain") or c.get("domainName") or ".reddit.com"
        if not domain.startswith(".") and "reddit" in domain:
            domain = "." + domain.lstrip("*")
        cookies.append({
            "name": str(c["name"]),
            "value": str(c["value"]),
            "domain": domain,
            "path": str(c.get("path") or "/"),
        })
    return cookies


def _detect_risk(page: Any, start_url: str) -> Tuple[bool, Optional[str]]:
    """Проверить страницу на признаки риска: редирект на капчу (по URL), уход с Reddit."""
    try:
        url = page.url
        # Капча — только если редирект на URL капчи (страница входа reddit.com/login содержит «captcha» в HTML — не считаем)
        if "captcha" in url.lower() or "g-recaptcha" in url.lower():
            return True, "captcha"
        if "reddit.com" not in url and "redd.it" not in url:
            return True, "redirect"
        # Не проверяем body на «captcha»/«verify you are human» — на login/signup это даёт ложные срабатывания
    except Exception as e:
        logger.warning("Ошибка при проверке риска: %s", e)
    return False, None


def run_session(
    account_config: AccountConfig,
    max_duration_seconds: Optional[int] = None,
    on_risk: Optional[Callable[[str], None]] = None,
    state_dir: Optional[str] = None,
    max_upvotes: Optional[int] = None,
    headless: bool = True,
) -> SessionResult:
    """
    Запустить одну сессию браузера: Reddit, скролл, паузы, изредка upvote (1–2), очень редко подписка.
    При обнаружении риска возвращает risk_detected=True.
    """
    if os.environ.get("RLS_SKIP_BROWSER") == "1":
        return SessionResult()
    max_duration_seconds = max_duration_seconds or 300
    max_upvotes = max_upvotes if max_upvotes is not None else UPVOTES_PER_SESSION_MAX
    result = SessionResult()
    profile_path = _profile_dir(account_config, state_dir)
    logger.info("Сессия: браузер для %s, профиль %s, макс. %d с.", account_config.account_id, profile_path, max_duration_seconds)
    profile_path.mkdir(parents=True, exist_ok=True)
    proxy_dict = _normalize_proxy(account_config.proxy)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright не установлен. Запустите: pip install playwright && playwright install chromium")
        return result

    try:
        with sync_playwright() as p:
            # Аргументы Chromium, чтобы браузер меньше походил на автоматизированный (Reddit иначе может отдавать «неверный логин/пароль»)
            chromium_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ]
            kwargs = {
                "headless": headless,
                "locale": (account_config.language or "en") + "-US",
                "viewport": {"width": 1280, "height": 800},
                "ignore_https_errors": True,
                "args": chromium_args,
            }
            if proxy_dict:
                kwargs["proxy"] = proxy_dict
            use_chrome = os.environ.get("RLS_USE_CHROME") == "1"
            if use_chrome:
                kwargs["channel"] = "chrome"
                logger.info("Используется системный Google Chrome (RLS_USE_CHROME=1).")
            try:
                context = p.chromium.launch_persistent_context(str(profile_path.resolve()), **kwargs)
            except Exception as launch_err:
                # Системный Chrome часто сразу закрывается при запуске с флагами автоматизации — fallback на Chromium
                if use_chrome and ("closed" in str(launch_err).lower() or "TargetClosedError" in type(launch_err).__name__):
                    logger.warning("Системный Chrome закрылся при запуске (известная особенность), используем Chromium.")
                    kwargs.pop("channel", None)
                    context = p.chromium.launch_persistent_context(str(profile_path.resolve()), **kwargs)
                else:
                    raise
            try:
                page = context.pages[0] if context.pages else context.new_page()
                if not context.pages:
                    page.goto(REDDIT_URL, wait_until="domcontentloaded", timeout=RISK_LOAD_TIMEOUT_MS)
                else:
                    try:
                        page.goto(REDDIT_URL, wait_until="domcontentloaded", timeout=RISK_LOAD_TIMEOUT_MS)
                    except Exception as e:
                        if "timeout" in str(e).lower() or "Timeout" in str(e):
                            result.risk_detected = True
                            result.risk_reason = "timeout"
                            if on_risk:
                                on_risk("timeout")
                            return result
                        raise

                # Подставить cookies из файла (экспорт из Chrome), чтобы быть уже залогиненным
                if account_config.cookies_file:
                    cookies = _load_cookies_from_file(account_config.cookies_file)
                    if cookies:
                        context.add_cookies(cookies)
                        page.reload(wait_until="domcontentloaded")
                        logger.info("Загружены cookies из %s (%d шт.), перезагрузка страницы.", account_config.cookies_file, len(cookies))
                    else:
                        logger.warning("Файл cookies пустой или не найден: %s", account_config.cookies_file)
                else:
                    logger.warning(
                        "cookies_file не указан — не вводите логин/пароль в окне симулятора (риск блокировки Reddit). "
                        "Войдите в Reddit в обычном Chrome, экспортируйте cookies, укажите cookies_file в config — см. README."
                    )

                risk_ok, risk_reason = _detect_risk(page, REDDIT_URL)
                if risk_ok:
                    result.risk_detected = True
                    result.risk_reason = risk_reason
                    if on_risk:
                        on_risk(risk_reason or "unknown")
                    return result

                start = time.monotonic()
                upvotes_done = 0
                subscribes_done = 0
                last_log_minute = -1
                logger.info("Reddit загружен, начинаем цикл (скролл, паузы, до %d upvote, макс. %d с).", max_upvotes, max_duration_seconds)

                while (time.monotonic() - start) < max_duration_seconds:
                    elapsed = int(time.monotonic() - start)
                    result.online_seconds = elapsed
                    # Лог раз в минуту, чтобы было видно, что сессия не зависла
                    minute = elapsed // 60
                    if minute > last_log_minute and minute > 0:
                        last_log_minute = minute
                        logger.info("Сессия %s: прошло %d мин, upvote %d, подписки %d.", account_config.account_id, minute, upvotes_done, subscribes_done)

                    risk_ok, risk_reason = _detect_risk(page, REDDIT_URL)
                    if risk_ok:
                        result.risk_detected = True
                        result.risk_reason = risk_reason
                        if on_risk:
                            on_risk(risk_reason or "unknown")
                        break

                    pause = random.uniform(SCROLL_PAUSE_MIN, SCROLL_PAUSE_MAX)
                    time.sleep(pause)
                    result.online_seconds = int(time.monotonic() - start)

                    try:
                        page.evaluate("window.scrollBy(0, window.innerHeight * 0.6)")
                    except Exception:
                        pass

                    if upvotes_done < max_upvotes and random.random() < 0.15:
                        try:
                            upvote_buttons = page.query_selector_all('button[aria-label="Upvote"], button[aria-label="upvote"], [data-click-id="upvote"], shreddit-post button[aria-label="Upvote"]')
                            if upvote_buttons:
                                btn = random.choice(upvote_buttons[:5])
                                btn.scroll_into_view_if_needed()
                                time.sleep(max(MIN_VIEW_SECONDS_BEFORE_UPVOTE, random.uniform(2, 5)))
                                btn.click()
                                upvotes_done += 1
                                result.upvotes = upvotes_done
                                logger.info("Upvote выполнен (%d/%d за сессию).", upvotes_done, max_upvotes)
                                time.sleep(random.uniform(1, 3))
                        except Exception as e:
                            logger.debug("Upvote не выполнен: %s", e)

                    if subscribes_done < SUBSCRIBES_PER_SESSION_MAX and random.random() < 0.03:
                        try:
                            join_btn = page.query_selector('button:has-text("Join"), button:has-text("Join r/")')
                            if join_btn:
                                join_btn.scroll_into_view_if_needed()
                                time.sleep(random.uniform(1, 3))
                                join_btn.click()
                                subscribes_done += 1
                                result.subscribes = subscribes_done
                                logger.info("Подписка на сабреддит выполнена (%d за сессию).", subscribes_done)
                                time.sleep(random.uniform(1, 2))
                        except Exception:
                            pass

                result.online_seconds = int(time.monotonic() - start)
            finally:
                try:
                    context.close()
                except KeyboardInterrupt:
                    logger.info("Прервано пользователем (Ctrl+C), закрытие браузера.")
                    raise
                except Exception as close_err:
                    logger.debug("Закрытие контекста браузера: %s", close_err)
    except Exception as e:
        logger.exception("Ошибка сессии браузера для %s: %s", account_config.account_id, e)
        if "timeout" in str(e).lower() or "Timeout" in str(e):
            result.risk_detected = True
            result.risk_reason = "timeout"
    return result


def detect_risk_in_page() -> Tuple[bool, Optional[str]]:
    """
    Проверить текущую страницу на признаки риска (вызов без контекста — заглушка).
    В контексте сессии используется _detect_risk(page, url).
    """
    return False, None
