# Reddit Life Simulator

> 🇷🇺 Russian version: [README_ru.md](README_ru.md)

[![Made by Alexander BotForge](https://img.shields.io/badge/Made%20by-Alexander%20BotForge-blue.svg)](https://github.com/alexanderbotforge)

An autonomous system for **long-term Reddit account simulation**.  
Behavior is visually and behaviorally indistinguishable from a real human.  
Ideal for running accounts safely for months without manual intervention — no aggressive actions, no growth obsession, just natural browsing rhythm.

---

## 🎯 Goal

Reddit Life Simulator (RLS) runs Reddit accounts in **full browser emulation** (Playwright).  
Each account:

- browses the feed without a fixed script — random session length, scroll, pauses  
- occasionally upvotes (1–2 per session, only after enough time on a post)  
- rarely subscribes to subreddits (only ones discovered naturally in the feed)  
- follows a timezone-based rhythm (weekdays vs weekends, fatigue after long sessions)  
- detects risks (captcha, redirects, anomalies) and backs off into cooldown  

Accounts are processed **one at a time** through a “life queue” — no parallel sessions, no correlation between accounts.

---

## ⚙️ How it works

When you run `rls.py`, the simulator:

1. Loads configuration from `.env` and account JSON files in `config/`  
2. Loads or creates account state (sessions, fatigue, risk level)  
3. Picks the next account from the queue (sorted by `account_id`)  
4. Launches **Playwright** with a persistent profile (per account)  
5. Opens Reddit, scrolls the feed with human-like pauses  
6. May upvote or subscribe, respecting per-session limits  
7. Detects risks (captcha, redirects) and increases cooldown if needed  
8. Saves state and moves to the next account  
9. Optionally sends a **daily Telegram report** at 23:58 (if configured)

**Reddit login:** Do not type username/password in the automated browser — Reddit often blocks that. Use **cookies export** from a normal Chrome session, or a Chrome profile directory.

---

## 🧱 Project structure

```text
reddit-life-simulator/
├── rls.py              # Main entry: life queue, CLI
├── browser.py          # Playwright emulation: profile, Reddit, scroll, upvote
├── behavior.py         # Fatigue, session duration, timezone rhythm
├── risk.py             # Cooldown, risk level
├── config.py           # Account configs, proxy validation
├── state.py            # Account state, summary
├── reporting.py        # Daily Telegram report
├── constants.py        # Limits, version, defaults
├── .env.example        # Template for secrets (copy to .env)
├── config/
│   └── account1.json.example   # Account config template
├── docs/
│   ├── README.md       # Full documentation (RU)
│   └── CHANGELOG.md
├── knowledge_base/     # Architecture, logic, decisions
├── tests/
└── requirements.txt
```

---

## ⚡ Quick start

1. **Clone the repo**
   ```bash
   git clone https://github.com/alexanderbotforge/reddit-life-simulator.git
   cd reddit-life-simulator
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configure environment variables**

   Copy `.env.example` to `.env` and fill in your values:

   ```env
   TELEGRAM_BOT_TOKEN=     # Optional: for daily report
   TELEGRAM_CHAT_ID=       # Optional: for daily report
   ```

   **Do not publish `.env`** — it’s ignored by Git.

4. **Add an account config**

   Copy `config/account1.json.example` to `config/account1.json` and edit:

   ```json
   {
     "account_id": "YourAccountName",
     "proxy": null,
     "timezone": "Europe/Kyiv",
     "language": "en",
     "region": "UA",
     "paused": false,
     "profile_dir": "",
     "cookies_file": "state/reddit_cookies_YourAccount.json"
   }
   ```

5. **Log in to Reddit via cookies** (recommended)

   - Log into Reddit in normal Chrome  
   - Export cookies with an extension (e.g. [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie))  
   - Save as `state/reddit_cookies_YourAccount.json`  
   - Set `cookies_file` in the account config  

6. **Run the simulator**

   ```bash
   python rls.py --dry-run                    # Test without browser
   python rls.py --config-dir config --state-dir state   # With browser
   python rls.py --no-headless                # Show browser window
   ```

---

## 📋 CLI options

| Option | Description |
|--------|-------------|
| `--dry-run` | Run life queue without launching browser |
| `--config-dir DIR` | Account configs directory (default: `config`) |
| `--state-dir DIR` | State and logs directory (default: `state`) |
| `--no-headless` | Show browser window instead of headless |
| `--send-daily-report` | Build and send daily Telegram report (run at 23:58) |
| `--daemon` | Loop life queue + daily report at 23:58 |
| `--daemon-interval-minutes N` | Interval between queue runs (default: 60) |

---

## 🧠 Requirements

- Python 3.9+  
- [Playwright](https://playwright.dev/python/)  
- [python-dotenv](https://pypi.org/project/python-dotenv/)  
- [requests](https://pypi.org/project/requests/) (for Telegram)

All dependencies are in `requirements.txt`.

---

## 🪵 Logging

Logs are written to the `logs/` folder.  
If it doesn’t exist, it will be created automatically.  
Sensitive data (proxy URLs, tokens) is masked in logs.

---

## 🧩 Limitations (v1.0)

- **One active account** at a time — processed sequentially  
- **No comments** — upvotes and subreddit subscribes only  
- **No API** — full browser emulation only  
- **Fixed proxy/timezone/language** per account — no switching mid-life  
- **Manual or daemon run** — no built-in scheduler beyond `--daemon`  
- **Reddit login** via cookies or Chrome profile — no typed credentials  

---

## 🛡️ GitHub safety

The repository is ready for public use:

- `.env`, `config/*.json`, `state/`, `logs/` are excluded via `.gitignore`  
- `.env.example` and `config/account1.json.example` provide safe templates  
- README includes setup and usage guide  

Never commit your real `.env` or account configs.

---

## 🧪 Tests

```bash
python -m pytest tests/ -v
```

Tests use `RLS_SKIP_BROWSER=1` — no real browser is launched.

---

## 👤 Author

**Alexander BotForge**  
Automation & analytics tools  
🔗 GitHub: [@alexanderbotforge](https://github.com/alexanderbotforge)  
💬 Telegram: [@alexanderbotforge](https://t.me/alexanderbotforge)

---

## 👥 Who is it for?

- Reddit account managers who need natural, low-risk activity  
- Developers experimenting with browser automation  
- Anyone wanting long-running account simulation without aggressive behavior  

---

## 🗺️ Possible future features

- Comment generation via AI module  
- Support for multiple concurrent accounts (with caution)  
- Proxy rotation  
- Custom session schedules  

---

## 📄 License

MIT
