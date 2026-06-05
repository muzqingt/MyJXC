"""
完整集成测试 — 覆盖所有路由的未测试路径
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


# ==================== Auth 路由测试 ====================

def test_login_already_authenticated(authenticated_client):
    """已登录用户访问登录页 -> 重定向"""
    resp = authenticated_client.get('/auth/login', follow_redirects=False)
    assert resp.status_code in (302, 303)


def test_register_page(client):
    """注册页面"""
    resp = client.get('/auth/register')
    assert resp.status_code == 200
    assert '注册' in resp.data.decode()


def test_register_success(client):
    """注册成功"""
    resp = client.post('/auth/register', data={
        'username': 'newuser_test',
        'email': 'newuser@test.com',
        'password': 'pass123',
        'password2': 'pass123',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_register_duplicate(client, app, db_session):
    """注册重复用户名"""
    user = User(username='dup_user', email='dup@test.com')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = client.post('/auth/register', data={
        'username': 'dup_user',
        'email': 'dup2@test.com',
        'password': 'pass123',
        'password2': 'pass123',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '已存在' in resp.data.decode() or '注册' in resp.data.decode()


def test_register_already_authenticated(authenticated_client):
    """已登录用户访问注册页 -> 重定向"""
    resp = authenticated_client.get('/auth/register', follow_redirects=False)
    assert resp.status_code in (302, 303)


def test_logout(authenticated_client):
    """登出"""
    resp = authenticated_client.post('/auth/logout', follow_redirects=True)
    assert resp.status_code == 200


def test_profile(authenticated_client):
    """个人资料"""
    resp = authenticated_client.get('/auth/profile')
    assert resp.status_code == 200


def test_change_password_success(authenticated_client):
    """修改密码成功"""
    resp = authenticated_client.post('/auth/change-password', data={
        'old_password': 'admin123',
        'new_password': 'newpass123',
        'confirm_password': 'newpass123',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_change_password_wrong_old(authenticated_client):
    """修改密码 - 旧密码错误"""
    resp = authenticated_client.post('/auth/change-password', data={
        'old_password': 'wrongpass',
        'new_password': 'newpass123',
        'confirm_password': 'newpass123',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_change_password_too_short(authenticated_client):
    """修改密码 - 新密码太短"""
    resp = authenticated_client.post('/auth/change-password', data={
        'old_password': 'admin123',
        'new_password': '123',
        'confirm_password': '123',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_change_password_mismatch(authenticated_client):
    """修改密码 - 两次输入不一致"""
    resp = authenticated_client.post('/auth/change-password', data={
        'old_password': 'admin123',
        'new_password': 'newpass123',
        'confirm_password': 'different',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_change_email_success(authenticated_client):
    """修改邮箱成功"""
    resp = authenticated_client.post('/auth/change-email', data={
        'new_email': 'newemail@test.com',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_change_email_empty(authenticated_client):
    """修改邮箱 - 空邮箱"""
    resp = authenticated_client.post('/auth/change-email', data={
        'new_email': '',
    }, follow_redirects=True)
    assert resp.status_code == 200


# ==================== Product 路由测试 ====================

def test_product_list(authenticated_client):
    """商品列表"""
    resp = authenticated_client.get('/product/products')
    assert resp.status_code == 200


def test_product_create(authenticated_client, app, db_session):
    """创建商品"""
    cat = create_category()
    resp = authenticated_client.post('/product/products/new', data={
        'code': 'INT_PROD_001',
        'name': '集成测试商品',
        'category_id': str(cat.id),
        'unit': '个',
        'purchase_price': '50',
        'sale_price': '100',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_product_edit(authenticated_client, app, db_session):
    """编辑商品"""
    product = create_product(code='EDIT_PROD_INT')
    resp = authenticated_client.post(f'/product/products/{product.id}/edit', data={
        'code': 'EDIT_PROD_INT',
        'name': '已编辑商品',
        'unit': '个',
        'purchase_price': '60',
        'sale_price': '120',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_product_delete(authenticated_client, app, db_session):
    """删除商品"""
    product = create_product(code='DEL_PROD_INT')
    resp = authenticated_client.post(f'/product/products/{product.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_product_detail(authenticated_client, app, db_session):
    """商品详情"""
    product = create_product(code='DETAIL_PROD_INT')
    resp = authenticated_client.get(f'/product/products/{product.id}')
    assert resp.status_code == 200


def test_product_not_found(authenticated_client):
    """商品不存在"""
    resp = authenticated_client.get('/product/products/99999')
    assert resp.status_code == 404


def test_category_list(authenticated_client):
    """分类列表"""
    resp = authenticated_client.get('/product/categories')
    assert resp.status_code == 200


def test_category_create(authenticated_client):
    """创建分类"""
    resp = authenticated_client.post('/product/categories/new', data={
        'name': '集成测试分类',
        'description': '测试',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_category_edit(authenticated_client, app, db_session):
    """编辑分类"""
    cat = create_category(name='编辑分类')
    resp = authenticated_client.post(f'/product/categories/{cat.id}/edit', data={
        'name': '已编辑分类',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_category_delete(authenticated_client, app, db_session):
    """删除分类"""
    cat = create_category(name='删除分类')
    resp = authenticated_client.post(f'/product/categories/{cat.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_product_api(authenticated_client):
    """商品 API"""
    resp = authenticated_client.get('/product/api/products')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_product_import_page(authenticated_client):
    """商品导入页面"""
    resp = authenticated_client.get('/product/import')
    assert resp.status_code == 200


# ==================== Partner 路由测试 ====================

def test_supplier_list(authenticated_client):
    """供应商列表"""
    resp = authenticated_client.get('/partner/suppliers')
    assert resp.status_code == 200


def test_supplier_create(authenticated_client):
    """创建供应商"""
    resp = authenticated_client.post('/partner/suppliers/new', data={
        'code': 'INT_SUP_001',
        'name': '集成测试供应商',
        'contact_person': '张三',
        'phone': '13800000001',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_supplier_edit(authenticated_client, app, db_session):
    """编辑供应商"""
    sup = create_supplier(code='EDIT_SUP_INT')
    resp = authenticated_client.post(f'/partner/suppliers/{sup.id}/edit', data={
        'code': 'EDIT_SUP_INT',
        'name': '已编辑供应商',
        'contact_person': '李四',
        'phone': '13900000001',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_supplier_delete(authenticated_client, app, db_session):
    """删除供应商"""
    sup = create_supplier(code='DEL_SUP_INT')
    resp = authenticated_client.post(f'/partner/suppliers/{sup.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_supplier_not_found(authenticated_client):
    """供应商不存在"""
    resp = authenticated_client.get('/partner/suppliers/99999/edit')
    assert resp.status_code == 404


def test_customer_list(authenticated_client):
    """客户列表"""
    resp = authenticated_client.get('/partner/customers')
    assert resp.status_code == 200


def test_customer_create(authenticated_client):
    """创建客户"""
    resp = authenticated_client.post('/partner/customers/new', data={
        'code': 'INT_CUS_001',
        'name': '集成测试客户',
        'contact_person': '李四',
        'phone': '13900000001',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_customer_edit(authenticated_client, app, db_session):
    """编辑客户"""
    cus = create_customer(code='EDIT_CUS_INT')
    resp = authenticated_client.post(f'/partner/customers/{cus.id}/edit', data={
        'code': 'EDIT_CUS_INT',
        'name': '已编辑客户',
        'contact_person': '王五',
        'phone': '13700000001',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_customer_delete(authenticated_client, app, db_session):
    """删除客户"""
    cus = create_customer(code='DEL_CUS_INT')
    resp = authenticated_client.post(f'/partner/customers/{cus.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_warehouse_list(authenticated_client):
    """仓库列表"""
    resp = authenticated_client.get('/partner/warehouses')
    assert resp.status_code == 200


def test_warehouse_create(authenticated_client):
    """创建仓库"""
    resp = authenticated_client.post('/partner/warehouses/new', data={
        'code': 'INT_WH_001',
        'name': '集成测试仓库',
        'address': '测试地址',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_warehouse_edit(authenticated_client, app, db_session):
    """编辑仓库"""
    wh = create_warehouse(code='EDIT_WH_INT')
    resp = authenticated_client.post(f'/partner/warehouses/{wh.id}/edit', data={
        'code': 'EDIT_WH_INT',
        'name': '已编辑仓库',
        'address': '新地址',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_warehouse_delete(authenticated_client, app, db_session):
    """删除仓库"""
    wh = create_warehouse(code='DEL_WH_INT')
    resp = authenticated_client.post(f'/partner/warehouses/{wh.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_supplier_import_page(authenticated_client):
    """供应商导入页面"""
    resp = authenticated_client.get('/partner/suppliers/import')
    assert resp.status_code == 200


def test_customer_import_page(authenticated_client):
    """客户导入页面"""
    resp = authenticated_client.get('/partner/customers/import')
    assert resp.status_code == 200


# ==================== Purchase 路由测试 ====================

def test_purchase_index(authenticated_client):
    """采购首页"""
    resp = authenticated_client.get('/purchase/')
    assert resp.status_code == 200


def test_purchase_order_create(authenticated_client, app, db_session):
    """创建采购订单"""
    sup = create_supplier()
    wh = create_warehouse()
    prod = create_product()

    resp = authenticated_client.post('/purchase/orders/new', data={
        'supplier_id': str(sup.id),
        'warehouse_id': str(wh.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '测试',
        'product_id[]': [str(prod.id)],
        'quantity[]': ['10'],
        'unit_price[]': ['50'],
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_purchase_order_edit(authenticated_client, app, db_session):
    """编辑采购订单"""
    sup = create_supplier()
    wh = create_warehouse()
    prod = create_product()
    order = create_purchase_order(
        supplier_id=sup.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 50}],
        status='confirmed'
    )

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/edit', data={
        'supplier_id': str(sup.id),
        'warehouse_id': str(wh.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '修改',
        'product_id[]': [str(prod.id)],
        'quantity[]': ['20'],
        'unit_price[]': ['60'],
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_purchase_order_delete(authenticated_client, app, db_session):
    """删除采购订单"""
    sup = create_supplier()
    wh = create_warehouse()
    order = create_purchase_order(
        supplier_id=sup.id,
        warehouse_id=wh.id,
        items=[],
        status='draft'
    )

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_purchase_order_detail(authenticated_client, app, db_session):
    """采购订单详情"""
    sup = create_supplier()
    wh = create_warehouse()
    order = create_purchase_order(
        supplier_id=sup.id,
        warehouse_id=wh.id,
        items=[],
        status='confirmed'
    )

    resp = authenticated_client.get(f'/purchase/orders/{order.id}')
    assert resp.status_code == 200


def test_purchase_quick_stock_in(authenticated_client, app, db_session):
    """快捷入库"""
    sup = create_supplier()
    wh = create_warehouse()
    prod = create_product(stock_quantity=0)
    order = create_purchase_order(
        supplier_id=sup.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 50}],
        status='confirmed'
    )

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/quick-stock-in', follow_redirects=True)
    assert resp.status_code == 200


def test_purchase_quick_return(authenticated_client, app, db_session):
    """快捷退货"""
    sup = create_supplier()
    wh = create_warehouse()
    prod = create_product(stock_quantity=50)
    order = create_purchase_order(
        supplier_id=sup.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 50}],
        status='completed'
    )
    order.items[0].received_quantity = Decimal('10')
    db.session.commit()

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/quick-return', follow_redirects=True)
    assert resp.status_code == 200


def test_purchase_returns_list(authenticated_client):
    """采购退货列表"""
    resp = authenticated_client.get('/purchase/returns')
    assert resp.status_code == 200


def test_purchase_stock_in_new(authenticated_client):
    """新建入库单"""
    resp = authenticated_client.get('/purchase/stock-ins/new')
    assert resp.status_code == 200


# ==================== Sales 路由测试 ====================

def test_sales_index(authenticated_client):
    """销售首页"""
    resp = authenticated_client.get('/sales/')
    assert resp.status_code == 200


def test_sales_order_create(authenticated_client, app, db_session):
    """创建销售订单"""
    cus = create_customer()
    wh = create_warehouse()
    prod = create_product(stock_quantity=100)

    resp = authenticated_client.post('/sales/orders/new', data={
        'customer_id': str(cus.id),
        'warehouse_id': str(wh.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '测试',
        'product_id[]': [str(prod.id)],
        'quantity[]': ['10'],
        'unit_price[]': ['100'],
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_sales_order_edit(authenticated_client, app, db_session):
    """编辑销售订单"""
    cus = create_customer()
    wh = create_warehouse()
    prod = create_product(stock_quantity=100)
    order = create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
        status='confirmed'
    )

    resp = authenticated_client.post(f'/sales/orders/{order.id}/edit', data={
        'customer_id': str(cus.id),
        'warehouse_id': str(wh.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '修改',
        'product_id[]': [str(prod.id)],
        'quantity[]': ['5'],
        'unit_price[]': ['120'],
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_sales_order_delete(authenticated_client, app, db_session):
    """删除销售订单"""
    cus = create_customer()
    wh = create_warehouse()
    order = create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[],
        status='draft'
    )

    resp = authenticated_client.post(f'/sales/orders/{order.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_sales_order_detail(authenticated_client, app, db_session):
    """销售订单详情"""
    cus = create_customer()
    wh = create_warehouse()
    order = create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[],
        status='confirmed'
    )

    resp = authenticated_client.get(f'/sales/orders/{order.id}')
    assert resp.status_code == 200


def test_sales_quick_stock_out(authenticated_client, app, db_session):
    """快捷出库"""
    cus = create_customer()
    wh = create_warehouse()
    prod = create_product(stock_quantity=100)
    order = create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
        status='confirmed'
    )

    resp = authenticated_client.post(f'/sales/orders/{order.id}/quick-stock-out', follow_redirects=True)
    assert resp.status_code == 200


def test_sales_quick_return(authenticated_client, app, db_session):
    """快捷退货"""
    cus = create_customer()
    wh = create_warehouse()
    prod = create_product(stock_quantity=50)
    order = create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
        status='completed'
    )
    order.items[0].delivered_quantity = Decimal('10')
    db.session.commit()

    resp = authenticated_client.post(f'/sales/orders/{order.id}/quick-return', follow_redirects=True)
    assert resp.status_code == 200


def test_sales_returns_list(authenticated_client):
    """销售退货列表"""
    resp = authenticated_client.get('/sales/returns')
    assert resp.status_code == 200


def test_sales_stock_out_new(authenticated_client):
    """新建出库单"""
    resp = authenticated_client.get('/sales/stock-outs/new')
    assert resp.status_code == 200


# ==================== Inventory 路由测试 ====================

def test_inventory_index(authenticated_client):
    """库存首页"""
    resp = authenticated_client.get('/inventory/')
    assert resp.status_code == 200


def test_inventory_product_list(authenticated_client):
    """商品库存列表"""
    resp = authenticated_client.get('/inventory/products')
    assert resp.status_code == 200


def test_inventory_warehouse_stock(authenticated_client, app, db_session):
    """仓库库存"""
    wh = create_warehouse()
    resp = authenticated_client.get(f'/inventory/warehouse/{wh.id}')
    assert resp.status_code == 200


def test_inventory_stock_check(authenticated_client):
    """库存盘点"""
    resp = authenticated_client.get('/inventory/stock-check')
    assert resp.status_code == 200


def test_inventory_stock_transfer(authenticated_client):
    """库存调拨"""
    resp = authenticated_client.get('/inventory/stock-transfer')
    assert resp.status_code == 200


def test_inventory_stock_adjust(authenticated_client):
    """库存调整"""
    resp = authenticated_client.get('/inventory/stock-adjust')
    assert resp.status_code == 200


def test_inventory_logs(authenticated_client):
    """库存日志"""
    resp = authenticated_client.get('/inventory/logs')
    assert resp.status_code == 200


def test_inventory_low_stock_api(authenticated_client):
    """低库存 API"""
    resp = authenticated_client.get('/inventory/api/low-stock')
    assert resp.status_code == 200


# ==================== Finance 路由测试 ====================

def test_finance_index(authenticated_client):
    """财务首页"""
    resp = authenticated_client.get('/finance/')
    assert resp.status_code == 200


def test_receipts_list(authenticated_client):
    """收款列表"""
    resp = authenticated_client.get('/finance/receipts')
    assert resp.status_code == 200


def test_payments_list(authenticated_client):
    """付款列表"""
    resp = authenticated_client.get('/finance/payments')
    assert resp.status_code == 200


def test_expenses_list(authenticated_client):
    """费用列表"""
    resp = authenticated_client.get('/finance/expenses')
    assert resp.status_code == 200


def test_profit_analysis(authenticated_client):
    """利润分析"""
    resp = authenticated_client.get('/finance/profit-analysis')
    assert resp.status_code == 200


def test_ar_ap_search(authenticated_client):
    """应收应付查询"""
    resp = authenticated_client.get('/finance/ar-ap-search')
    assert resp.status_code == 200


def test_receipt_add(authenticated_client, app, db_session):
    """添加收款"""
    cus = create_customer()
    resp = authenticated_client.post('/finance/receipt/add', data={
        'customer_id': str(cus.id),
        'amount': '1000',
        'payment_method': 'cash',
        'receipt_date': date.today().strftime('%Y-%m-%d'),
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_payment_add(authenticated_client, app, db_session):
    """添加付款"""
    sup = create_supplier()
    resp = authenticated_client.post('/finance/payment/add', data={
        'supplier_id': str(sup.id),
        'amount': '500',
        'payment_method': 'bank_transfer',
        'payment_date': date.today().strftime('%Y-%m-%d'),
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_expense_add(authenticated_client):
    """添加费用"""
    resp = authenticated_client.post('/finance/expense/add', data={
        'category': '办公费',
        'amount': '100',
        'expense_date': date.today().strftime('%Y-%m-%d'),
    }, follow_redirects=True)
    assert resp.status_code == 200


# ==================== Report 路由测试 ====================

def test_report_index(authenticated_client):
    """报表首页"""
    resp = authenticated_client.get('/report/')
    assert resp.status_code == 200


def test_inventory_report(authenticated_client):
    """进销存报表"""
    resp = authenticated_client.get('/report/inventory-report')
    assert resp.status_code == 200


def test_sales_ranking(authenticated_client):
    """销售排行"""
    resp = authenticated_client.get('/report/sales-ranking')
    assert resp.status_code == 200


def test_customer_statistics(authenticated_client):
    """客户统计"""
    resp = authenticated_client.get('/report/customer-statistics')
    assert resp.status_code == 200


def test_supplier_statistics(authenticated_client):
    """供应商统计"""
    resp = authenticated_client.get('/report/supplier-statistics')
    assert resp.status_code == 200


def test_daily_report(authenticated_client):
    """日报"""
    resp = authenticated_client.get('/report/daily-report')
    assert resp.status_code == 200


# ==================== System 路由测试 ====================

def test_system_index(authenticated_client):
    """系统首页"""
    resp = authenticated_client.get('/system/')
    assert resp.status_code == 200


def test_users_list(authenticated_client):
    """用户列表"""
    resp = authenticated_client.get('/system/users')
    assert resp.status_code == 200


def test_settings_page(authenticated_client):
    """系统设置"""
    resp = authenticated_client.get('/system/settings')
    assert resp.status_code == 200


def test_backup_page(authenticated_client):
    """备份页面"""
    resp = authenticated_client.get('/system/backup')
    assert resp.status_code == 200


def test_logs_page(authenticated_client):
    """系统日志"""
    resp = authenticated_client.get('/system/logs')
    assert resp.status_code == 200


def test_system_info_api(authenticated_client):
    """系统信息 API"""
    resp = authenticated_client.get('/system/api/system-info')
    assert resp.status_code == 200


def test_user_edit(authenticated_client, app, db_session):
    """编辑用户"""
    user = User(username='edit_user', email='edit@test.com')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = authenticated_client.get(f'/system/user/edit/{user.id}')
    assert resp.status_code == 200


def test_non_admin_access(client, app, db_session):
    """非管理员访问系统管理"""
    user = User(username='normal_int', email='normal_int@test.com', role='user')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    client.post('/auth/login', data={'username': 'normal_int', 'password': 'pass123'})
    resp = client.get('/system/users')
    assert resp.status_code == 403


# ==================== Main 路由测试 ====================

def test_dashboard(authenticated_client):
    """仪表板"""
    resp = authenticated_client.get('/')
    assert resp.status_code == 200


def test_sales_trend_api(authenticated_client):
    """销售趋势 API"""
    resp = authenticated_client.get('/api/sales-trend')
    assert resp.status_code == 200


def test_stock_overview_api(authenticated_client):
    """库存概览 API"""
    resp = authenticated_client.get('/api/stock-overview')
    assert resp.status_code == 200


def test_finance_summary_api(authenticated_client):
    """财务汇总 API"""
    resp = authenticated_client.get('/api/finance-summary')
    assert resp.status_code == 200
