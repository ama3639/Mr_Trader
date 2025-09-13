# Copilot Coding Agent Instructions for MrTrader Bot

## Project Overview
- **MrTrader Bot** is a modular Telegram bot for crypto technical analysis and trading signals, using Python 3.8+.
- The architecture is layered: **handlers** (Telegram entry), **managers** (business logic), **core** (config/cache/db), **api** (external APIs), **models** (data), **utils** (helpers), **templates** (UI), **scripts** (ops), **tests** (unit tests).
- Data flows: Telegram → handlers → managers → core/api/models → data/logs.
- Key files: `main.py` (entry), `handlers/`, `managers/`, `core/`, `api/`, `models/`, `utils/`, `config/`.

## Key Conventions & Patterns
- **Caching:** Use `core/cache.py` for 60s smart cache on signals.
- **Config:** All config in `config/` (env, API servers, dev/prod JSONs). Use `core/config.py` to access.
- **Database:** SQLite via `database/database_manager.py`. Use managers for all DB access.
- **Payments:** Integrate via `managers/payment_manager.py` and `api/api_client.py`.
- **User/Package/Signal Models:** See `models/` for all data structures.
- **Logging:** Use `utils/logger.py` for all logs. Log files in `logs/`.
- **Validation:** Use `utils/validators.py` for all input checks.
- **Admin/Referrals:** Managed via `managers/admin_manager.py` and `managers/referral_manager.py`.
- **Reports:** Use `managers/report_manager.py` and `templates/reports.py`.

## Developer Workflows
- **Run bot:** `python main.py` (ensure config and DB exist)
- **Setup env:** `python scripts/setup_environment.py`
- **Migrate DB:** `python scripts/migrate_database.py`
- **Backup:** `python scripts/backup_data.py`
- **Health check:** `python scripts/health_check.py`
- **Clean logs:** `python scripts/cleanup_logs.py`
- **Tests:** Place in `tests/`, run with `pytest` (see `pytest.ini`)
- **Dev requirements:** `pip install -r requirements-dev.txt`

## Integration & External
- **APIs:** All external API calls via `api/api_client.py` (config in `config/api_servers_config.json`).
- **Payments:** ZarinPal, Mellat, Crypto supported (see payment manager/client).
- **Telegram:** Handlers in `handlers/`, UI in `templates/`.

## Project-Specific Practices
- **Git Flow:** Use `feature/*`, `release/*`, `hotfix/*`, `develop`, `main` branches. See README for details.
- **Access control:** All user/package access via managers, not direct DB.
- **Rate limiting:** Enforced in managers using cache and package info.
- **Sensitive data:** Store only in `config/` or `.env`, never in code.
- **All new features:** Add tests in `tests/` and update docs in `docs/`.

## Examples
- To add a new strategy: implement in `managers/strategy_manager.py`, add model if needed, update `templates/` for UI, and add tests.
- To add a new payment gateway: extend `api/api_client.py` and `managers/payment_manager.py`.

## References
- See `README.md` for full architecture, features, and workflow details.
- See `config/` for all environment and API configs.
- See `scripts/` for ops/maintenance tasks.

---
For any unclear patterns, check the README or ask for clarification in the docs directory.
