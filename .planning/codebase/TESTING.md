# Testing Patterns

**Analysis Date:** 2026-06-08

## Test Framework

**Runner:**
- pytest 9.0.3
- Config: `pytest.ini` at project root (`/home/code/claude/my-jxc/pytest.ini`)

**Assertion Library:**
- Plain `assert` statements (no pytest-assume or other plugins)

**Configuration (`pytest.ini`):**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
python_classes = Test*
addopts = -v --tb=short
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

**Run Commands:**
```bash
# Run all tests (use venv pytest)
/home/code/claude/my-jxc/venv/bin/python -m pytest tests/

# Run specific test file
/home/code/claude/my-jxc/venv/bin/python -m pytest tests/test_purchase.py

# Run specific test
/home/code/claude/my-jxc/venv/bin/python -m pytest tests/test_purchase.py::test_new_order_post

# Verbose with short traceback (default via addopts)
/home/code/claude/my-jxc/venv/bin/python -m pytest -v --tb=short

# Coverage
/home/code/claude/my-jxc/venv/bin/python -m pytest --cov=app --cov-report=html
```

**Installed testing packages (from venv):**
- pytest 9.0.3
- coverage 7.14.1
- selenium (for E2E tests in `tests/e2e/`)
- requests (for E2E factories)

## Test File Organization

**Location:**
- Unit and integration tests: `tests/` directory (co-located, not alongside source)
- E2E tests: `tests/e2e/` directory (separate conftest with Selenium fixtures)

**Naming:**
- `test_{domain}.py` for domain-specific tests: `test_purchase.py`, `test_sales.py`, `test_finance.py`
- `test_{domain}_deep.py` for additional domain coverage: `test_purchase_deep.py`, `test_sales_deep.py`
- `test_coverage_{domain}.py` for coverage gap filling: `test_coverage_purchase.py`, `test_coverage_finance.py`
- `test_integration*.py` for cross-module business flows: `test_integration.py`, `test_integration_business.py`
- `test_unit_complete.py` for comprehensive unit coverage (104 test functions)
- `test_smoke.py` for infrastructure sanity checks

**Structure:**
```
tests/
├── __init__.py
├── conftest.py              # Core fixtures: app, client, db_session, authenticated_client
├── factories.py             # Factory functions for test data creation
├── helpers.py               # HTTP helper functions: get_page, post_page, get_json
├── test_smoke.py            # Infrastructure smoke tests
├── test_models.py           # Model unit tests
├── test_utils.py            # Utility function unit tests
├── test_utils_order.py      # Order utility function tests
├── test_auth.py             # Auth route tests
├── test_product.py          # Product route tests
├── test_partner.py          # Partner route tests
├── test_purchase.py         # Purchase route tests (491 lines, 24 tests)
├── test_sales.py            # Sales route tests (440 lines, 22 tests)
├── test_inventory.py        # Inventory route tests
├── test_finance.py          # Finance route tests
├── test_report.py           # Report route tests
├── test_system.py           # System route tests
├── test_integration.py      # Cross-module integration tests
├── test_integration_business.py
├── test_integration_complete.py
├── test_integration_edge_cases.py
├── test_integration_remaining.py
├── test_unit_complete.py    # Comprehensive unit tests (1462 lines, 104 tests)
├── test_bug_coverage.py     # Regression tests for specific bugs
├── test_import_export.py    # Import/export feature tests
├── test_coverage_*.py       # Coverage gap filling tests (8 files)
└── e2e/
    ├── conftest.py          # Selenium + Flask server fixtures
    ├── factories.py         # HTTP-based factory class (E2EFactories)
    ├── test_login.py
    ├── test_dashboard.py
    ├── test_product_full.py
    ├── test_partner_full.py
    ├── test_purchase.py
    ├── test_sales.py
    ├── test_inventory.py
    ├── test_finance.py
    ├── test_report_full.py
    ├── test_system_full.py
    ├── test_search.py
    ├── test_pagination.py
    └── test_form_validation.py
```

**Total collected tests:** 1144 (as of 2026-06-08)

## Fixtures

**Core fixtures (`tests/conftest.py`):**

```python
@pytest.fixture(scope='session')
def app():
    """Session-scoped Flask app with in-memory SQLite, CSRF disabled"""
    # Creates temp DB, initializes app, seeds default admin/warehouse/category
    # Tears down temp files after session

@pytest.fixture(scope='function')
def client(app):
    """Per-test Flask test client"""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    """Per-test DB session with cleanup"""
    # Yields db.session
    # After test: rollback, delete all rows from all tables, re-seed defaults

@pytest.fixture(scope='function')
def authenticated_client(app, client, db_session):
    """Logged-in admin test client"""
    # POSTs to /auth/login with admin credentials
    return client
```

**Sample data fixtures (`tests/conftest.py`):**

```python
@pytest.fixture
def sample_user(app, db_session):
    return create_user(username='testuser', password='test123', role='user')

@pytest.fixture
def sample_category(app, db_session):
    return create_category(name='电子产品')

@pytest.fixture
def sample_product(app, db_session, sample_category):
    return create_product(code='TEST001', name='测试商品A', ...)

@pytest.fixture
def sample_supplier(app, db_session):
    return create_supplier(code='SUP001', name='测试供应商A', ...)

@pytest.fixture
def sample_customer(app, db_session):
    return create_customer(code='CUS001', name='测试客户A', ...)

@pytest.fixture
def sample_warehouse(app, db_session):
    return create_warehouse(code='WH001', name='测试仓库A', ...)
```

**Key fixture characteristics:**
- `app` is session-scoped (shared across all tests for performance)
- `client` and `db_session` are function-scoped (isolated per test)
- `db_session` teardown deletes ALL rows from ALL tables, then re-seeds 3 default records (admin user, default warehouse, default category)
- No savepoint/nested transaction pattern — uses full table truncation between tests

## Factory Functions (`tests/factories.py`)

**Pattern:** Simple factory functions (not factory_boy or similar libraries). Each function creates a model instance, adds to session, flushes to get ID, and returns.

```python
def create_user(username=None, password='test123', role='user', email=None):
    """创建用户"""
    from app.models import User
    suffix = _unique_suffix()
    user = User(
        username=username or f'user_{suffix}',
        email=email or f'user_{suffix}@test.com',
        role=role,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # Get auto-generated ID
    return user
```

**Available factories:**
- `create_user(username, password, role, email)`
- `create_category(name, parent_id, description)`
- `create_product(code, name, category_id, unit, sale_price, cost_price, stock_quantity)`
- `create_supplier(code, name, contact_person, phone)`
- `create_customer(code, name, contact_person, phone)`
- `create_warehouse(code, name, address)`
- `create_purchase_order(supplier_id, warehouse_id, created_by, items, status)`
- `create_sales_order(customer_id, warehouse_id, created_by, items, status)`

**Unique ID generation:**
```python
_ts_counter = 0

def _unique_suffix():
    global _ts_counter
    _ts_counter += 1
    return f"{int(time.time())}{_ts_counter}"
```
- Uses timestamp + counter to avoid unique constraint violations
- Each factory call auto-generates codes/names if not provided (e.g., `SKU_{suffix}`)

**Order factory pattern:**
```python
def create_purchase_order(supplier_id, warehouse_id, created_by=None,
                          items=None, status='confirmed'):
    # items: list of dict with product_id, quantity, unit_price
    order = PurchaseOrder(order_number=generate_order_number('PO', PurchaseOrder), ...)
    db.session.add(order)
    db.session.flush()
    # Create items, calculate total
    db.session.flush()
    return order
```

## Test Helpers (`tests/helpers.py`)

```python
def get_page(client, url, expected=200, follow=True):
    """GET request with status assertion"""
    resp = client.get(url, follow_redirects=follow)
    assert resp.status_code == expected
    return resp

def post_page(client, url, data, expected=200, follow=True):
    """POST request with status assertion"""
    resp = client.post(url, data=data, follow_redirects=follow)
    assert resp.status_code == expected
    return resp

def get_json(client, url):
    """GET request returning JSON"""
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.get_json()

def assert_redirects_to_login(client, url):
    """Assert unauthenticated access redirects to login"""
    resp = client.get(url, follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers.get('Location', '')
```

## Test Structure Patterns

**Typical route test:**
```python
def test_new_order_post(app, authenticated_client, db_session):
    """POST 创建采购订单，验证订单号生成"""
    # 1. Create prerequisite data via factories
    supplier = create_supplier(code='PO_SUP01', name='采购测试供应商')
    warehouse = create_warehouse(code='PO_WH01', name='采购测试仓库')
    product = create_product(code='PO_PROD01', name='采购测试商品')

    # 2. Make HTTP request
    resp = authenticated_client.post('/purchase/orders/new', data={
        'supplier_id': str(supplier.id),
        'warehouse_id': str(warehouse.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'action': 'save',
        'order_status': 'confirmed',
        'product_id[]': [str(product.id)],
        'quantity[]': ['10'],
        'unit_price[]': ['50.00'],
    }, follow_redirects=True)

    # 3. Assert HTTP response
    assert resp.status_code == 200

    # 4. Assert database state
    with app.app_context():
        order = PurchaseOrder.query.filter_by(supplier_id=supplier.id).first()
        assert order is not None
        assert order.order_number.startswith('PO')
        assert order.status == 'confirmed'
```

**Section dividers in test files:**
```python
# ==================== 采购订单 CRUD ====================
# ==================== 入库流程 ====================
# ==================== 退货流程 ====================
# ==================== 边界情况和 API ====================
```

## Mocking

**Framework:** None — no mocking libraries used

**Approach:**
- Tests use real Flask app with real SQLite database (in-memory for `app` fixture, temp file for `db_session`)
- No `unittest.mock`, `pytest-mock`, or `monkeypatch` usage detected
- CSRF disabled globally in test config: `app.config['WTF_CSRF_ENABLED'] = False`
- All tests are effectively integration tests against the real app stack

**What to Mock (if adding mocks):**
- External API calls (none currently exist)
- File system operations (backup/restore in system routes)
- Time-dependent operations (order number generation uses `datetime.now()`)

**What NOT to Mock:**
- Database operations (use real SQLite)
- Flask route handlers (test through HTTP client)
- Form validation (test through actual form submission)

## Coverage

**Requirements:** None formally enforced (no coverage threshold in config)

**View Coverage:**
```bash
/home/code/claude/my-jxc/venv/bin/python -m pytest --cov=app --cov-report=html
# Opens htmlcov/index.html
```

**Coverage tool:** coverage 7.14.1 installed in venv

**Current state:** ~1144 tests across ~50 test files. Coverage gap-filling tests exist (`test_coverage_*.py` files, 8 files total).

## Test Types

**Unit Tests (`tests/test_unit_complete.py`, `tests/test_utils.py`, `tests/test_models.py`):**
- Test individual utility functions: `to_decimal()`, `add_balance()`, `sub_balance()`, `generate_order_number()`
- Test model properties and methods
- Test constants and enums
- No HTTP requests, pure function testing with `app` and `db_session` fixtures

**Route/Integration Tests (`tests/test_purchase.py`, `tests/test_sales.py`, etc.):**
- Test HTTP endpoints via Flask test client
- Verify response status codes, database state changes, stock log creation
- Use `authenticated_client` fixture for authenticated routes
- Test CRUD operations, business flows, error cases

**Cross-Module Integration Tests (`tests/test_integration.py`, `tests/test_integration_business.py`, etc.):**
- Test complete business flows spanning multiple modules
- Example: Purchase order -> stock-in -> payment -> verify inventory + financials
- Example: Sales order -> stock-out -> receipt -> verify inventory + financials

**Smoke Tests (`tests/test_smoke.py`):**
- Verify test infrastructure works: app creation, login/logout, factory functions
- 6 tests, fast sanity check

**Bug Regression Tests (`tests/test_bug_coverage.py`):**
- Tests written for specific bugs found and fixed
- Prevents regressions

**E2E Tests (`tests/e2e/`):**
- Selenium-based browser tests
- Separate `conftest.py` with Flask server process + Chrome WebDriver fixtures
- Uses `E2EFactories` class (HTTP-based data creation via `requests`)
- Tests real browser interactions: form filling, button clicks, page navigation
- Requires Chromium/ChromeDriver installed

## E2E Test Fixtures (`tests/e2e/conftest.py`)

```python
@pytest.fixture(scope="session")
def app_server():
    """Start Flask app in a separate process on port 5000"""
    # Uses multiprocessing.Process
    # Waits for server readiness via requests.get polling
    yield 'http://localhost:5000'
    server.terminate()

@pytest.fixture(scope="session")
def chrome_options():
    """Headless Chrome options"""
    # --headless, --no-sandbox, --window-size=1920,1080

@pytest.fixture
def driver(app_server, chrome_options):
    """Selenium WebDriver per test"""
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()
```

**E2E Factory class (`tests/e2e/factories.py`):**
```python
class E2EFactories:
    """Creates test data via HTTP requests (not direct DB access)"""
    def __init__(self, base_url):
        self.session = requests.Session()

    def login(self, username='admin', password='admin123'): ...
    def create_product(self, code, name, **kwargs): ...
    def create_supplier(self, code, name, **kwargs): ...
    def create_customer(self, code, name, **kwargs): ...
    def create_warehouse(self, code, name, **kwargs): ...
```

## Common Patterns

**Async Testing:**
- Not applicable — Flask is synchronous, no async routes

**Error Testing:**
```python
def test_order_not_found_404(authenticated_client):
    """Access non-existent entity returns 404"""
    resp = authenticated_client.get('/purchase/orders/99999', follow_redirects=False)
    assert resp.status_code == 404

def test_unauthenticated_redirect(client):
    """Unauthenticated access redirects to login"""
    resp = client.get('/purchase/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers.get('Location', '')

def test_update_stock_invalid_type(app, db_session):
    """Invalid change type raises ValueError"""
    from app.utils import update_stock_and_log
    product = create_product(code='STK_INV01', name='无效类型测试', stock_quantity=50)
    warehouse = create_warehouse(code='STK_WH03', name='无效仓库')
    with pytest.raises(ValueError):
        update_stock_and_log(product, warehouse.id, 10, 'invalid_type', 1, 'test', '测试', 1)
```

**Form submission pattern (array-style fields):**
```python
resp = authenticated_client.post('/purchase/orders/new', data={
    'supplier_id': str(supplier.id),
    'warehouse_id': str(warehouse.id),
    'order_date': date.today().strftime('%Y-%m-%d'),
    'action': 'save',
    'order_status': 'confirmed',
    'product_id[]': [str(product1.id), str(product2.id)],
    'quantity[]': ['10', '5'],
    'unit_price[]': ['10.00', '20.00'],
}, follow_redirects=True)
```

**Database state verification pattern:**
```python
with app.app_context():
    p = db.session.get(Product, product.id)
    assert p.stock_quantity == Decimal('100')

    log = StockLog.query.filter_by(product_id=product.id, change_type='in').first()
    assert log is not None
    assert log.quantity == Decimal('20')
```

**Decimal assertions:**
- Always use `Decimal` for financial comparisons: `assert order.total_amount == Decimal('200.00')`
- Never compare with float

## Writing New Tests

**New route test:**
1. Create test file: `tests/test_{domain}.py`
2. Import fixtures and factories
3. Use `authenticated_client` for authenticated routes, `client` for unauthenticated
4. Use `db_session` whenever test modifies or reads database
5. Use factory functions to create prerequisite data
6. Use section dividers: `# ==================== {section} ====================`

**New unit test:**
1. Add to existing file or create `tests/test_{module}.py`
2. Import function directly from `app.utils` or `app.constants`
3. Use `app` and `db_session` fixtures if function touches database
4. Test edge cases: None, zero, negative, invalid input

**New integration test:**
1. Add to `tests/test_integration*.py` or create new file
2. Test complete business flow across multiple HTTP requests
3. Verify intermediate and final database state
4. Use descriptive test name: `test_purchase_to_payment_flow`

---

*Testing analysis: 2026-06-08*
