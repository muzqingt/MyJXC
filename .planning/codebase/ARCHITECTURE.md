<!-- refreshed: 2026-06-08 -->
# Architecture

**Analysis Date:** 2026-06-08

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        Flask Web Application                            │
│                  (Jinja2 Templates + Bootstrap 5)                       │
│  `my-jxc/app/__init__.py`  create_app()                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐     │
│  │    Auth      │ │   Product   │ │   Partner   │ │   Purchase   │     │
│  │  Blueprint   │ │  Blueprint  │ │  Blueprint  │ │  Blueprint   │     │
│  │ `routes/     │ │ `routes/    │ │ `routes/    │ │ `routes/     │     │
│  │  auth.py`    │ │  product.py`│ │  partner.py`│ │  purchase.py`│     │
│  └──────┬───────┘ └──────┬──────┘ └──────┬──────┘ └──────┬───────┘     │
│         │                │                │                │            │
│  ┌──────┴───────┐ ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴───────┐    │
│  │    Sales      │ │  Inventory  │ │   Finance   │ │    Report    │    │
│  │  Blueprint   │ │  Blueprint  │ │  Blueprint  │ │  Blueprint   │    │
│  │ `routes/     │ │ `routes/    │ │ `routes/    │ │ `routes/     │    │
│  │  sales.py`   │ │  inventory` │ │  finance.py`│ │  report.py`  │    │
│  └──────┬───────┘ └──────┬──────┘ └──────┬──────┘ └──────┬───────┘    │
│         │                │                │                │            │
│  ┌──────┴───────┐ ┌──────┴──────┐                                      │
│  │    Main      │ │   System    │                                      │
│  │  Blueprint   │ │  Blueprint  │                                      │
│  │ `routes/     │ │ `routes/    │                                      │
│  │  main.py`    │ │  system.py` │                                      │
│  └──────┬───────┘ └──────┬──────┘                                      │
├─────────┴────────────────┴──────────────────────────────────────────────┤
│                        Data / Logic Layer                                │
│                                                                         │
│  ┌──────────────────────┐  ┌─────────────────────────────────────────┐ │
│  │  SQLAlchemy Models   │  │        Utility Functions                │ │
│  │  `app/models/`       │  │  `app/utils.py` + `app/utils_order.py` │ │
│  │  (18 tables, 9 files)│  │  (Decimal, balance, order#, Excel)     │ │
│  └──────────────────────┘  └─────────────────────────────────────────┘ │
│  ┌──────────────────────┐  ┌─────────────────────────────────────────┐ │
│  │  WTForms Forms       │  │        Constants                       │ │
│  │  `app/forms.py`      │  │  `app/constants.py`                    │ │
│  └──────────────────────┘  └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────┤
│                        SQLite Database                                   │
│                        `instance/store.db`                              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| App Factory | Create Flask app, init extensions, register 10 blueprints, set security headers, register error handlers | `my-jxc/app/__init__.py` |
| Entry Point | Start server, init DB with defaults (admin/warehouse/category), mDNS registration, shell context | `my-jxc/run.py` |
| Config | Environment-based config (dev/prod/test), DB URI, security settings, CSRF, cookie policies | `my-jxc/config.py` |
| Auth Blueprint | Login, register, logout, profile, password/email change | `my-jxc/app/routes/auth.py` |
| Product Blueprint | CRUD products + categories, product price API, image upload, import/export | `my-jxc/app/routes/product.py` |
| Partner Blueprint | CRUD suppliers, customers, warehouses, import from Excel | `my-jxc/app/routes/partner.py` |
| Purchase Blueprint | Purchase orders, stock-in docs, purchase returns, quick stock-in, payments | `my-jxc/app/routes/purchase.py` |
| Sales Blueprint | Sales orders, stock-out docs, sales returns, quick stock-out, receipts | `my-jxc/app/routes/sales.py` |
| Inventory Blueprint | Stock overview, per-warehouse stock, stock check (adjust), transfer, logs, Excel export | `my-jxc/app/routes/inventory.py` |
| Finance Blueprint | Receipts, payments, expenses, AR/AP search, profit analysis | `my-jxc/app/routes/finance.py` |
| Report Blueprint | Inventory reports, sales ranking, customer/supplier statistics, daily report | `my-jxc/app/routes/report.py` |
| System Blueprint | User management (admin-only), backup/restore, settings, operation logs | `my-jxc/app/routes/system.py` |
| Main Blueprint | Dashboard KPIs, chart data APIs (sales trend, stock overview, finance summary) | `my-jxc/app/routes/main.py` |
| Utils | Decimal conversion, atomic balance ops, order number generation, stock logging, Excel styling | `my-jxc/app/utils.py` |
| Order Utils | Stock log creation, reference ID matching for comma-separated fields, form rebuild helpers | `my-jxc/app/utils_order.py` |
| Constants | OrderStatus, ChangeType, PaymentMethod, UserRole enums with label methods | `my-jxc/app/constants.py` |
| Forms | WTForms form classes for all CRUD operations (login, register, product, partner, stock, finance) | `my-jxc/app/forms.py` |

## Pattern Overview

**Overall:** Flask Application Factory with Blueprint-based modular monolith

**Key Characteristics:**
- No service layer -- all business logic lives directly in route handlers
- SQLAlchemy ORM models with direct `db.session` operations in routes
- WTForms for form validation on server-rendered pages
- Jinja2 templates with Bootstrap 5 (Flatly Bootswatch theme via Flask-Bootstrap)
- Selective JSON API endpoints embedded alongside HTML routes in blueprint files
- One domain per file in models; one domain per file in routes
- Shared helper functions in `app/utils.py` and `app/utils_order.py`

## Layers

**Presentation Layer (Templates + Static):**
- Purpose: Server-rendered HTML with Jinja2 templating and client-side interactivity
- Location: `my-jxc/app/templates/` (73 HTML files across 10 domain subdirectories), `my-jxc/app/static/`
- Contains: HTML templates, base layout (`base.html`), per-domain sub-templates, `main.js` (jQuery), `charts.js`, `style.css`
- Depends on: Route context variables passed from blueprints, Bootstrap 5 CDN, jQuery CDN
- Used by: Browser clients

**Route Layer (Blueprints):**
- Purpose: Handle HTTP requests, orchestrate business logic, return HTML or JSON responses
- Location: `my-jxc/app/routes/` (10 blueprint files, 7,285 total lines)
- Contains: Route handlers with inline business logic, DB transactions, flash messages, JSON API endpoints
- Depends on: Models, Forms, Utils, db session, flask_login
- Used by: Flask router (registered in `create_app()` at `my-jxc/app/__init__.py:39-49`)

**Model Layer (SQLAlchemy ORM):**
- Purpose: Define database schema, relationships, and model-level methods
- Location: `my-jxc/app/models/` (9 model files, 18 tables, 549 total lines)
- Contains: SQLAlchemy model classes with `__tablename__`, relationships, `__repr__`, model properties
- Depends on: `app.db` (SQLAlchemy instance)
- Used by: Route handlers directly (no repository pattern)

**Utility Layer:**
- Purpose: Reusable helper functions and business constants shared across blueprints
- Location: `my-jxc/app/utils.py` (291 lines), `my-jxc/app/utils_order.py` (141 lines), `my-jxc/app/constants.py` (80 lines)
- Contains: Decimal conversion, atomic balance operations, order number generation, stock log creation, Excel export helpers, business constants
- Depends on: `app.db`, SQLAlchemy
- Used by: Route handlers

**Form Layer (WTForms):**
- Purpose: Server-side form validation and rendering
- Location: `my-jxc/app/forms.py`
- Contains: WTForms form classes for all CRUD operations
- Depends on: WTForms, app models (for custom validators)
- Used by: Route handlers for form validation

## Data Flow

### Primary Purchase Flow

1. User creates PurchaseOrder via `purchase.new_order()` (`my-jxc/app/routes/purchase.py:95`)
2. System generates order number via `generate_order_number('PO', PurchaseOrder)` (`my-jxc/app/utils.py:77`)
3. PurchaseOrderItem rows created for each line item
4. User creates StockIn from order via `purchase.stock_in_from_order()` (`my-jxc/app/routes/purchase.py`)
5. For each StockInItem, `update_stock_and_log()` or `create_stock_log()` updates `Product.stock_quantity` and creates a `StockLog` entry (`my-jxc/app/utils.py:149`, `my-jxc/app/utils_order.py:54`)
6. `PurchaseOrderItem.received_quantity` updated; order status changes to `partial` or `completed`
7. Payment recorded via `finance.new_payment()`, which calls `sub_balance(supplier, 'payable_balance', amount)` (`my-jxc/app/utils.py:55`)

### Primary Sales Flow

1. User creates SalesOrder via `sales.new_order()` (`my-jxc/app/routes/sales.py`)
2. System generates order number via `generate_order_number('SO', SalesOrder)` (`my-jxc/app/utils.py:77`)
3. SalesOrderItem rows created for each line item
4. User creates StockOut from order via `sales.stock_out_from_order()`
5. For each StockOutItem, stock decremented and StockLog created with `change_type='out'`
6. `SalesOrderItem.delivered_quantity` updated; order status changes to `partial` or `completed`
7. Receipt recorded via `finance.new_receipt()`, which calls `add_balance(customer, 'receivable_balance', amount)` (`my-jxc/app/utils.py:31`)

### Quick Stock-In/Out Flow

1. User submits quick form via `purchase.quick_stock_in()` or `sales.quick_stock_out()`
2. System creates StockIn/StockOut directly (no preceding PurchaseOrder/SalesOrder)
3. Stock updated immediately via `update_stock_and_log()` (`my-jxc/app/utils.py:149`)
4. No order status tracking -- single-step operation

### Finance (Receipt/Payment) Flow

1. Receipt: `finance.new_receipt()` creates Receipt record, calls `add_balance(customer, 'receivable_balance', amount)` to atomically reduce AR (`my-jxc/app/routes/finance.py`)
2. Payment: `finance.new_payment()` creates Payment record, calls `sub_balance(supplier, 'payable_balance', amount)` to atomically reduce AP
3. Expense: `finance.new_expense()` creates Expense record (no balance impact)
4. Balance operations use SQL-level `UPDATE ... SET field = field + delta` to prevent lost updates (`my-jxc/app/utils.py:31-74`)

### Dashboard Data Flow

1. `main.index()` queries KPIs: today's orders, pending stock-in/out, low-stock products, recent records (`my-jxc/app/routes/main.py:127`)
2. Chart data loaded via AJAX to API endpoints: `/api/sales-trend`, `/api/stock-overview`, `/api/finance-summary` (`my-jxc/app/routes/main.py:17-124`)
3. Charts rendered client-side via `my-jxc/app/static/js/charts.js`

**State Management:**
- No client-side state management (traditional server-rendered pages with full page reloads)
- Session state via Flask-Login (`flask_login`) -- stores `user_id` in signed cookie
- CSRF protection via Flask-WTF (`CSRFProtect`) with header-based token support
- Flash messages for user feedback (`flash()` with Bootstrap alert categories: `success`, `danger`, `warning`, `info`)

## Key Abstractions

**StockLog (Inventory Audit Trail):**
- Purpose: Immutable audit trail of all inventory changes
- Examples: `my-jxc/app/models/inventory.py`
- Pattern: Every stock mutation creates a StockLog with `before_quantity`, `after_quantity`, `change_type`, `reference_id`, `reference_type`. Valid types defined in `my-jxc/app/constants.py:27-37` (ChangeType class). The `reference_number` property at line 26 uses inline imports to resolve the related document number.

**Atomic Balance Operations:**
- Purpose: Prevent lost-update concurrency issues on financial balances
- Examples: `my-jxc/app/utils.py:31` (`add_balance`), `my-jxc/app/utils.py:55` (`sub_balance`)
- Pattern: Uses `UPDATE ... SET field = field + delta` SQL expressions via `sqlalchemy.update()` rather than read-then-write. Calls `db.session.refresh()` after to sync ORM state.

**Order Number Generation:**
- Purpose: Generate sequential, date-based document numbers
- Examples: `my-jxc/app/utils.py:77` (`generate_order_number`)
- Pattern: `{PREFIX}{YYYYMMDD}{NNNN}` (e.g., `PO202606030001`). Queries the last order matching today's pattern, extracts the sequence number, increments by 1.

**SystemSetting (Runtime Config):**
- Purpose: Runtime-configurable system settings stored in DB
- Examples: `my-jxc/app/models/system.py`
- Pattern: `SystemSetting.get_value('KEY')` / `SystemSetting.set_value('KEY', 'value')` class methods. Column named `key` but accessed via `setting_key` attribute.

**Comma-Separated Reference IDs:**
- Purpose: Link financial records (Receipt/Payment) to multiple orders
- Examples: `my-jxc/app/models/finance.py:15` (Receipt.reference_id), `my-jxc/app/models/finance.py:37` (Payment.reference_id)
- Pattern: Stores IDs as comma-separated strings (e.g., "1,2,3"). Queried via `match_reference_id_filter()` in `my-jxc/app/utils_order.py:13` which builds OR conditions for 4 positional patterns.

## Entry Points

**Application Entry (`run.py`):**
- Location: `my-jxc/run.py`
- Triggers: `python run.py` (dev mode with Flask server) or `MODE=prod python run.py` (production with waitress)
- Responsibilities: `create_app()` at module level (line 12), `init_database()` (lines 90-122) creates default admin/warehouse/category, mDNS registration (lines 28-58), `app.run(host='0.0.0.0', port=5000)` (line 146)
- Root route at line 60 redirects authenticated users to product index, unauthenticated to login

**App Factory (`app/__init__.py`):**
- Location: `my-jxc/app/__init__.py`
- Triggers: `create_app(config_name)` called from `run.py`
- Responsibilities: Initialize 5 extensions (SQLAlchemy, Migrate, Bootstrap, CSRF, LoginManager), register 10 blueprints (lines 39-49), set security headers (lines 71-77), register template context/filters (lines 52-69), register error handlers (lines 80-102)

**Shell Context:**
- Location: `my-jxc/run.py:77` (`make_shell_context`)
- Triggers: `flask shell`
- Provides: `db`, `User`, `Category`, `Product`, `Supplier`, `Customer`, `Warehouse`

**Database Scripts:**
- Location: `my-jxc/scripts/reset_db.py` -- Drop all tables, recreate, seed test data
- Location: `my-jxc/scripts/migrate_db.py` -- Manual SQLite ALTER TABLE migrations

## Architectural Constraints

- **Threading:** Single-process WSGI. Dev mode uses Flask dev server; production mode uses waitress (`my-jxc/run.py:140-141`). Uses `with_for_update()` for row-level locking on critical stock operations, but SQLite has limited concurrent write support (single writer).
- **Global state:** `db`, `migrate`, `bootstrap`, `csrf`, `login_manager` are module-level singletons in `my-jxc/app/__init__.py` (lines 13-17). Initialized per-app via `init_app()`. The `app/services/` directory exists but is empty (no service layer).
- **Circular imports:** Avoided through late imports in model properties (e.g., `StockLog.reference_number` at `my-jxc/app/models/inventory.py:26-55` uses inline `from app.models import ...`) and blueprint-level imports in `my-jxc/app/routes/__init__.py`.
- **Database:** SQLite only. Connection string in `my-jxc/config.py:25`. No connection pooling configured (SQLite default). Database file at `my-jxc/instance/store.db`.
- **No service layer:** All business logic is inline in route handlers. No repository or service abstractions exist. The `app/services/` directory is empty.
- **No task queue:** All operations are synchronous. Long-running exports (Excel) happen in-request.

## Anti-Patterns

### Fat Route Handlers

**What happens:** Business logic (stock updates, balance calculations, order status transitions, validation) lives directly in route handler functions. Files like `purchase.py` (1,216 lines), `sales.py` (1,243 lines), `finance.py` (1,226 lines) contain complete business workflows.

**Why it's wrong:** Makes business logic untestable in isolation, creates code duplication across similar operations (e.g., stock-in vs quick stock-in), and makes route files difficult to navigate.

**Do this instead:** Extract business logic into service functions in `app/services/`. For example, a `PurchaseService.create_stock_in()` method could encapsulate the stock update, log creation, and order status update logic that is currently duplicated in route handlers.

### Comma-Separated Reference IDs

**What happens:** `Receipt.reference_id` and `Payment.reference_id` store multiple order IDs as comma-separated strings (e.g., "1,2,3") instead of using a junction table.

**Why it's wrong:** Cannot use foreign key constraints, requires complex LIKE queries with 4 positional patterns (`my-jxc/app/utils_order.py:13-33`), makes joins impossible, and risks data integrity issues.

**Do this instead:** Create junction tables `receipt_orders` and `payment_orders` with `(receipt_id, order_id)` foreign keys. This enables proper joins, constraints, and simpler queries.

### Inline SQL Queries in Routes

**What happens:** Complex SQLAlchemy queries with joins, aggregations, and filtering are written directly in route handlers. The dashboard alone (`my-jxc/app/routes/main.py`) runs 12+ separate queries.

**Why it's wrong:** Duplicates query logic across routes, makes optimization difficult, and creates N+1 query risks.

**Do this instead:** Use SQLAlchemy model methods or repository functions for common queries. For example, `Product.low_stock_count()` class method instead of inline filter at `my-jxc/app/routes/main.py:164`.

## Error Handling

**Strategy:** Try/except with rollback and flash messages for all database operations.

**Patterns:**
- Every `db.session.commit()` is wrapped in try/except `SQLAlchemyError` (and sometimes `IntegrityError`)
- On error: `db.session.rollback()` + `flash('...', 'danger')` + redirect
- Helper: `safe_commit()` in `my-jxc/app/utils.py:199` returns `(success, error_message)` tuple
- Foreign key constraints checked manually before delete operations (e.g., `purchase.delete_order()` checks for related StockIns, Payments, StockLogs, Returns)
- `abort(404)` for missing records after `db.session.get()`
- `abort(403)` for admin-only routes via `_require_admin()` helper in system blueprint
- Custom error pages registered in `my-jxc/app/__init__.py:80-102` (403, 404, 500)

## Cross-Cutting Concerns

**Logging:**
- Audit logs for user actions (login, logout, password change, email change) via `Log` model (`my-jxc/app/models/user.py:38`)
- Includes: `user_id`, `action` (Chinese description), `details`, `ip_address`
- No application-level logging framework (no `logging` module usage)

**Validation:**
- WTForms validators: `DataRequired`, `Length`, `NumberRange`, `Email`, `Optional`, `EqualTo` (`my-jxc/app/forms.py`)
- Manual validation for complex business rules in route handlers
- File upload validation: check content type, magic bytes, and file size in `my-jxc/app/routes/product.py`

**Authentication:**
- Flask-Login with session-based auth (`my-jxc/app/__init__.py:18-19`)
- All routes require `@login_required` except login/register
- Admin-only routes call `_require_admin()` which does `abort(403)` if not admin
- Logout is POST-only: `@bp.route('/logout', methods=['POST'])`
- User loader registered in `my-jxc/app/models/user.py:33-35`

**Security Headers:**
- Set globally via `@app.after_request` in `my-jxc/app/__init__.py:71-77`
- X-Content-Type-Options: nosniff, X-Frame-Options: DENY, X-XSS-Protection, Referrer-Policy

**CSRF Protection:**
- Enabled globally via `CSRFProtect` (`my-jxc/app/__init__.py:35`)
- Disabled in test config: `app.config['WTF_CSRF_ENABLED'] = False` (`my-jxc/config.py:71`)
- API endpoints support header-based tokens: `X-CSRFToken`, `X-CSRF-Token` (`my-jxc/config.py:32`)

**Financial Precision:**
- `Decimal` type for all monetary calculations, never `float`
- `to_decimal()` from `my-jxc/app/utils.py:12` for safe conversions
- Atomic SQL expressions for balance updates via `add_balance()` / `sub_balance()` in `my-jxc/app/utils.py:31-74`

---

*Architecture analysis: 2026-06-08*
