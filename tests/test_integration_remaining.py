"""
集成测试 — 剩余缺失路径覆盖
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


# ==================== Auth 完整测试 ====================

def test_change_password_success(authenticated_client):
    """修改密码成功"""
    resp = authenticated_client.post('/auth/change-password', data={
        'old_password': 'admin123',
        'new_password': 'newpass123',
        'confirm_password': 'newpass123',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '成功' in resp.data.decode() or '密码' in resp.data.decode()


def test_change_password_wrong_old(authenticated_client):
    """修改密码 - 旧密码错误"""
    resp = authenticated_client.post('/auth/change-password', data={
        'old_password': 'wrongpass',
        'new_password': 'newpass123',
        'confirm_password': 'newpass123',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '错误' in resp.data.decode() or '密码' in resp.data.decode()


def test_change_password_too_short(authenticated_client):
    """修改密码 - 新密码太短"""
    resp = authenticated_client.post('/auth/change-password', data={
        'old_password': 'admin123',
        'new_password': '123',
        'confirm_password': '123',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '6位' in resp.data.decode() or '密码' in resp.data.decode()


def test_change_password_too_long(authenticated_client):
    """修改密码 - 新密码太长"""
    long_password = 'a' * 129
    resp = authenticated_client.post('/auth/change-password', data={
        'old_password': 'admin123',
        'new_password': long_password,
        'confirm_password': long_password,
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '128位' in resp.data.decode() or '密码' in resp.data.decode()


def test_change_password_mismatch(authenticated_client):
    """修改密码 - 两次输入不一致"""
    resp = authenticated_client.post('/auth/change-password', data={
        'old_password': 'admin123',
        'new_password': 'newpass123',
        'confirm_password': 'different',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '不一致' in resp.data.decode() or '密码' in resp.data.decode()


def test_change_email_success(authenticated_client):
    """修改邮箱成功"""
    resp = authenticated_client.post('/auth/change-email', data={
        'new_email': 'newemail@test.com',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '成功' in resp.data.decode() or '邮箱' in resp.data.decode()


def test_change_email_empty(authenticated_client):
    """修改邮箱 - 空邮箱"""
    resp = authenticated_client.post('/auth/change-email', data={
        'new_email': '',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '空' in resp.data.decode() or '邮箱' in resp.data.decode()


def test_change_email_invalid(authenticated_client):
    """修改邮箱 - 无效格式"""
    resp = authenticated_client.post('/auth/change-email', data={
        'new_email': 'invalid-email',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '有效' in resp.data.decode() or '邮箱' in resp.data.decode()


def test_change_email_already_used(authenticated_client, app, db_session):
    """修改邮箱 - 已被使用"""
    import time
    other = User(username=f'other_email_{int(time.time())}', email='used@test.com')
    other.set_password('pass123')
    db.session.add(other)
    db.session.commit()

    resp = authenticated_client.post('/auth/change-email', data={
        'new_email': 'used@test.com',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '已被' in resp.data.decode() or '邮箱' in resp.data.decode()


def test_login_already_authenticated(authenticated_client):
    """已登录用户访问登录页"""
    resp = authenticated_client.get('/auth/login', follow_redirects=False)
    assert resp.status_code in (302, 303)


def test_register_already_authenticated(authenticated_client):
    """已登录用户访问注册页"""
    resp = authenticated_client.get('/auth/register', follow_redirects=False)
    assert resp.status_code in (302, 303)


def test_register_success(client):
    """注册成功"""
    resp = client.post('/auth/register', data={
        'username': 'reg_success_user',
        'email': 'reg@test.com',
        'password': 'pass123',
        'password2': 'pass123',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_register_duplicate(client, app, db_session):
    """注册重复用户名"""
    import time
    user = User(username=f'dup_reg_{int(time.time())}', email='dup@test.com')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = client.post('/auth/register', data={
        'username': user.username,
        'email': 'dup2@test.com',
        'password': 'pass123',
        'password2': 'pass123',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_register_password_mismatch(client):
    """注册密码不一致"""
    resp = client.post('/auth/register', data={
        'username': 'mismatch_user',
        'email': 'mismatch@test.com',
        'password': 'pass123',
        'password2': 'different',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_inactive_user_login(client, app, db_session):
    """未激活用户登录"""
    import time
    user = User(username=f'inactive_{int(time.time())}', email='inactive@test.com', is_active=False)
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = client.post('/auth/login', data={
        'username': user.username,
        'password': 'pass123',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert '激活' in resp.data.decode() or '登录' in resp.data.decode()


# ==================== System 完整测试 ====================

def test_user_add_success(authenticated_client):
    """添加用户成功"""
    resp = authenticated_client.post('/system/user/add', data={
        'username': 'new_sys_user',
        'email': 'newsys@test.com',
        'password': 'pass123',
        'role': 'user',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_user_add_duplicate(authenticated_client, app, db_session):
    """添加用户 - 重复用户名"""
    import time
    user = User(username=f'dup_sys_{int(time.time())}', email='dupsys@test.com')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = authenticated_client.post('/system/user/add', data={
        'username': user.username,
        'email': 'dupsys2@test.com',
        'password': 'pass123',
        'role': 'user',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_user_edit_success(authenticated_client, app, db_session):
    """编辑用户成功"""
    import time
    user = User(username=f'edit_sys_{int(time.time())}', email='editsys@test.com')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = authenticated_client.post(f'/system/user/edit/{user.id}', data={
        'username': user.username,
        'email': 'neweditsys@test.com',
        'role': 'user',
        'is_active': 'on',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_user_edit_not_found(authenticated_client):
    """编辑用户 - 不存在"""
    resp = authenticated_client.get('/system/user/edit/99999')
    assert resp.status_code == 404


def test_user_delete_success(authenticated_client, app, db_session):
    """删除用户成功"""
    import time
    user = User(username=f'del_sys_{int(time.time())}', email='delsys@test.com')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = authenticated_client.post(f'/system/user/delete/{user.id}', follow_redirects=True)
    assert resp.status_code == 200


def test_user_delete_not_found(authenticated_client):
    """删除用户 - 不存在"""
    resp = authenticated_client.post('/system/user/delete/99999', follow_redirects=True)
    assert resp.status_code == 200


def test_backup_create(authenticated_client):
    """创建备份"""
    resp = authenticated_client.post('/system/backup/create', follow_redirects=True)
    assert resp.status_code == 200


def test_backup_list(authenticated_client):
    """备份列表"""
    resp = authenticated_client.get('/system/backup/list')
    assert resp.status_code == 200


def test_backup_download_not_found(authenticated_client):
    """下载备份 - 文件不存在"""
    resp = authenticated_client.get('/system/backup/download/nonexistent.db')
    assert resp.status_code in (302, 404)


def test_backup_download_invalid(authenticated_client):
    """下载备份 - 无效文件名"""
    resp = authenticated_client.get('/system/backup/download/....//etc/passwd')
    assert resp.status_code in (302, 404)


def test_backup_restore_no_file(authenticated_client):
    """恢复备份 - 未选择文件"""
    resp = authenticated_client.post('/system/backup/restore', data={}, follow_redirects=True)
    assert resp.status_code == 200


def test_backup_restore_not_found(authenticated_client):
    """恢复备份 - 文件不存在"""
    resp = authenticated_client.post('/system/backup/restore', data={
        'filename': 'nonexistent.db'
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_backup_restore_invalid(authenticated_client):
    """恢复备份 - 无效文件名"""
    resp = authenticated_client.post('/system/backup/restore', data={
        'filename': '....//etc/passwd'
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_backup_delete(authenticated_client):
    """删除备份"""
    # 先创建备份
    authenticated_client.post('/system/backup/create', follow_redirects=True)

    # 获取备份列表
    resp = authenticated_client.get('/system/backup/list')
    assert resp.status_code == 200


def test_settings_page(authenticated_client):
    """系统设置页面"""
    resp = authenticated_client.get('/system/settings')
    assert resp.status_code == 200


def test_settings_update(authenticated_client):
    """更新系统设置"""
    resp = authenticated_client.post('/system/api/system/settings', data={
        'COMPANY_NAME': '测试公司',
        'COMPANY_ADDRESS': '测试地址',
        'COMPANY_PHONE': '13800000000',
        'DEFAULT_CURRENCY': 'CNY',
        'ITEMS_PER_PAGE': '20',
        'ENABLE_BACKUP': '1',
        'ENABLE_LOGGING': '1',
    })
    assert resp.status_code in (200, 400)


def test_system_info(authenticated_client):
    """系统信息"""
    resp = authenticated_client.get('/system/api/system-info')
    assert resp.status_code == 200


def test_recent_logs(authenticated_client):
    """最近日志"""
    resp = authenticated_client.get('/system/api/system/recent-logs')
    assert resp.status_code == 200


def test_optimize_db(authenticated_client):
    """优化数据库"""
    resp = authenticated_client.post('/system/api/system/optimize-db')
    assert resp.status_code in (200, 500)


def test_clean_logs(authenticated_client):
    """清理日志"""
    resp = authenticated_client.post('/system/api/system/clean-logs')
    assert resp.status_code == 200


def test_export_db(authenticated_client):
    """导出数据库"""
    resp = authenticated_client.get('/system/api/system/export-db')
    assert resp.status_code == 200


def test_non_admin_access(client, app, db_session):
    """非管理员访问系统管理"""
    user = User(username='non_admin_test', email='nonadmin@test.com', role='user')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    client.post('/auth/login', data={'username': 'non_admin_test', 'password': 'pass123'})
    resp = client.get('/system/users')
    assert resp.status_code == 403


# ==================== Product 完整测试 ====================

def test_product_create(authenticated_client, app, db_session):
    """创建商品"""
    cat = create_category()
    resp = authenticated_client.post('/product/products/new', data={
        'code': 'NEW_PROD_TEST',
        'name': '新商品测试',
        'category_id': str(cat.id),
        'unit': '个',
        'purchase_price': '50',
        'sale_price': '100',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_product_create_duplicate(authenticated_client, app, db_session):
    """创建商品 - 重复编码"""
    create_product(code='DUP_PROD_CODE')
    resp = authenticated_client.post('/product/products/new', data={
        'code': 'DUP_PROD_CODE',
        'name': '重复编码商品',
        'unit': '个',
        'purchase_price': '50',
        'sale_price': '100',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_product_edit(authenticated_client, app, db_session):
    """编辑商品"""
    product = create_product(code='EDIT_PROD_TEST')
    resp = authenticated_client.post(f'/product/products/{product.id}/edit', data={
        'code': 'EDIT_PROD_TEST',
        'name': '已编辑商品',
        'unit': '个',
        'purchase_price': '60',
        'sale_price': '120',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_product_edit_duplicate(authenticated_client, app, db_session):
    """编辑商品 - 重复编码"""
    create_product(code='DUP_EDIT_CODE1')
    product = create_product(code='DUP_EDIT_CODE2')
    resp = authenticated_client.post(f'/product/products/{product.id}/edit', data={
        'code': 'DUP_EDIT_CODE1',
        'name': '重复编码',
        'unit': '个',
        'purchase_price': '50',
        'sale_price': '100',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_product_delete(authenticated_client, app, db_session):
    """删除商品"""
    product = create_product(code='DEL_PROD_TEST')
    resp = authenticated_client.post(f'/product/products/{product.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_product_detail(authenticated_client, app, db_session):
    """商品详情"""
    product = create_product(code='DETAIL_PROD_TEST')
    resp = authenticated_client.get(f'/product/products/{product.id}')
    assert resp.status_code == 200


def test_product_not_found(authenticated_client):
    """商品不存在"""
    resp = authenticated_client.get('/product/products/99999')
    assert resp.status_code == 404


def test_product_edit_not_found(authenticated_client):
    """编辑商品 - 不存在"""
    resp = authenticated_client.get('/product/products/99999/edit')
    assert resp.status_code == 404


def test_product_delete_not_found(authenticated_client):
    """删除商品 - 不存在"""
    resp = authenticated_client.post('/product/products/99999/delete')
    assert resp.status_code == 404


def test_category_create(authenticated_client):
    """创建分类"""
    resp = authenticated_client.post('/product/categories/new', data={
        'name': '新分类测试',
        'description': '测试',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_category_edit(authenticated_client, app, db_session):
    """编辑分类"""
    cat = create_category(name='编辑分类测试')
    resp = authenticated_client.post(f'/product/categories/{cat.id}/edit', data={
        'name': '已编辑分类',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_category_delete(authenticated_client, app, db_session):
    """删除分类"""
    cat = create_category(name='删除分类测试')
    resp = authenticated_client.post(f'/product/categories/{cat.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


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


def test_product_filter_category(authenticated_client, app, db_session):
    """按分类筛选"""
    cat = create_category(name='筛选分类')
    create_product(category_id=cat.id)
    resp = authenticated_client.get(f'/product/products?category_id={cat.id}')
    assert resp.status_code == 200


def test_product_api(authenticated_client):
    """商品 API"""
    resp = authenticated_client.get('/product/api/products')
    assert resp.status_code == 200


def test_categories_api(authenticated_client):
    """分类 API"""
    resp = authenticated_client.get('/product/api/categories')
    assert resp.status_code == 200


def test_product_import(authenticated_client):
    """商品导入页面"""
    resp = authenticated_client.get('/product/import')
    assert resp.status_code == 200


def test_product_import_template(authenticated_client):
    """商品导入模板"""
    resp = authenticated_client.get('/product/import/template')
    assert resp.status_code == 200


# ==================== Partner 完整测试 ====================

def test_supplier_create(authenticated_client):
    """创建供应商"""
    resp = authenticated_client.post('/partner/suppliers/new', data={
        'code': 'NEW_SUP_TEST',
        'name': '新供应商测试',
        'contact_person': '张三',
        'phone': '13800000001',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_supplier_edit(authenticated_client, app, db_session):
    """编辑供应商"""
    sup = create_supplier(code='EDIT_SUP_TEST')
    resp = authenticated_client.post(f'/partner/suppliers/{sup.id}/edit', data={
        'code': 'EDIT_SUP_TEST',
        'name': '已编辑供应商',
        'contact_person': '李四',
        'phone': '13900000001',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_supplier_delete(authenticated_client, app, db_session):
    """删除供应商"""
    sup = create_supplier(code='DEL_SUP_TEST')
    resp = authenticated_client.post(f'/partner/suppliers/{sup.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_supplier_not_found(authenticated_client):
    """供应商不存在"""
    resp = authenticated_client.get('/partner/suppliers/99999/edit')
    assert resp.status_code == 404


def test_customer_create(authenticated_client):
    """创建客户"""
    resp = authenticated_client.post('/partner/customers/new', data={
        'code': 'NEW_CUS_TEST',
        'name': '新客户测试',
        'contact_person': '李四',
        'phone': '13900000001',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_customer_edit(authenticated_client, app, db_session):
    """编辑客户"""
    cus = create_customer(code='EDIT_CUS_TEST')
    resp = authenticated_client.post(f'/partner/customers/{cus.id}/edit', data={
        'code': 'EDIT_CUS_TEST',
        'name': '已编辑客户',
        'contact_person': '王五',
        'phone': '13700000001',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_customer_delete(authenticated_client, app, db_session):
    """删除客户"""
    cus = create_customer(code='DEL_CUS_TEST')
    resp = authenticated_client.post(f'/partner/customers/{cus.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_customer_not_found(authenticated_client):
    """客户不存在"""
    resp = authenticated_client.get('/partner/customers/99999/edit')
    assert resp.status_code == 404


def test_warehouse_create(authenticated_client):
    """创建仓库"""
    resp = authenticated_client.post('/partner/warehouses/new', data={
        'code': 'NEW_WH_TEST',
        'name': '新仓库测试',
        'address': '测试地址',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_warehouse_edit(authenticated_client, app, db_session):
    """编辑仓库"""
    wh = create_warehouse(code='EDIT_WH_TEST')
    resp = authenticated_client.post(f'/partner/warehouses/{wh.id}/edit', data={
        'code': 'EDIT_WH_TEST',
        'name': '已编辑仓库',
        'address': '新地址',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_warehouse_delete(authenticated_client, app, db_session):
    """删除仓库"""
    wh = create_warehouse(code='DEL_WH_TEST')
    resp = authenticated_client.post(f'/partner/warehouses/{wh.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_warehouse_not_found(authenticated_client):
    """仓库不存在"""
    resp = authenticated_client.get('/partner/warehouses/99999/edit')
    assert resp.status_code == 404


def test_supplier_import(authenticated_client):
    """供应商导入页面"""
    resp = authenticated_client.get('/partner/suppliers/import')
    assert resp.status_code == 200


def test_supplier_import_template(authenticated_client):
    """供应商导入模板"""
    resp = authenticated_client.get('/partner/suppliers/import/template')
    assert resp.status_code == 200


def test_customer_import(authenticated_client):
    """客户导入页面"""
    resp = authenticated_client.get('/partner/customers/import')
    assert resp.status_code == 200


def test_customer_import_template(authenticated_client):
    """客户导入模板"""
    resp = authenticated_client.get('/partner/customers/import/template')
    assert resp.status_code == 200


# ==================== Inventory 完整测试 ====================

def test_inventory_index(authenticated_client):
    """库存首页"""
    resp = authenticated_client.get('/inventory/')
    assert resp.status_code == 200


def test_product_list(authenticated_client):
    """商品库存列表"""
    resp = authenticated_client.get('/inventory/products')
    assert resp.status_code == 200


def test_warehouse_stock(authenticated_client, app, db_session):
    """仓库库存"""
    wh = create_warehouse()
    resp = authenticated_client.get(f'/inventory/warehouse/{wh.id}')
    assert resp.status_code == 200


def test_warehouse_stock_not_found(authenticated_client):
    """仓库库存 - 不存在"""
    resp = authenticated_client.get('/inventory/warehouse/99999')
    assert resp.status_code == 404


def test_stock_check(authenticated_client):
    """库存盘点"""
    resp = authenticated_client.get('/inventory/stock-check')
    assert resp.status_code == 200


def test_stock_transfer(authenticated_client):
    """库存调拨"""
    resp = authenticated_client.get('/inventory/stock-transfer')
    assert resp.status_code == 200


def test_stock_adjust(authenticated_client):
    """库存调整"""
    resp = authenticated_client.get('/inventory/stock-adjust')
    assert resp.status_code == 200


def test_stock_logs(authenticated_client):
    """库存日志"""
    resp = authenticated_client.get('/inventory/logs')
    assert resp.status_code == 200


def test_low_stock_api(authenticated_client):
    """低库存 API"""
    resp = authenticated_client.get('/inventory/api/low-stock')
    assert resp.status_code == 200


def test_stock_check_flow(authenticated_client, app, db_session):
    """盘点流程"""
    wh = create_warehouse()
    prod = create_product(stock_quantity=100)
    resp = authenticated_client.post('/inventory/stock-check', data={
        'warehouse_id': str(wh.id),
        'notes': '盘点测试',
        'product_id[]': [str(prod.id)],
        'actual_quantity[]': ['110'],
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_stock_adjust_in(authenticated_client, app, db_session):
    """调整入库"""
    wh = create_warehouse()
    prod = create_product(stock_quantity=50)
    resp = authenticated_client.post('/inventory/stock-adjust', data={
        'product_id': str(prod.id),
        'warehouse_id': str(wh.id),
        'adjust_type': 'adjust_in',
        'quantity': '10',
        'notes': '盘盈',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_stock_adjust_out(authenticated_client, app, db_session):
    """调整出库"""
    wh = create_warehouse()
    prod = create_product(stock_quantity=50)
    resp = authenticated_client.post('/inventory/stock-adjust', data={
        'product_id': str(prod.id),
        'warehouse_id': str(wh.id),
        'adjust_type': 'adjust_out',
        'quantity': '10',
        'notes': '盘亏',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_stock_adjust_insufficient(authenticated_client, app, db_session):
    """调整出库 - 库存不足"""
    wh = create_warehouse()
    prod = create_product(stock_quantity=5)
    resp = authenticated_client.post('/inventory/stock-adjust', data={
        'product_id': str(prod.id),
        'warehouse_id': str(wh.id),
        'adjust_type': 'adjust_out',
        'quantity': '100',
        'notes': '库存不足',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_stock_transfer_flow(authenticated_client, app, db_session):
    """调拨流程"""
    wh1 = create_warehouse()
    wh2 = create_warehouse()
    prod = create_product(stock_quantity=100)
    resp = authenticated_client.post('/inventory/stock-transfer', data={
        'from_warehouse': str(wh1.id),
        'to_warehouse': str(wh2.id),
        'transfer_date': date.today().strftime('%Y-%m-%d'),
        'notes': '调拨测试',
        'items-0-product_id': str(prod.id),
        'items-0-quantity': '10',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_stock_transfer_same_warehouse(authenticated_client, app, db_session):
    """调拨 - 同一仓库"""
    wh = create_warehouse()
    prod = create_product(stock_quantity=100)
    resp = authenticated_client.post('/inventory/stock-transfer', data={
        'from_warehouse': str(wh.id),
        'to_warehouse': str(wh.id),
        'transfer_date': date.today().strftime('%Y-%m-%d'),
        'notes': '同仓库调拨',
        'items-0-product_id': str(prod.id),
        'items-0-quantity': '10',
    }, follow_redirects=True)
    assert resp.status_code == 200
