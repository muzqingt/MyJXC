# Coding Conventions

**Analysis Date:** 2026-06-08

## Naming Patterns

**Files:**
- `snake_case` for all Python files: `purchase.py`, `stock_in_items.html`, `utils_order.py`
- One model domain per file in `app/models/`: `user.py`, `product.py`, `purchase.py`, `sales.py`, `finance.py`, `returns.py`, `inventory.py`, `partner.py`, `system.py`
- One blueprint per file in `app/routes/`: `auth.py`, `product.py`, `purchase.py`, `sales.py`, `inventory.py`, `finance.py`, `report.py`, `system.py`, `main.py`, `partner.py`
- Templates organized by domain subdirectory: `app/templates/purchase/`, `app/templates/sales/`, etc.

**Classes:**
- `PascalCase` for all classes: `PurchaseOrder`, `StockInItem`, `SystemSetting`, `StockLog`
- SQLAlchemy models inherit from `db.Model`
- User model additionally inherits `UserMixin` for Flask-Login: `class User(UserMixin, db.Model)`
- Constants use plain classes with class attributes (not Enum): `class OrderStatus:`, `class ChangeType:`
- Every model defines `__tablename__` explicitly: `__tablename__ = 'purchase_orders'`
- Every model defines `__repr__`: `return f'<PurchaseOrder {self.order_number}>'`

**Functions:**
- `snake_case` for all functions: `to_decimal()`, `add_balance()`, `generate_order_number()`
- Private helpers prefixed with underscore: `_require_admin()`, `_safe_filename()`, `_unique_suffix()`
- Blueprint route handlers: `new_order()`, `edit_order()`, `quick_stock_in()`, `view_order()`
- API endpoints prefixed with `api_`: `api_products()`, `api_order_items()`, `api_stock_check()`
- Factory functions prefixed with `create_`: `create_user()`, `create_product()`, `create_purchase_order()`

**Variables:**
- `snake_case` for all variables: `order_number`, `stock_quantity`, `total_amount`
- Query parameters from `request.args`: `page`, `keyword`, `start_date`, `end_date`
- Timestamp convention: `ts = int(time.time())` (in tests)

**Constants:**
- `UPPER_SNAKE_CASE` for module-level constants: `VALID_CHANGE_TYPES`, `EXCEL_HEADER_FONT`, `EXCEL_THIN_BORDER`
- Business constants as class attributes: `OrderStatus.DRAFT`, `ChangeType.IN`, `PaymentMethod.CASH`
- Defined in `app/constants.py`

## Code Style

**Formatting:**
- No linter or formatter configuration detected (no `.flake8`, `pyproject.toml`, `ruff.toml`, or `setup.cfg`)
- 4-space indentation throughout
- Double quotes for strings predominant, single quotes also used (no enforced standard)
- Lines typically under 120 characters but no hard limit

**Linting:**
- No automated linting configured
- No pre-commit hooks detected

**Docstrings:**
- Chinese-language docstrings for all public functions and classes
- Use triple double-quotes: `"""中文描述"""`
- Short single-line docstrings for simple functions
- Multi-line docstrings with parameter/return descriptions for complex functions
- Example from `app/utils.py:update_stock_and_log`:
  ```python
  def update_stock_and_log(product, warehouse_id, quantity, change_type, ...):
      """
      更新商品库存数量并记录一条库存变动流水。

      before_quantity 取自 product.stock_quantity 当前值...
      Returns:
          (before_quantity, after_quantity) - 变动前后的库存数量
      """
  ```

## Import Organization

**Route files (top of file):**
1. Flask imports: `from flask import render_template, redirect, url_for, flash, request, Blueprint`
2. Flask extensions: `from flask_login import login_required, current_user`
3. App imports: `from app import db`
4. SQLAlchemy imports: `from sqlalchemy.orm import selectinload`, `from sqlalchemy.exc import SQLAlchemyError`
5. Model imports: `from app.models import PurchaseOrder, StockIn, ...`
6. Utility imports: `from app.utils import to_decimal, add_balance, ...`
7. Form imports: `from app.forms import StockInForm`
8. Standard library: `from datetime import datetime`

**Model files:**
- Use late/inline imports to avoid circular dependencies
- Example from `app/models/inventory.py:StockLog.reference_number`:
  ```python
  @property
  def reference_number(self) -> str:
      if self.reference_type == 'stock_in':
          from app.models import StockIn  # inline to avoid circular import
          stock_in = StockIn.query.get(self.reference_id)
  ```

**Test files:**
1. Standard library: `import pytest`, `from datetime import date`, `from decimal import Decimal`
2. App imports: `from app import db`, `from app.models import ...`
3. Factory imports: `from tests.factories import create_supplier, create_product, ...`
4. Helper imports: `from tests.helpers import get_page, post_page`

**Barrel imports:**
- `app/models/__init__.py` exports all models: always import from `app.models`, not individual model files
- `app/routes/__init__.py` exports all blueprint references (though `create_app()` imports directly from route modules)

**Path Aliases:**
- Not applicable — no path aliases configured

## Error Handling

**Database operations:**
- Every `db.session.commit()` in route handlers is wrapped in try/except `SQLAlchemyError`
- On error: `db.session.rollback()` + `flash('...', 'danger')` + `redirect()`
- Pattern:
  ```python
  try:
      db.session.commit()
      flash('操作成功！', 'success')
  except SQLAlchemyError:
      db.session.rollback()
      flash('操作失败，请重试。', 'danger')
  ```

**Validation:**
- WTForms validators for form fields: `DataRequired`, `Length`, `NumberRange`, `Email`, `Optional`
- Manual validation for complex business rules in route handlers
- Flash messages for user-facing errors: `flash('当前密码错误！', 'danger')`

**Missing records:**
- `abort(404)` after `db.session.get()` returns None
- Pattern: `order = db.session.get(PurchaseOrder, id)` then `if not order: abort(404)`

**Admin-only access:**
- `_require_admin()` helper in `app/routes/system.py` calls `abort(403)` if `current_user.role != 'admin'`
- Call at top of admin route handlers

**CSRF validation:**
- Manual CSRF check via `validate_csrf_token()` from `app/utils.py` for non-WTForms POST handlers
- Pattern: `if not validate_csrf_token(request.form.get('csrf_token')): flash(...); return redirect(...)`

**Safe commit helper:**
- `safe_commit()` in `app/utils.py` returns `(True, None)` on success, `(False, error_str)` on failure
- Used in some routes as alternative to inline try/except

## Logging

**Framework:** Python stdlib `logging` via `current_app.logger`

**Patterns:**
- Log significant user actions (login, logout, password change, email change)
- Log includes: `user_id`, `action` (Chinese description), `details`, `ip_address`
- Log stored in `Log` model (database audit trail) and also via `current_app.logger.warning()` for failures
- Example from `app/routes/auth.py`:
  ```python
  log = Log(
      user_id=user.id,
      action='用户登录',
      details=f'用户 {user.username} 登录系统',
      ip_address=request.remote_addr
  )
  db.session.add(log)
  ```

## Comments

**When to Comment:**
- Complex business logic (concurrency control, balance calculations)
- Non-obvious SQL expressions
- Section dividers in large route files: `# ==================== 采购退货管理 ====================`
- Chinese comments for business logic explanations
- English comments for technical explanations

**Section Dividers:**
- Used extensively in large route files to separate functional areas
- Pattern: `# ==================== 采购订单管理 ====================`

## Function Design

**Route handlers:**
- Decorate with `@bp.route()`, `@login_required`
- Accept `id` parameter as `int` for entity lookups: `def edit_order(id):`
- Use `db.session.get(Model, id)` for primary key lookups
- Use `abort(404)` for missing entities
- Return `render_template()` for GET or `redirect()` after POST
- Query params: `page = request.args.get('page', 1, type=int)` (always use `type=int`)

**Form handling:**
- WTForms: `form.validate_on_submit()`, `form.field.data`
- Raw form data: `request.form.get('field')`, `request.form.getlist('field[]')`
- Array-style form fields for dynamic line items: `product_id[]`, `quantity[]`, `unit_price[]`

**Financial precision:**
- Use `Decimal` for all monetary calculations, never `float`
- Use `to_decimal()` from `app/utils.py` for conversions
- Use atomic SQL expressions for balance updates via `add_balance()` / `sub_balance()`
- Serialize Decimal to string in JSON responses: `'amount': str(item.amount)`

**Concurrency control:**
- Use `with_for_update()` to lock rows during concurrent modifications on critical paths
- Use `db.session.flush()` to get auto-generated IDs before creating related records
- Use `db.session.refresh(entity)` after atomic SQL updates to sync ORM state

## Module Design

**Blueprint pattern:**
- Each route module exports `bp = Blueprint('name', __name__, url_prefix='/prefix')`
- Registered in `app/__init__.py`: `app.register_blueprint(module.bp)`
- Barrel export in `app/routes/__init__.py`

**Model pattern:**
- One domain per file in `app/models/`
- Barrel import in `app/models/__init__.py` exports all models
- Always import from `app.models` not individual model files

**Shared helpers:**
- `app/utils.py`: `to_decimal()`, `add_balance()`, `sub_balance()`, `safe_commit()`, `generate_order_number()`, `update_stock_and_log()`, Excel styling helpers
- `app/utils_order.py`: `create_stock_log()`, `match_reference_id_filter()`, `rebuild_items_on_error()`
- `app/constants.py`: `OrderStatus`, `ChangeType`, `PaymentMethod`, `UserRole`, `VALID_CHANGE_TYPES`

**Forms:**
- All form classes in single file `app/forms.py`
- WTForms-based with Chinese labels

## Security Conventions

**Authentication:**
- All routes require `@login_required` except login/register
- Logout is POST-only: `@bp.route('/logout', methods=['POST'])`

**CSRF:**
- Enabled globally via `CSRFProtect` in `app/__init__.py`
- Disabled in test config: `app.config['WTF_CSRF_ENABLED'] = False`
- API endpoints exempt from CSRF or use header-based tokens (`X-CSRFToken`, `X-CSRF-Token`)

**Password handling:**
- Werkzeug `generate_password_hash` / `check_password_hash`
- Min 6 chars, max 128 chars enforced in route handler

**Security headers:**
- Set in `app/__init__.py` via `@app.after_request`:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`

---

*Convention analysis: 2026-06-08*
