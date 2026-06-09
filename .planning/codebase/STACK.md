# Technology Stack

**Analysis Date:** 2026-06-08

## Languages

**Primary:**
- Python 3.13 — All backend logic, routes, models, utilities (`my-jxc/app/`, `my-jxc/run.py`, `my-jxc/config.py`)

**Secondary:**
- HTML/Jinja2 — Server-side rendered templates (`my-jxc/app/templates/`)
- JavaScript (ES6) — Client-side interactivity, AJAX, chart rendering (`my-jxc/app/static/js/main.js`, `my-jxc/app/static/js/charts.js`)
- CSS — Custom styles (`my-jxc/app/static/css/style.css`)

## Runtime

**Environment:**
- Python 3.13+ (venv at `my-jxc/venv/`)
- Flask development server (default port 5000, `host='0.0.0.0'`)
- Waitress WSGI server for production mode (`MODE=prod`)

**Package Manager:**
- pip
- Lockfile: missing (no `requirements.lock` or `pip freeze` output)

**Server Modes:**
- Development: Flask built-in server (`python run.py` or `MODE=dev python run.py`)
- Production: Waitress (`MODE=prod python run.py`)
- `FLASK_DEBUG=1` enables debug mode in dev mode

## Frameworks

**Core:**
- Flask 2.3.3 — Web framework, application factory pattern (`my-jxc/app/__init__.py:create_app()`)
- Flask-SQLAlchemy 3.0.5 — ORM integration, `db` singleton (`my-jxc/app/__init__.py`)
- SQLAlchemy 2.0.49 — Database ORM engine
- Flask-Login 0.6.2 — Session-based authentication (`login_manager` in `my-jxc/app/__init__.py`)
- Flask-WTF 1.1.1 — CSRF protection and form handling (`CSRFProtect` in `my-jxc/app/__init__.py`)
- Flask-Bootstrap 3.3.7.1 — Bootstrap integration (Bootswatch theme: flatly)
- Flask-Migrate 4.0.5 — Alembic database migrations (`my-jxc/app/__init__.py`)

**Testing:**
- pytest — Test runner (`my-jxc/pytest.ini`)
- Selenium + Chromium — E2E browser tests (`my-jxc/tests/e2e/conftest.py`)

**Build/Dev:**
- PyInstaller — Desktop executable packaging (`my-jxc/scripts/build_linux.sh`, `my-jxc/scripts/build_windows.bat`)

## Key Dependencies

**Critical:**
- `Flask==2.3.3` — Core web framework
- `Flask-SQLAlchemy==3.0.5` — ORM bridge
- `SQLAlchemy==2.0.49` — ORM engine (all DB operations)
- `Flask-Login==0.6.2` — Authentication sessions
- `Flask-WTF==1.1.1` — Form validation and CSRF
- `Werkzeug==2.3.7` — WSGI utilities, password hashing (`set_password`/`check_password`)
- `WTForms==3.0.1` — Form field definitions (`my-jxc/app/forms.py`)
- `waitress==3.0.2` — Production WSGI server

**Infrastructure:**
- `openpyxl==3.1.2` — Excel file generation for reports/exports (used in `my-jxc/app/routes/product.py`, `my-jxc/app/routes/inventory.py`, `my-jxc/app/routes/finance.py`, `my-jxc/app/routes/report.py`)
- `python-dotenv==1.0.0` — Environment variable loading
- `email_validator==2.3.0` — Email field validation in WTForms

**Optional:**
- `zeroconf` — mDNS service discovery for LAN access (`my-jxc/run.py:28-58`)
- `requests` — HTTP client (used only in E2E test setup: `my-jxc/tests/e2e/conftest.py`)

## Frontend Stack

**CSS Framework:**
- Bootstrap 5.3.0 — loaded from CDN (`my-jxc/app/templates/base.html`)
- Bootswatch Flatly theme — configured via `BOOTSTRAP_BOOTSWATCH_THEME` in `my-jxc/config.py`
- Bootstrap Icons 1.10.0 — loaded from CDN (`my-jxc/app/templates/base.html`)

**JavaScript:**
- jQuery 3.6.0 — loaded from CDN (`my-jxc/app/templates/base.html`)
- Chart.js 4.4.0 — loaded from CDN (`my-jxc/app/templates/base.html`, `my-jxc/app/static/js/charts.js`)
- Vanilla JS class-based components (`EntitySearcher` in `my-jxc/app/static/js/main.js`)

**Custom Assets:**
- `my-jxc/app/static/js/main.js` — Entity search, form helpers, AJAX utilities
- `my-jxc/app/static/js/charts.js` — Chart.js wrapper functions for sales trends, stock overview
- `my-jxc/app/static/css/style.css` — Custom styles

## Configuration

**Environment Variables:**
- `FLASK_ENV` — Selects config class: `development`, `production`, `test` (default: `production`)
- `SECRET_KEY` — Flask secret; auto-generated to `my-jxc/instance/.flask_secret_key` if not set
- `DATABASE_URL` — Override SQLite path; defaults to `sqlite:///instance/store.db`
- `FLASK_DEBUG` — Set to `1` to enable debug mode
- `MODE` — Server mode: `dev` (Flask) or `prod` (Waitress)
- `PORT` — Server port (default: 5000)
- `SECURE_COOKIES` — Set to `1` to enable HTTPS cookie flags in production

**Config Classes:**
- `Config` — Base config with secure cookie settings (`my-jxc/config.py`)
- `DevelopmentConfig(Config)` — DEBUG=True, relaxed cookie security
- `ProductionConfig(Config)` — DEBUG=False, configurable via `SECURE_COOKIES`
- `TestConfig(Config)` — TESTING=True, CSRF disabled, in-memory SQLite

**Build:**
- `my-jxc/scripts/build_linux.sh` — Linux build script (PyInstaller)
- `my-jxc/scripts/build_windows.bat` — Windows build script (PyInstaller)
- `my-jxc/scripts/migrate_db.py` — Manual SQLite ALTER TABLE migrations
- `my-jxc/scripts/reset_db.py` — Drop all tables, recreate, seed test data

## Platform Requirements

**Development:**
- Python 3.13+
- pip for dependency installation
- Virtual environment recommended (`python -m venv venv`)
- Chromium/Chrome browser for E2E tests (Selenium)

**Production:**
- Standalone Python process (`python run.py`)
- Waitress WSGI server (installed via requirements.txt)
- Can be packaged as desktop executable via PyInstaller
- Supports LAN access with optional mDNS (zeroconf) for `.local` domain discovery
- No reverse proxy configured (Waitress serves directly)

---

*Stack analysis: 2026-06-08*
