# External Integrations

**Analysis Date:** 2026-06-08

## APIs & External Services

**No external APIs used.** This is a self-contained system with no outbound API calls. All data lives in the local SQLite database.

## Content Delivery Networks (CDNs)

**Bootstrap 5.3.0:**
- CSS: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css`
- JS: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js`
- Loaded in: `my-jxc/app/templates/base.html`

**Bootstrap Icons 1.10.0:**
- CSS: `https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css`
- Loaded in: `my-jxc/app/templates/base.html`

**Chart.js 4.4.0:**
- JS: `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`
- Loaded in: `my-jxc/app/templates/base.html`
- Also loaded individually in report templates: `my-jxc/app/templates/report/sales_ranking.html`, `my-jxc/app/templates/report/customer_statistics.html`, `my-jxc/app/templates/report/supplier_statistics.html`, `my-jxc/app/templates/report/index.html`, `my-jxc/app/templates/report/daily_report.html`, `my-jxc/app/templates/finance/profit_analysis.html`

**Risk:** CDN dependency means the app requires internet access for full functionality. No local fallbacks configured.

## Data Storage

**Database:**
- SQLite (file-based, single-user)
- Default path: `my-jxc/instance/store.db`
- Connection: `sqlite:///instance/store.db` (configurable via `DATABASE_URL` env var)
- Client: SQLAlchemy 2.0.49 via Flask-SQLAlchemy 3.0.5
- No connection pooling configured (SQLite default)
- In-memory for tests: `sqlite:///:memory:` (TestConfig)

**Schema Management:**
- Flask-Migrate 4.0.5 (Alembic) initialized but no `migrations/` directory exists
- Manual migrations via `my-jxc/scripts/migrate_db.py` (direct ALTER TABLE)
- Schema changes applied via `db.create_all()` in `my-jxc/scripts/reset_db.py`

**File Storage:**
- Local filesystem only
- Upload directory: `my-jxc/app/static/uploads/` (created automatically by `my-jxc/app/__init__.py`)
- Max upload size: 16MB (`MAX_CONTENT_LENGTH` in `my-jxc/config.py`)
- Product images stored in uploads directory
- Backup files: `my-jxc/backups/` (SQLite DB copies)

**Caching:**
- None. No Redis, Memcached, or in-memory cache layer.

## Authentication & Identity

**Auth Provider:**
- Custom implementation using Flask-Login 0.6.2

**Implementation:**
- Session-based authentication with `remember me` cookie (30-day duration)
- Password hashing via Werkzeug (`generate_password_hash`/`check_password_hash`)
- Login: `my-jxc/app/routes/auth.py` — `auth.login` route
- Registration: `my-jxc/app/routes/auth.py` — `auth.register` route
- Logout: POST-only (`my-jxc/app/routes/auth.py`)
- User model: `my-jxc/app/models/user.py` (inherits `UserMixin`)
- Role-based access: `admin` vs `user` roles (`my-jxc/app/constants.py:UserRole`)
- Admin check: `_require_admin()` helper calls `abort(403)`

**Session Configuration:**
- `SESSION_COOKIE_HTTPONLY = True`
- `SESSION_COOKIE_SAMESITE = 'Lax'`
- `SESSION_PROTECTION = 'strong'`
- `SESSION_COOKIE_SECURE = True` (production), `False` (development)

## Security

**CSRF Protection:**
- Flask-WTF CSRFProtect enabled globally (`my-jxc/app/__init__.py`)
- Custom headers: `X-CSRFToken`, `X-CSRF-Token` (`my-jxc/config.py`)
- Disabled in test config: `WTF_CSRF_ENABLED = False`
- CSRF token in meta tag: `my-jxc/app/templates/base.html`

**Security Headers:**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- Applied via `@app.after_request` in `my-jxc/app/__init__.py`

**Secret Management:**
- `SECRET_KEY` auto-generated to `my-jxc/instance/.flask_secret_key` if not set via env var
- `.env` file: Not present (no `.env` files detected)

## Monitoring & Observability

**Error Tracking:**
- None. No Sentry, Bugsnag, or similar service.

**Logs:**
- Python `print()` statements to stdout (not structured logging)
- Flask request logging via Werkzeug (development mode)
- User action logging to database: `Log` model in `my-jxc/app/models/user.py` (login, logout, password change, email change)

**Audit Trail:**
- `StockLog` model in `my-jxc/app/models/inventory.py` — immutable audit of all inventory changes
- `Log` model in `my-jxc/app/models/user.py` — user action log (login, profile changes)

## CI/CD & Deployment

**Hosting:**
- Standalone Python process (no containerization)
- Desktop/laptop deployment target
- LAN access via `0.0.0.0` binding
- Optional mDNS for `.local` domain discovery (`my-jxc/run.py:28-58`)

**CI Pipeline:**
- None detected. No `.github/workflows/`, `.gitlab-ci.yml`, or similar.

**Build Scripts:**
- `my-jxc/scripts/build_linux.sh` — PyInstaller Linux build
- `my-jxc/scripts/build_windows.bat` — PyInstaller Windows build

## Database Backup & Restore

**Backup:**
- Manual backup via web UI: `my-jxc/app/routes/system.py:backup()` / `create_backup()`
- Creates SQLite file copies in `my-jxc/backups/` directory
- Downloadable via `export_db()` endpoint

**Restore:**
- Manual restore via web UI: `my-jxc/app/routes/system.py:restore_backup()`
- Upload `.db` file to replace current database

## Excel Import/Export

**Export:**
- openpyxl 3.1.2 generates `.xlsx` files
- Used in: `my-jxc/app/routes/product.py`, `my-jxc/app/routes/inventory.py`, `my-jxc/app/routes/finance.py`, `my-jxc/app/routes/report.py`, `my-jxc/app/routes/partner.py`
- Download via `send_file()` with `Content-Disposition` header
- Filename encoding: `urllib.parse.quote()` for Chinese filenames

**Import:**
- Product import from `.xlsx`: `my-jxc/app/routes/product.py`
- Partner import from `.xlsx`: `my-jxc/app/routes/partner.py`
- Uses `openpyxl.load_workbook()` to parse uploaded files

## Network Services

**mDNS (optional):**
- zeroconf library for `.local` domain discovery
- Service name: `myjxc._http._tcp.local.`
- Registration: `my-jxc/run.py:28-58`
- Graceful degradation if zeroconf not installed

**No outbound HTTP calls:**
- No external API integrations
- No webhook receivers or senders
- No email sending (SMTP not configured)

## Environment Configuration

**Required env vars:**
- `FLASK_ENV` — Config class selection (default: `production`)
- `SECRET_KEY` — Auto-generated if not set
- `DATABASE_URL` — SQLite path (default: `sqlite:///instance/store.db`)

**Optional env vars:**
- `FLASK_DEBUG` — Enable debug mode (`1` to enable)
- `MODE` — Server mode (`dev` or `prod`)
- `PORT` — Server port (default: 5000)
- `SECURE_COOKIES` — Enable HTTPS cookies in production (`1` to enable)

**Secrets location:**
- `my-jxc/instance/.flask_secret_key` — Auto-generated Flask secret
- No `.env` file present
- No external secrets manager

---

*Integration audit: 2026-06-08*
