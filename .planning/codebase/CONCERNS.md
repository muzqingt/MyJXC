# Codebase Concerns

**Analysis Date:** 2026-06-08

## Tech Debt

**Comma-Separated reference_id (Relational Anti-Pattern):**
- Issue: `Receipt.reference_id` and `Payment.reference_id` store comma-separated order IDs as `String(500)` instead of using a junction table or foreign key.
- Files: `my-jxc/app/models/finance.py:15`, `my-jxc/app/models/finance.py:37`
- Impact: Breaks referential integrity, requires fragile LIKE-based queries (`my-jxc/app/utils_order.py:13-33`), makes it impossible to use proper foreign keys or cascade deletes. Query performance degrades as data grows since LIKE '%id%' cannot use indexes effectively.
- Fix approach: Create `receipt_order_links` and `payment_order_links` junction tables with proper foreign keys. Migrate existing comma-separated data. Update `match_reference_id_filter()` and `calc_order_paid_amount()` in `my-jxc/app/routes/finance.py:16-34`.

**Fat Route Handlers (No Service Layer):**
- Issue: All business logic lives directly in route handlers. No service, repository, or domain abstractions exist.
- Files: `my-jxc/app/routes/purchase.py` (1216 lines), `my-jxc/app/routes/sales.py` (1243 lines), `my-jxc/app/routes/finance.py` (1226 lines), `my-jxc/app/routes/inventory.py` (695 lines)
- Impact: Extreme code duplication (purchase and sales flows are near-identical), difficult to test business logic in isolation, hard to maintain or extend.
- Fix approach: Extract shared business logic into `app/services/` module. Start with `StockService` (stock in/out/transfer), `OrderService` (order CRUD + status transitions), `FinanceService` (receipt/payment/expense + balance updates).

**Duplicate Stock Log Creation Functions:**
- Issue: Two separate functions create stock logs with identical logic: `update_stock_and_log()` in `my-jxc/app/utils.py:149` and `create_stock_log()` in `my-jxc/app/utils_order.py:54`.
- Files: `my-jxc/app/utils.py:149-196`, `my-jxc/app/utils_order.py:54-103`
- Impact: Confusion about which to use, risk of divergent behavior if only one is updated.
- Fix approach: Consolidate into a single function in `my-jxc/app/utils.py`. Update all callers.

**All Forms in Single File:**
- Issue: All 18+ WTForms classes are in one file, making it large and hard to navigate.
- Files: `my-jxc/app/forms.py` (210 lines)
- Impact: Merge conflicts when multiple features modify forms simultaneously. Not blocking but grows with each new feature.
- Fix approach: Split into `app/forms/auth.py`, `app/forms/purchase.py`, `app/forms/sales.py`, `app/forms/finance.py`, `app/forms/inventory.py`. Keep barrel import in `app/forms/__init__.py`.

**Missing Database Indexes on Foreign Keys:**
- Issue: Many foreign key columns lack indexes, slowing JOINs and filtered queries.
- Files: `my-jxc/app/models/purchase.py:10-11` (`supplier_id`, `warehouse_id`), `my-jxc/app/models/sales.py:10-11` (`customer_id`, `warehouse_id`), `my-jxc/app/models/inventory.py:9-10` (`product_id`, `warehouse_id`), all `created_by` columns
- Impact: Queries filtering by supplier, customer, warehouse, or creator become full table scans as data grows.
- Fix approach: Add `index=True` to foreign key columns, or create composite indexes for common query patterns. Use Alembic migration.

## Known Bugs

**Order Number Race Condition:**
- Symptoms: Two concurrent requests can generate identical order numbers, causing a unique constraint violation on commit.
- Files: `my-jxc/app/utils.py:77-117` (`generate_order_number`)
- Trigger: Two users creating orders of the same type at the same moment (within the same second).
- Workaround: The unique constraint on `order_number` columns causes the second commit to fail with an IntegrityError. The user sees a generic "creation failed" error and must retry. Not a silent data corruption but a poor UX.
- Fix approach: Wrap order number generation in a database-level advisory lock, or use `SELECT ... FOR UPDATE` on a sequence table, or retry on IntegrityError with a new number.

**Default Admin Password Hardcoded:**
- Symptoms: Every fresh installation creates admin account with password `admin123`.
- Files: `my-jxc/run.py:98-99`
- Trigger: New deployment or database reset.
- Workaround: None built-in. User must manually change password after first login.
- Fix approach: Force password change on first login, or generate a random password and display it once during `init_database()`.

## Security Considerations

**HTTP in Production by Default:**
- Risk: `ProductionConfig` sets `SESSION_COOKIE_SECURE = False` unless `SECURE_COOKIES=1` env var is set. Session cookies are transmitted in cleartext over HTTP.
- Files: `my-jxc/config.py:57-64`
- Current mitigation: LAN-only deployment assumption. Security headers set in `my-jxc/app/__init__.py:72-77` (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy).
- Recommendations: Document the HTTPS requirement prominently. Consider adding a startup warning when running in production mode without `SECURE_COOKIES=1`.

**No Business-Level Authorization:**
- Risk: Any authenticated user can view/modify any entity (all customers, all suppliers, all orders). Only admin vs. user role distinction exists.
- Files: `my-jxc/app/routes/finance.py:730` (TODO comment), `my-jxc/app/routes/finance.py:1108` (TODO comment)
- Current mitigation: `_require_admin()` in `my-jxc/app/routes/system.py:14-16` protects system-level operations only.
- Recommendations: Add ownership checks on order/financial record operations. At minimum, non-admin users should only see records they created unless explicitly granted access.

**No Rate Limiting:**
- Risk: Login endpoint has no brute-force protection. An attacker can attempt unlimited password guesses.
- Files: `my-jxc/app/routes/auth.py:15-59`
- Current mitigation: None.
- Recommendations: Add Flask-Limiter or implement account lockout after N failed attempts. Log failed login attempts with IP address.

**No Password Complexity Enforcement Beyond Length:**
- Risk: Passwords like `123456` or `aaaaaa` pass validation (only length >= 6 checked).
- Files: `my-jxc/app/routes/auth.py:124`, `my-jxc/app/routes/system.py:344`
- Current mitigation: None.
- Recommendations: Add minimum complexity requirements (uppercase, digit, or special character).

**Backup Files Accessible Without Expiry:**
- Risk: Backup `.db` files accumulate in `backups/` directory with no automatic cleanup. Contains full database including password hashes.
- Files: `my-jxc/app/routes/system.py:52-95`
- Current mitigation: `_require_admin()` guards all backup endpoints. `_safe_filename()` prevents path traversal in `my-jxc/app/routes/system.py:18-23`.
- Recommendations: Add automatic backup rotation (e.g., keep last 10). Encrypt backups at rest.

**Clean Logs Uses Inefficient Deletion:**
- Risk: `clean_logs()` loads up to 1000 Log objects into Python memory, then deletes them one by one.
- Files: `my-jxc/app/routes/system.py:442-459`
- Current mitigation: `.limit(1000)` prevents unbounded load.
- Fix approach: Use `Log.query.filter(Log.created_at < cutoff_date).delete()` for bulk deletion.

## Performance Bottlenecks

**N+1 Query in StockLog.reference_number:**
- Problem: Each access to `StockLog.reference_number` triggers up to 6 separate database queries (one per reference_type branch).
- Files: `my-jxc/app/models/inventory.py:25-55`
- Cause: The property uses `Model.query.get()` for each log entry. When displaying a list of 50 stock logs, this creates up to 300 additional queries.
- Improvement path: Eager-load related entities using `selectinload()` when querying StockLogs. Or store the reference_number directly on StockLog as a denormalized column.

**Unpaginated .all() Calls (54 instances):**
- Problem: Many routes load entire tables into memory without pagination.
- Files: `my-jxc/app/routes/inventory.py:41-42` (all products + all warehouses on every page load), `my-jxc/app/routes/sales.py:100-103` (all customers + warehouses + products), `my-jxc/app/routes/product.py:73` (all categories), `my-jxc/app/routes/purchase.py:70-71` (all suppliers + warehouses)
- Cause: Convenience — querying all records for dropdowns and filters.
- Improvement path: For dropdowns, use AJAX-based search/select (already partially implemented via `api_products()` endpoints). For product lists, add pagination. Track the 54 call sites in `my-jxc/app/routes/` and prioritize the inventory index (loads all products on every visit).

**Dashboard N+1 Warehouse Query:**
- Problem: `api_stock_overview()` iterates all warehouses and runs 2 queries per warehouse to calculate stock.
- Files: `my-jxc/app/routes/main.py:53-79`
- Cause: Stock is calculated from StockLog aggregation rather than stored on the product/warehouse level.
- Improvement path: Use a single GROUP BY query: `SELECT warehouse_id, change_type, SUM(quantity) FROM stock_logs GROUP BY warehouse_id, change_type`. Or materialize warehouse-level stock in a separate table.

**Excel Export Loads All Records:**
- Problem: All Excel export routes load entire result sets into memory before generating the file.
- Files: `my-jxc/app/routes/finance.py:736-739` (all orders for a customer), `my-jxc/app/routes/finance.py:846-906` (all receipts), `my-jxc/app/routes/report.py` (all products for inventory report)
- Cause: openpyxl requires all data in memory.
- Improvement path: For large datasets, consider streaming CSV as an alternative. Add date range limits to exports.

## Fragile Areas

**Order Number Generation:**
- Files: `my-jxc/app/utils.py:77-117`
- Why fragile: Uses LIKE pattern matching on order numbers to find the last sequence number. Relies on the format `{PREFIX}{YYYYMMDD}{NNNN}` being consistent. If an order number is manually edited or the format changes, the sequence breaks. Also has no protection against concurrent generation (see race condition bug above).
- Safe modification: Do not change the order number format without updating all parsing logic. Add a dedicated sequence table if reliability is critical.
- Test coverage: `my-jxc/tests/test_utils_order.py` exists but may not cover concurrent scenarios.

**Stock Quantity Update Without Atomic Locking:**
- Files: `my-jxc/app/utils.py:149-196` (`update_stock_and_log`), `my-jxc/app/utils_order.py:54-103` (`create_stock_log`)
- Why fragile: Both functions read `product.stock_quantity`, compute the new value in Python, then write it back. Although `with_for_update()` is used at the call site (in route handlers), the lock + read + write is not atomic at the database level — it relies on the caller remembering to lock the product row first.
- Safe modification: Always call `with_for_update()` on the Product row before calling either stock update function. Consider moving the lock inside the utility function.
- Test coverage: Integration tests exist in `my-jxc/tests/test_integration.py` but concurrent scenarios are not tested.

**Database Path Parsing:**
- Files: `my-jxc/app/routes/system.py:63` (`current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')`)
- Why fragile: String replacement to extract the file path. Breaks if the URI contains query parameters or uses a different format (e.g., `sqlite:///./instance/store.db` with relative paths).
- Safe modification: Use `from sqlalchemy.engine.url import make_url` to parse the URI properly.
- Test coverage: Not unit tested.

## Scaling Limits

**SQLite Single-Writer:**
- Current capacity: Supports ~100 concurrent read requests, 1 write at a time.
- Limit: Under concurrent write load (e.g., multiple users creating orders simultaneously), SQLite's write lock causes serialization and potential `database is locked` errors.
- Scaling path: For more than ~5 concurrent writers, migrate to PostgreSQL or MySQL. The codebase uses SQLAlchemy ORM which abstracts the database, but raw SQL in a few places (VACUUM, stock overview queries) would need updating.

**Order Number Sequence:**
- Current capacity: 9999 orders per day per prefix (4-digit sequence).
- Limit: If a business processes > 9999 purchase orders in a single day, the sequence wraps to 0001 and collides.
- Scaling path: Increase sequence digits to 6, or switch to a database sequence/auto-increment approach.

## Dependencies at Risk

**Flask-Bootstrap 3.3.7.1:**
- Risk: Pinned to Bootstrap 3, which reached end of life. The templates actually load Bootstrap 5.3.0 from CDN in `my-jxc/app/templates/base.html`, making the Flask-Bootstrap extension largely unused for styling.
- Impact: Conflicting Bootstrap versions could cause layout issues. The extension adds overhead without benefit.
- Migration plan: Remove Flask-Bootstrap dependency. Use Bootstrap 5 CDN directly (already done in templates). Replace any `{{ bootstrap.load_css() }}` calls with manual CDN links.

**Flask 2.3.3 / Werkzeug 2.3.7:**
- Risk: These are not the latest versions. Flask 3.x and Werkzeug 3.x have been released with breaking changes.
- Impact: Security patches may not be backported to 2.x indefinitely.
- Migration plan: Test upgrade to Flask 3.x in a branch. Key changes: removal of deprecated `flask.ext` imports, JSON provider changes.

## Missing Critical Features

**No Automated Backups:**
- Problem: Backup is manual-only via the admin panel. If the admin forgets, data loss risk increases.
- Blocks: Disaster recovery.

**No Audit Trail for Financial Deletions:**
- Problem: When receipts/payments are deleted, the corresponding balance adjustments are reversed, but no log entry is created recording who deleted what and when.
- Files: `my-jxc/app/routes/finance.py` (delete handlers)
- Blocks: Compliance and forensic analysis.

## Test Coverage Gaps

**Concurrent Write Scenarios:**
- What's not tested: Two users creating orders simultaneously, concurrent stock modifications, race conditions in order number generation.
- Files: `my-jxc/app/utils.py:77-117` (generate_order_number), all `with_for_update()` code paths
- Risk: Silent data corruption or IntegrityError crashes under concurrent load.
- Priority: Medium (low for single-user desktop deployment, high if multi-user LAN usage increases)

**Excel Export Routes:**
- What's not tested: Excel file generation and content correctness.
- Files: `my-jxc/app/routes/finance.py` (6 export functions), `my-jxc/app/routes/report.py` (multiple export functions)
- Risk: Export bugs (wrong data, formatting issues) ship unnoticed.
- Priority: Medium

**Error Recovery Paths:**
- What's not tested: Rollback behavior when partial operations fail (e.g., stock update succeeds but balance update fails).
- Files: All route handlers with nested try/except blocks
- Risk: Database could be left in an inconsistent state if error handling has bugs.
- Priority: High

**StockLog.reference_number Property:**
- What's not tested: The 6-branch conditional in the property that resolves reference IDs to human-readable numbers.
- Files: `my-jxc/app/models/inventory.py:25-55`
- Risk: If a reference type is added but the property isn't updated, it silently returns empty string.
- Priority: Low

---

*Concerns audit: 2026-06-08*
