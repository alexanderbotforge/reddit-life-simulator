# -*- coding: utf-8 -*-
"""Pytest fixtures и настройки: отключение реального браузера в тестах."""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def skip_browser_in_tests():
    """В тестах не запускать реальный Playwright-браузер."""
    os.environ["RLS_SKIP_BROWSER"] = "1"
