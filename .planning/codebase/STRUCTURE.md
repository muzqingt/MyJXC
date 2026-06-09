# Codebase Structure

**Analysis Date:** 2026-06-08

## Directory Layout

```
my-jxc/
├── app/                        # Main application package
│   ├── __init__.py             # App factory: create_app(), extension init, blueprint registration
│   ├── constants.py            # Business constants: OrderStatus, ChangeType, PaymentMethod, UserRole
│   ├── forms.py                # WTForms form classes for all CRUD operations
│   ├── utils.py                # Shared helpers: Decimal, balance ops, order#, Excel styles
│   ├── utils_order.py          # Order-specific helpers: stock log, reference ID matching
│   ├── models/                 # SQLAlchemy ORM models (18 tables across 9 files)
│   │   ├── __init__.py         # Barrel export of all models
│   │   ├── user.py             # User, Log
│   │   ├── product.py          # Product, Category
│   │   ├── partner.py          # Supplier, Customer, Warehouse
│   │   ├── purchase.py         # PurchaseOrder, PurchaseOrderItem, StockIn, StockInItem
│   │   ├── sales.py            # SalesOrder, SalesOrderItem, StockOut, StockOutItem
│   │   ├── inventory.py        # StockLog
│   │   ├── finance.py          # Receipt, Payment, Expense
│   │   ├── returns.py          # PurchaseReturn, PurchaseReturnItem, SalesReturn, SalesReturnItem
│   │   └── system.py           # SystemSetting
│   ├── routes/                 # Flask blueprints (10 blueprints, 7,285 lines total)
│   │   ├── __init__.py         # Barrel import of all blueprint modules
│   │   ├── auth.py             # Login, register, logout, profile (197 lines)
│   │   ├── main.py             # Dashboard + chart data APIs (239 lines)
│   │   ├── product.py          # Product/category CRUD, import/export (569 lines)
│   │   ├── partner.py          # Supplier/customer/warehouse CRUD, import (677 lines)
│   │   ├── purchase.py         # Purchase orders, stock-in, returns (1,216 lines)
│   │   ├── sales.py            # Sales orders, stock-out, returns (1,243 lines)
│   │   ├── inventory.py        # Stock overview, adjust, transfer, logs (695 lines)
│   │   ├── finance.py          # Receipts, payments, expenses, AR/AP (1,226 lines)
│   │   ├── report.py           # Inventory/sales/customer/supplier reports (706 lines)
│   │   └── system.py           # User mgmt, backup, settings, logs (507 lines)
│   ├── services/               # Empty directory (no service layer implemented)
│   ├── templates/              # Jinja2 templates (73 HTML files)
│   │   ├── base.html           # Base layout with navbar, Bootstrap 5 CDN, CSRF meta
│   │   ├── error.html          # Custom error page (403, 404, 500)
│   │   ├── auth/               # login.html, register.html, profile.html
│   │   ├── components/         # charts.html (shared chart component)
│   │   ├── main/               # dashboard.html
│   │   ├── product/            # index, edit, view, categories, category_edit, import, import_result, suppliers, supplier_edit, customers, customer_edit, warehouses, warehouse_edit
│   │   ├── partner/            # supplier_import, customer_import, import_result
│   │   ├── purchase/           # index, order_items, order_view, order_stock_in, stock_in_edit, stock_in_items, stock_in_view, returns, return_view
│   │   ├── sales/              # index, orders, order_edit, order_items, order_view, stock_outs, stock_out_edit, stock_out_items, stock_out_view, returns, return_view
│   │   ├── inventory/          # index, products, warehouse_stock, stock_check, stock_adjust, stock_transfer, logs
│   │   ├── finance/            # index, receipts, receipt_edit, receipt_view, payments, payment_edit, payment_view, expenses, expense_edit, ar_ap_search, profit_analysis
│   │   ├── report/             # index, inventory_report, sales_ranking, customer_statistics, supplier_statistics, daily_report
│   │   └── system/             # index, users, user_edit, settings, backup, logs
│   └── static/                 # Static assets
│       ├── css/style.css       # Custom styles (2,786 bytes)
│       ├── js/main.js          # jQuery client-side logic (15,588 bytes)
│       ├── js/charts.js        # Chart.js dashboard charts (10,641 bytes)
│       └── uploads/            # User-uploaded files (product images)
├── instance/                   # Runtime data (not committed)
│   ├── store.db                # SQLite database file
│   └── .flask_secret_key       # Auto-generated Flask secret key
├── backups/                    # Database backup files
├── docs/                       # Documentation
│   ├── API.md                  # API documentation
│   ├── BUG_STATUS.md           # Bug tracking
│   └── CHANGELOG.md            # Change log
├── scripts/                    # Utility scripts
│   ├── reset_db.py             # Drop all tables, recreate, seed test data
│   ├── migrate_db.py           # Manual SQLite ALTER TABLE migrations
│   ├── jxc.spec                # PyInstaller spec for desktop packaging
│   ├── build_linux.sh          # Linux build script
│   └── build_windows.bat       # Windows build script
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Root conftest (test fixtures)
│   ├── factories.py            # Test data factories
│   ├── helpers.py              # Test helper functions
│   ├── e2e/                    # End-to-end tests (13 test files)
│   │   ├── conftest.py         # E2E-specific fixtures
│   │   ├── factories.py        # E2E test factories
│   │   └── test_*.py           # E2E test modules
│   └── test_*.py               # Unit/integration tests (40+ test files)
├── config.py                   # Config classes: Development, Production, Test
├── run.py                      # Application entry point
├── conftest.py                 # Root pytest conftest
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies
└── .planning/                  # Planning artifacts
    └── codebase/               # Codebase analysis documents
```

## Directory Purposes

**`app/`:**
- Purpose: Main Flask application package containing all application code
- Contains: App factory, models, routes, forms, utilities, templates, static assets
- Key files: `__init__.py` (app factory), `utils.py` (shared helpers), `constants.py` (business constants), `forms.py` (WTForms)

**`app/models/`:**
- Purpose: SQLAlchemy ORM model definitions, one domain per file
- Contains: 18 database table definitions across 9 model files
- Key files: `__init__.py` (barrel export importing all models from submodules)
- Convention: Import from `app.models` (e.g., `from app.models import Product`), never from individual model files

**`app/routes/`:**
- Purpose: Flask blueprint modules, each handling a business domain
- Contains: 10 blueprint files with route handlers, inline business logic, JSON API endpoints
- Key files: `__init__.py` (barrel import of all blueprint modules)
- Convention: Each file exports `bp = Blueprint('name', __name__, url_prefix='/prefix')`

**`app/templates/`:**
- Purpose: Jinja2 HTML templates for server-rendered pages
- Contains: 73 HTML files organized by domain subdirectory
- Key files: `base.html` (shared layout with navbar, Bootstrap 5, CSRF meta tag)
- Convention: Templates organized by domain (e.g., `purchase/index.html`, `sales/orders.html`)

**`app/static/`:**
- Purpose: Static assets served directly by Flask
- Contains: CSS, JavaScript, uploaded files
- Key files: `css/style.css`, `js/main.js` (jQuery), `js/charts.js` (Chart.js)

**`app/services/`:**
- Purpose: Intended for service layer (currently empty)
- Contains: Only `__pycache__/` directory
- Note: No service layer implemented -- all business logic is in route handlers

**`tests/`:**
- Purpose: Test suite (unit, integration, E2E)
- Contains: 40+ test files at root level, 13 E2E test files in `e2e/` subdirectory
- Key files: `conftest.py` (fixtures), `factories.py` (test data factories), `helpers.py` (test utilities)

**`scripts/`:**
- Purpose: Database management and build scripts
- Contains: DB reset/migrate scripts, PyInstaller build configs
- Key files: `reset_db.py` (full DB reset), `migrate_db.py` (manual migrations), `jxc.spec` (PyInstaller)

**`instance/`:**
- Purpose: Runtime data directory (database, secrets)
- Contains: SQLite database file, auto-generated Flask secret key
- Generated: Yes (created at runtime)
- Committed: No (in `.gitignore`)

**`backups/`:**
- Purpose: Database backup files created via system backup feature
- Contains: SQLite database backup files
- Generated: Yes (created by backup feature in `system.py`)
- Committed: No

## Key File Locations

**Entry Points:**
- `my-jxc/run.py`: Application entry point -- creates app, initializes DB, starts server
- `my-jxc/app/__init__.py`: App factory `create_app()` -- initializes extensions, registers blueprints

**Configuration:**
- `my-jxc/config.py`: Config classes (Development, Production, Test) with DB URI, security settings
- `my-jxc/pytest.ini`: Pytest configuration

**Core Logic:**
- `my-jxc/app/utils.py`: Shared helpers -- `to_decimal()`, `add_balance()`, `sub_balance()`, `generate_order_number()`, `update_stock_and_log()`, `safe_commit()`, Excel styling
- `my-jxc/app/utils_order.py`: Order helpers -- `create_stock_log()`, `match_reference_id_filter()`, `parse_reference_ids()`, `rebuild_items_on_error()`
- `my-jxc/app/constants.py`: Business constants -- `OrderStatus`, `ChangeType`, `PaymentMethod`, `UserRole`, `VALID_CHANGE_TYPES`
- `my-jxc/app/forms.py`: WTForms form classes for all CRUD operations

**Models:**
- `my-jxc/app/models/user.py`: `User` (with `UserMixin`), `Log`
- `my-jxc/app/models/product.py`: `Product`, `Category` (self-referential parent)
- `my-jxc/app/models/partner.py`: `Supplier` (with `payable_balance`), `Customer` (with `receivable_balance`), `Warehouse`
- `my-jxc/app/models/purchase.py`: `PurchaseOrder`, `PurchaseOrderItem`, `StockIn`, `StockInItem`
- `my-jxc/app/models/sales.py`: `SalesOrder`, `SalesOrderItem`, `StockOut`, `StockOutItem`
- `my-jxc/app/models/inventory.py`: `StockLog` (immutable audit trail)
- `my-jxc/app/models/finance.py`: `Receipt`, `Payment`, `Expense`
- `my-jxc/app/models/returns.py`: `PurchaseReturn`, `PurchaseReturnItem`, `SalesReturn`, `SalesReturnItem`
- `my-jxc/app/models/system.py`: `SystemSetting` (key-value config store)

**Routes (by size, largest first):**
- `my-jxc/app/routes/sales.py`: 1,243 lines -- Sales orders, stock-out, returns, quick stock-out
- `my-jxc/app/routes/finance.py`: 1,226 lines -- Receipts, payments, expenses, AR/AP, profit analysis
- `my-jxc/app/routes/purchase.py`: 1,216 lines -- Purchase orders, stock-in, returns, quick stock-in
- `my-jxc/app/routes/report.py`: 706 lines -- Inventory/sales/customer/supplier reports, daily report
- `my-jxc/app/routes/inventory.py`: 695 lines -- Stock overview, adjust, transfer, logs, Excel export
- `my-jxc/app/routes/partner.py`: 677 lines -- Supplier/customer/warehouse CRUD, Excel import
- `my-jxc/app/routes/product.py`: 569 lines -- Product/category CRUD, image upload, Excel import/export
- `my-jxc/app/routes/system.py`: 507 lines -- User management, backup/restore, settings, logs
- `my-jxc/app/routes/main.py`: 239 lines -- Dashboard KPIs, chart data APIs
- `my-jxc/app/routes/auth.py`: 197 lines -- Login, register, logout, profile

**Testing:**
- `my-jxc/conftest.py`: Root pytest conftest
- `my-jxc/tests/conftest.py`: Test fixtures (app, client, auth helpers)
- `my-jxc/tests/factories.py`: Test data factory functions
- `my-jxc/tests/helpers.py`: Test helper utilities
- `my-jxc/tests/e2e/conftest.py`: E2E-specific fixtures
- `my-jxc/tests/e2e/factories.py`: E2E test data factories

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` -- `purchase.py`, `stock_in_items.html`, `utils_order.py`
- Templates: `snake_case.html` -- `order_view.html`, `stock_in_edit.html`, `ar_ap_search.html`
- Scripts: `snake_case.py` -- `reset_db.py`, `migrate_db.py`

**Directories:**
- Python packages: `snake_case` -- `app/models/`, `app/routes/`, `app/services/`
- Template domains: `snake_case` -- `app/templates/purchase/`, `app/templates/finance/`

**Models:**
- PascalCase class names: `PurchaseOrder`, `StockInItem`, `SystemSetting`, `StockLog`
- Explicit `__tablename__` on every model: `__tablename__ = 'purchase_orders'`
- Table names: plural snake_case -- `purchase_orders`, `stock_in_items`, `stock_logs`

**Functions:**
- snake_case: `to_decimal()`, `add_balance()`, `generate_order_number()`
- Private helpers prefixed with underscore: `_save_product_image()`, `_require_admin()`, `_safe_filename()`
- Blueprint route functions: `new_order()`, `edit_order()`, `quick_stock_in()`, `view_order()`
- API endpoints prefixed with `api_`: `api_products()`, `api_order_items()`, `api_stock_check()`, `api_sales_trend()`

**Variables:**
- snake_case: `order_number`, `stock_quantity`, `total_amount`
- Query parameters from `request.args`: `page`, `keyword`, `start_date`, `end_date`
- Constants: UPPER_SNAKE_CASE: `VALID_CHANGE_TYPES`, `EXCEL_HEADER_FONT`, `EXCEL_THIN_BORDER`

## Where to Add New Code

**New Business Domain (e.g., Inventory Transfer as separate module):**
- Model: Create `my-jxc/app/models/transfer.py`, add imports to `my-jxc/app/models/__init__.py`
- Routes: Create `my-jxc/app/routes/transfer.py` with `bp = Blueprint('transfer', __name__, url_prefix='/transfer')`, register in `my-jxc/app/__init__.py`
- Templates: Create `my-jxc/app/templates/transfer/` directory with HTML files
- Forms: Add form classes to `my-jxc/app/forms.py` (single file for all forms)

**New API Endpoint:**
- Add to existing blueprint file in `my-jxc/app/routes/` (e.g., `@bp.route('/api/new-endpoint')`)
- Follow naming convention: prefix with `api_` (e.g., `def api_new_endpoint():`)
- Return `jsonify()` with Decimal values serialized as strings: `'amount': str(item.amount)`

**New Utility Function:**
- Shared across domains: Add to `my-jxc/app/utils.py`
- Order/purchase/sales specific: Add to `my-jxc/app/utils_order.py`
- New business constant: Add to `my-jxc/app/constants.py`

**New Form:**
- Add WTForms class to `my-jxc/app/forms.py` (single file for all forms)
- Import in route file: `from app.forms import NewForm`

**New Test:**
- Unit/integration test: Create `my-jxc/tests/test_new_feature.py`
- E2E test: Create `my-jxc/tests/e2e/test_new_feature.py`
- Use factories from `my-jxc/tests/factories.py` or `my-jxc/tests/e2e/factories.py`

**New Static Asset:**
- CSS: Add to `my-jxc/app/static/css/style.css` (single file)
- JavaScript: Add to `my-jxc/app/static/js/main.js` (single file) or create new file
- Uploaded files: `my-jxc/app/static/uploads/`

## Special Directories

**`instance/`:**
- Purpose: Runtime data (SQLite database, Flask secret key)
- Generated: Yes (created at runtime by `run.py` and `config.py`)
- Committed: No (in `.gitignore`)

**`backups/`:**
- Purpose: Database backup files created via system backup feature
- Generated: Yes (created by backup feature in `my-jxc/app/routes/system.py`)
- Committed: No

**`app/services/`:**
- Purpose: Intended for service layer extraction (currently empty)
- Generated: No (directory exists but contains no Python files)
- Committed: Yes (empty directory)

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (by Python interpreter)
- Committed: No (in `.gitignore`)

**`.planning/`:**
- Purpose: Planning artifacts, codebase analysis, phase documentation
- Generated: Partially (codebase docs are generated, phase docs are hand-written)
- Committed: Yes (planning artifacts tracked in git)

**`venv/`:**
- Purpose: Python virtual environment
- Generated: Yes (by `python -m venv venv`)
- Committed: No (in `.gitignore`)

---

*Structure analysis: 2026-06-08*
