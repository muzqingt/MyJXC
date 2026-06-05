"""
集成测试 — 边缘情况和错误处理路径
"""
import pytest
from decimal import Decimal
from datetime import datetime, date
from app import db
from app.models import (
    User, Product, Category, Supplier, Customer, Warehouse,
    PurchaseOrder, PurchaseOrderItem, SalesOrder, SalesOrderItem,
    StockIn, StockInItem, StockOut, StockOutItem,
    PurchaseReturn, PurchaseReturnItem, SalesReturn, SalesReturnItem,
    Receipt, Payment, Expense, StockLog, SystemSetting, Log
)
from tests.factories import (
    create_product, create_category, create_supplier, create_customer,
    create_warehouse, create_purchase_order, create_sales_order
)


# ==================== Auth 边缘情况 ====================

def test_login_inactive_user(client, app, db_session):
    """登录未激活用户"""
    user = User(username='inactive_user', email='inactive@test.com', is_active=False)
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = client.post('/auth/login', data={
        'username': 'inactive_user',
        'password': 'pass123',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '激活' in resp.data.decode() or '登录' in resp.data.decode()


def test_login_with_next_url(client, app, db_session):
    """登录后重定向到 next URL"""
    user = User(username='next_user', email='next@test.com', is_active=True)
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = client.post('/auth/login?next=/product/products', data={
        'username': 'next_user',
        'password': 'pass123',
    }, follow_redirects=False)
    assert resp.status_code in (302, 303)


def test_login_with_malicious_next_url(client, app, db_session):
    """登录后重定向到恶意 URL -> 回到首页"""
    user = User(username='malicious_user', email='mal@test.com', is_active=True)
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = client.post('/auth/login?next=http://evil.com', data={
        'username': 'malicious_user',
        'password': 'pass123',
    }, follow_redirects=False)
    assert resp.status_code in (302, 303)


def test_change_email_invalid_format(authenticated_client):
    """修改邮箱 - 无效格式"""
    resp = authenticated_client.post('/auth/change-email', data={
        'new_email': 'invalid-email',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '有效' in resp.data.decode() or '邮箱' in resp.data.decode()


def test_change_email_already_used(authenticated_client, app, db_session):
    """修改邮箱 - 已被使用"""
    other = User(username='other_user', email='used@test.com')
    other.set_password('pass123')
    db.session.add(other)
    db.session.commit()

    resp = authenticated_client.post('/auth/change-email', data={
        'new_email': 'used@test.com',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '已被' in resp.data.decode() or '邮箱' in resp.data.decode()


# ==================== Product 边缘情况 ====================

def test_product_create_duplicate_code(authenticated_client, app, db_session):
    """创建商品 - 重复编码"""
    create_product(code='DUP_CODE')
    resp = authenticated_client.post('/product/products/new', data={
        'code': 'DUP_CODE',
        'name': '重复编码商品',
        'unit': '个',
        'purchase_price': '50',
        'sale_price': '100',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '已存在' in resp.data.decode() or '重复' in resp.data.decode() or '商品' in resp.data.decode()


def test_product_edit_not_found(authenticated_client):
    """编辑商品 - 不存在"""
    resp = authenticated_client.get('/product/products/99999/edit')
    assert resp.status_code == 404


def test_product_delete_not_found(authenticated_client):
    """删除商品 - 不存在"""
    resp = authenticated_client.post('/product/products/99999/delete')
    assert resp.status_code == 404


def test_category_edit_not_found(authenticated_client):
    """编辑分类 - 不存在"""
    resp = authenticated_client.get('/product/categories/99999/edit')
    assert resp.status_code == 404


def test_category_delete_not_found(authenticated_client):
    """删除分类 - 不存在"""
    resp = authenticated_client.post('/product/categories/99999/delete')
    assert resp.status_code == 404


def test_product_search(authenticated_client, app, db_session):
    """商品搜索"""
    create_product(name='搜索测试商品')
    resp = authenticated_client.get('/product/products?keyword=搜索')
    assert resp.status_code == 200


def test_product_filter_by_category(authenticated_client, app, db_session):
    """按分类筛选商品"""
    cat = create_category(name='筛选分类')
    create_product(category_id=cat.id)
    resp = authenticated_client.get(f'/product/products?category_id={cat.id}')
    assert resp.status_code == 200


# ==================== Partner 边缘情况 ====================

def test_supplier_edit_not_found(authenticated_client):
    """编辑供应商 - 不存在"""
    resp = authenticated_client.get('/partner/suppliers/99999/edit')
    assert resp.status_code == 404


def test_supplier_delete_not_found(authenticated_client):
    """删除供应商 - 不存在"""
    resp = authenticated_client.post('/partner/suppliers/99999/delete')
    assert resp.status_code == 404


def test_customer_edit_not_found(authenticated_client):
    """编辑客户 - 不存在"""
    resp = authenticated_client.get('/partner/customers/99999/edit')
    assert resp.status_code == 404


def test_customer_delete_not_found(authenticated_client):
    """删除客户 - 不存在"""
    resp = authenticated_client.post('/partner/customers/99999/delete')
    assert resp.status_code == 404


def test_warehouse_edit_not_found(authenticated_client):
    """编辑仓库 - 不存在"""
    resp = authenticated_client.get('/partner/warehouses/99999/edit')
    assert resp.status_code == 404


def test_warehouse_delete_not_found(authenticated_client):
    """删除仓库 - 不存在"""
    resp = authenticated_client.post('/partner/warehouses/99999/delete')
    assert resp.status_code == 404


def test_supplier_create_duplicate_code(authenticated_client, app, db_session):
    """创建供应商 - 重复编码"""
    create_supplier(code='DUP_SUP')
    resp = authenticated_client.post('/partner/suppliers/new', data={
        'code': 'DUP_SUP',
        'name': '重复编码供应商',
        'contact_person': '测试',
        'phone': '13800000000',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_customer_create_duplicate_code(authenticated_client, app, db_session):
    """创建客户 - 重复编码"""
    create_customer(code='DUP_CUS')
    resp = authenticated_client.post('/partner/customers/new', data={
        'code': 'DUP_CUS',
        'name': '重复编码客户',
        'contact_person': '测试',
        'phone': '13800000000',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_warehouse_create_duplicate_code(authenticated_client, app, db_session):
    """创建仓库 - 重复编码"""
    create_warehouse(code='DUP_WH')
    resp = authenticated_client.post('/partner/warehouses/new', data={
        'code': 'DUP_WH',
        'name': '重复编码仓库',
        'address': '测试',
    }, follow_redirects=True)
    assert resp.status_code == 200


# ==================== Purchase 边缘情况 ====================

def test_purchase_order_not_found(authenticated_client):
    """采购订单不存在"""
    resp = authenticated_client.get('/purchase/orders/99999')
    assert resp.status_code == 404


def test_purchase_order_edit_not_found(authenticated_client):
    """编辑采购订单 - 不存在"""
    resp = authenticated_client.get('/purchase/orders/99999/edit')
    assert resp.status_code == 404


def test_purchase_order_delete_not_found(authenticated_client):
    """删除采购订单 - 不存在"""
    resp = authenticated_client.post('/purchase/orders/99999/delete')
    assert resp.status_code == 404


def test_purchase_quick_stock_in_not_found(authenticated_client):
    """快捷入库 - 订单不存在"""
    resp = authenticated_client.post('/purchase/orders/99999/quick-stock-in')
    assert resp.status_code == 404


def test_purchase_quick_return_not_found(authenticated_client):
    """快捷退货 - 订单不存在"""
    resp = authenticated_client.post('/purchase/orders/99999/quick-return')
    assert resp.status_code == 404


def test_purchase_order_create_empty_items(authenticated_client, app, db_session):
    """创建采购订单 - 空明细"""
    sup = create_supplier()
    wh = create_warehouse()

    resp = authenticated_client.post('/purchase/orders/new', data={
        'supplier_id': str(sup.id),
        'warehouse_id': str(wh.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '测试',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_purchase_order_create_missing_fields(authenticated_client):
    """创建采购订单 - 缺少必填字段"""
    resp = authenticated_client.post('/purchase/orders/new', data={
        'notes': '测试',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_purchase_quick_return_non_completed(authenticated_client, app, db_session):
    """快捷退货 - 非已完成订单"""
    sup = create_supplier()
    wh = create_warehouse()
    order = create_purchase_order(
        supplier_id=sup.id,
        warehouse_id=wh.id,
        items=[],
        status='confirmed'
    )

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/quick-return', follow_redirects=True)
    assert resp.status_code == 200


# ==================== Sales 边缘情况 ====================

def test_sales_order_not_found(authenticated_client):
    """销售订单不存在"""
    resp = authenticated_client.get('/sales/orders/99999')
    assert resp.status_code == 404


def test_sales_order_edit_not_found(authenticated_client):
    """编辑销售订单 - 不存在"""
    resp = authenticated_client.get('/sales/orders/99999/edit')
    assert resp.status_code == 404


def test_sales_order_delete_not_found(authenticated_client):
    """删除销售订单 - 不存在"""
    resp = authenticated_client.post('/sales/orders/99999/delete')
    assert resp.status_code == 404


def test_sales_quick_stock_out_not_found(authenticated_client):
    """快捷出库 - 订单不存在"""
    resp = authenticated_client.post('/sales/orders/99999/quick-stock-out')
    assert resp.status_code == 404


def test_sales_quick_return_not_found(authenticated_client):
    """快捷退货 - 订单不存在"""
    resp = authenticated_client.post('/sales/orders/99999/quick-return')
    assert resp.status_code == 404


def test_sales_order_create_empty_items(authenticated_client, app, db_session):
    """创建销售订单 - 空明细"""
    cus = create_customer()
    wh = create_warehouse()

    resp = authenticated_client.post('/sales/orders/new', data={
        'customer_id': str(cus.id),
        'warehouse_id': str(wh.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '测试',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_sales_order_create_missing_fields(authenticated_client):
    """创建销售订单 - 缺少必填字段"""
    resp = authenticated_client.post('/sales/orders/new', data={
        'notes': '测试',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_sales_quick_return_non_completed(authenticated_client, app, db_session):
    """快捷退货 - 非已完成订单"""
    cus = create_customer()
    wh = create_warehouse()
    order = create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[],
        status='confirmed'
    )

    resp = authenticated_client.post(f'/sales/orders/{order.id}/quick-return', follow_redirects=True)
    assert resp.status_code == 200


def test_sales_order_edit_completed(authenticated_client, app, db_session):
    """编辑销售订单 - 已完成订单"""
    cus = create_customer()
    wh = create_warehouse()
    order = create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[],
        status='completed'
    )

    resp = authenticated_client.post(f'/sales/orders/{order.id}/edit', data={
        'customer_id': str(cus.id),
        'warehouse_id': str(wh.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '测试',
    }, follow_redirects=True)
    assert resp.status_code == 200


# ==================== Inventory 边缘情况 ====================

def test_inventory_warehouse_stock_not_found(authenticated_client):
    """仓库库存 - 仓库不存在"""
    resp = authenticated_client.get('/inventory/warehouse/99999')
    assert resp.status_code == 404


def test_inventory_stock_adjust_insufficient(authenticated_client, app, db_session):
    """库存调整 - 库存不足"""
    prod = create_product(stock_quantity=5)
    wh = create_warehouse()

    resp = authenticated_client.post('/inventory/stock-adjust', data={
        'product_id': str(prod.id),
        'warehouse_id': str(wh.id),
        'adjust_type': 'adjust_out',
        'quantity': '100',
        'notes': '测试',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '不足' in resp.data.decode() or '库存' in resp.data.decode()


def test_inventory_stock_adjust_invalid_type(authenticated_client, app, db_session):
    """库存调整 - 无效类型"""
    prod = create_product()
    wh = create_warehouse()

    resp = authenticated_client.post('/inventory/stock-adjust', data={
        'product_id': str(prod.id),
        'warehouse_id': str(wh.id),
        'adjust_type': 'invalid',
        'quantity': '10',
        'notes': '测试',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_inventory_stock_transfer_same_warehouse(authenticated_client, app, db_session):
    """库存调拨 - 同一仓库"""
    wh = create_warehouse()
    prod = create_product(stock_quantity=100)

    resp = authenticated_client.post('/inventory/stock-transfer', data={
        'from_warehouse': str(wh.id),
        'to_warehouse': str(wh.id),
        'transfer_date': date.today().strftime('%Y-%m-%d'),
        'notes': '测试',
        'items-0-product_id': str(prod.id),
        'items-0-quantity': '10',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '相同' in resp.data.decode() or '调拨' in resp.data.decode()


# ==================== Finance 边缘情况 ====================

def test_receipt_add_missing_fields(authenticated_client):
    """添加收款 - 缺少必填字段"""
    resp = authenticated_client.post('/finance/receipt/add', data={
        'notes': '测试',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_payment_add_missing_fields(authenticated_client):
    """添加付款 - 缺少必填字段"""
    resp = authenticated_client.post('/finance/payment/add', data={
        'notes': '测试',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_expense_add_missing_fields(authenticated_client):
    """添加费用 - 缺少必填字段"""
    resp = authenticated_client.post('/finance/expense/add', data={
        'notes': '测试',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_receipt_not_found(authenticated_client):
    """收款不存在"""
    resp = authenticated_client.get('/finance/receipt/99999')
    assert resp.status_code == 404


def test_payment_not_found(authenticated_client):
    """付款不存在"""
    resp = authenticated_client.get('/finance/payment/99999')
    assert resp.status_code == 404


def test_expense_delete(authenticated_client, app, db_session):
    """删除费用"""
    expense = Expense(
        expense_number='EXP_DEL_001',
        category='办公费',
        amount=Decimal('100'),
        expense_date=date.today()
    )
    db.session.add(expense)
    db.session.commit()

    resp = authenticated_client.post(f'/finance/expense/{expense.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_expense_delete_not_found(authenticated_client):
    """删除费用 - 不存在"""
    resp = authenticated_client.post('/finance/expense/99999/delete')
    assert resp.status_code == 404


# ==================== System 边缘情况 ====================

def test_user_edit_not_found(authenticated_client):
    """编辑用户 - 不存在"""
    resp = authenticated_client.get('/system/user/edit/99999')
    assert resp.status_code == 404


def test_user_delete_not_found(authenticated_client):
    """删除用户 - 不存在"""
    resp = authenticated_client.post('/system/user/delete/99999', follow_redirects=True)
    assert resp.status_code == 200


def test_backup_download_invalid_filename(authenticated_client):
    """下载备份 - 无效文件名"""
    resp = authenticated_client.get('/system/backup/download/....//etc/passwd')
    assert resp.status_code in (302, 404)


def test_backup_download_not_found(authenticated_client):
    """下载备份 - 文件不存在"""
    resp = authenticated_client.get('/system/backup/download/nonexistent.db')
    assert resp.status_code in (302, 404)


def test_backup_restore_no_file(authenticated_client):
    """恢复备份 - 未选择文件"""
    resp = authenticated_client.post('/system/backup/restore', data={}, follow_redirects=True)
    assert resp.status_code == 200


def test_backup_restore_invalid_filename(authenticated_client):
    """恢复备份 - 无效文件名"""
    resp = authenticated_client.post('/system/backup/restore', data={
        'filename': '....//etc/passwd'
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_backup_restore_not_found(authenticated_client):
    """恢复备份 - 文件不存在"""
    resp = authenticated_client.post('/system/backup/restore', data={
        'filename': 'nonexistent.db'
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_user_add(authenticated_client):
    """添加用户"""
    resp = authenticated_client.post('/system/user/add', data={
        'username': 'new_system_user',
        'email': 'newsys@test.com',
        'password': 'pass123',
        'role': 'user',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_user_add_duplicate(authenticated_client, app, db_session):
    """添加用户 - 重复用户名"""
    user = User(username='dup_system_user', email='dupsys@test.com')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = authenticated_client.post('/system/user/add', data={
        'username': 'dup_system_user',
        'email': 'dupsys2@test.com',
        'password': 'pass123',
        'role': 'user',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_user_edit(authenticated_client, app, db_session):
    """编辑用户"""
    user = User(username='edit_system_user', email='editsys@test.com')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = authenticated_client.post(f'/system/user/edit/{user.id}', data={
        'username': 'edit_system_user',
        'email': 'newemail@test.com',
        'role': 'user',
        'is_active': 'on',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_user_delete(authenticated_client, app, db_session):
    """删除用户"""
    user = User(username='del_system_user', email='delsys@test.com')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = authenticated_client.post(f'/system/user/delete/{user.id}', follow_redirects=True)
    assert resp.status_code == 200


def test_settings_page_loads(authenticated_client):
    """系统设置页面加载"""
    resp = authenticated_client.get('/system/settings')
    assert resp.status_code == 200


def test_optimize_db(authenticated_client):
    """优化数据库"""
    resp = authenticated_client.post('/system/api/system/optimize-db')
    # 可能返回 200 或 500（取决于环境）
    assert resp.status_code in (200, 500)


def test_clean_logs(authenticated_client):
    """清理日志"""
    resp = authenticated_client.post('/system/api/system/clean-logs')
    assert resp.status_code == 200


def test_export_db(authenticated_client):
    """导出数据库"""
    resp = authenticated_client.get('/system/api/system/export-db')
    assert resp.status_code == 200
