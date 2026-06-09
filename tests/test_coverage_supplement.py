"""
补充测试 — 覆盖未测试的代码路径
"""
from app import db
from app.models import User, Product, Category, Supplier, Customer, Warehouse


# ==================== Auth 补充测试 ====================

def test_change_password_too_short(authenticated_client):
    """密码长度不足6位"""
    resp = authenticated_client.post('/auth/change-password', data={
        'old_password': 'admin123',
        'new_password': '12345',
        'confirm_password': '12345',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_change_password_too_long(authenticated_client):
    """密码长度超过128位"""
    long_password = 'a' * 129
    resp = authenticated_client.post('/auth/change-password', data={
        'old_password': 'admin123',
        'new_password': long_password,
        'confirm_password': long_password,
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_change_password_mismatch(authenticated_client):
    """两次输入密码不一致"""
    resp = authenticated_client.post('/auth/change-password', data={
        'old_password': 'admin123',
        'new_password': 'newpass123',
        'confirm_password': 'different123',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_change_email_empty(authenticated_client):
    """空邮箱"""
    resp = authenticated_client.post('/auth/change-email', data={
        'new_email': '',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_register_password_mismatch(client):
    """注册时密码不一致"""
    resp = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'new@test.com',
        'password': 'pass123',
        'password2': 'different',
    }, follow_redirects=True)
    assert resp.status_code == 200


# ==================== System 补充测试 ====================

def test_delete_user_not_found(authenticated_client):
    """删除不存在的用户"""
    resp = authenticated_client.post('/system/user/delete/99999', follow_redirects=True)
    assert resp.status_code == 404


def test_edit_user_not_found(authenticated_client):
    """编辑不存在的用户"""
    resp = authenticated_client.get('/system/user/edit/99999', follow_redirects=True)
    # 可能返回 404 或重定向
    assert resp.status_code in (200, 404)


def test_backup_download_invalid_filename(authenticated_client):
    """下载备份 — 无效文件名"""
    resp = authenticated_client.get('/system/backup/download/....//etc/passwd', follow_redirects=True)
    # 可能返回 404 或重定向
    assert resp.status_code in (200, 404)


def test_backup_download_not_found(authenticated_client):
    """下载备份 — 文件不存在"""
    resp = authenticated_client.get('/system/backup/download/nonexistent.db', follow_redirects=True)
    assert resp.status_code == 200


def test_restore_backup_no_file(authenticated_client):
    """恢复备份 — 未选择文件"""
    resp = authenticated_client.post('/system/backup/restore', data={}, follow_redirects=True)
    assert resp.status_code == 200


def test_restore_backup_invalid_filename(authenticated_client):
    """恢复备份 — 无效文件名"""
    resp = authenticated_client.post('/system/backup/restore', data={
        'filename': '....//etc/passwd'
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_settings_page(authenticated_client):
    """系统设置页面"""
    resp = authenticated_client.get('/system/settings')
    assert resp.status_code == 200


def test_non_admin_cannot_access_system(app, db_session):
    """非管理员不能访问系统管理"""
    import time
    # 创建普通用户
    user = User(username=f'normaluser_{int(time.time())}', email='normal@test.com', role='user')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    # 用普通用户登录
    client = app.test_client()
    client.post('/auth/login', data={'username': user.username, 'password': 'pass123'})

    resp = client.get('/system/users')
    assert resp.status_code == 403


# ==================== Product 补充测试 ====================

def test_add_category(authenticated_client):
    """添加商品分类"""
    resp = authenticated_client.post('/product/categories/new', data={
        'name': '新分类',
        'description': '测试分类',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_edit_category(authenticated_client, app, db_session):
    """编辑商品分类"""
    cat = Category(name='待编辑分类')
    db.session.add(cat)
    db.session.commit()

    resp = authenticated_client.post(f'/product/categories/{cat.id}/edit', data={
        'name': '已编辑分类',
        'description': '已编辑',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_delete_category(authenticated_client, app, db_session):
    """删除商品分类"""
    cat = Category(name='待删除分类')
    db.session.add(cat)
    db.session.commit()

    resp = authenticated_client.post(f'/product/categories/{cat.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_add_product(authenticated_client, app, db_session):
    """添加商品"""
    cat = Category(name='测试分类')
    db.session.add(cat)
    db.session.commit()

    resp = authenticated_client.post('/product/products/new', data={
        'code': 'NEW_PROD_001',
        'name': '新商品',
        'category_id': str(cat.id),
        'unit': '个',
        'purchase_price': '50.00',
        'sale_price': '100.00',
        'safety_stock': '10',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_edit_product(authenticated_client, app, db_session):
    """编辑商品"""
    cat = Category(name='编辑分类')
    db.session.add(cat)
    db.session.flush()

    prod = Product(code='EDIT_PROD', name='待编辑', category_id=cat.id, unit='个',
                   purchase_price=50, sale_price=100)
    db.session.add(prod)
    db.session.commit()

    resp = authenticated_client.post(f'/product/products/{prod.id}/edit', data={
        'code': 'EDIT_PROD',
        'name': '已编辑商品',
        'category_id': str(cat.id),
        'unit': '个',
        'purchase_price': '60.00',
        'sale_price': '120.00',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_delete_product(authenticated_client, app, db_session):
    """删除商品"""
    prod = Product(code='DEL_PROD', name='待删除', unit='个', purchase_price=50, sale_price=100)
    db.session.add(prod)
    db.session.commit()

    resp = authenticated_client.post(f'/product/products/{prod.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_product_search_api(authenticated_client, app, db_session):
    """商品搜索API"""
    resp = authenticated_client.get('/product/api/products?limit=10')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_product_price_update(authenticated_client, app, db_session):
    """更新商品价格"""
    prod = Product(code='PRICE_PROD', name='价格测试', unit='个', purchase_price=50, sale_price=100)
    db.session.add(prod)
    db.session.commit()

    resp = authenticated_client.post('/product/api/product/price', json={
        'product_id': prod.id,
        'price_type': 'sale_price',
        'price': 150,
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success']


# ==================== Partner 补充测试 ====================

def test_add_supplier(authenticated_client):
    """添加供应商"""
    resp = authenticated_client.post('/partner/suppliers/new', data={
        'code': 'NEW_SUP_001',
        'name': '新供应商',
        'contact_person': '张三',
        'phone': '13800000001',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_edit_supplier(authenticated_client, app, db_session):
    """编辑供应商"""
    sup = Supplier(code='EDIT_SUP', name='待编辑', contact_person='张三', phone='13800000001')
    db.session.add(sup)
    db.session.commit()

    resp = authenticated_client.post(f'/partner/suppliers/{sup.id}/edit', data={
        'code': 'EDIT_SUP',
        'name': '已编辑供应商',
        'contact_person': '李四',
        'phone': '13900000001',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_delete_supplier(authenticated_client, app, db_session):
    """删除供应商"""
    sup = Supplier(code='DEL_SUP', name='待删除', contact_person='张三', phone='13800000001')
    db.session.add(sup)
    db.session.commit()

    resp = authenticated_client.post(f'/partner/suppliers/{sup.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_add_customer(authenticated_client):
    """添加客户"""
    resp = authenticated_client.post('/partner/customers/new', data={
        'code': 'NEW_CUS_001',
        'name': '新客户',
        'contact_person': '李四',
        'phone': '13900000001',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_edit_customer(authenticated_client, app, db_session):
    """编辑客户"""
    cus = Customer(code='EDIT_CUS', name='待编辑', contact_person='李四', phone='13900000001')
    db.session.add(cus)
    db.session.commit()

    resp = authenticated_client.post(f'/partner/customers/{cus.id}/edit', data={
        'code': 'EDIT_CUS',
        'name': '已编辑客户',
        'contact_person': '王五',
        'phone': '13700000001',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_delete_customer(authenticated_client, app, db_session):
    """删除客户"""
    cus = Customer(code='DEL_CUS', name='待删除', contact_person='李四', phone='13900000001')
    db.session.add(cus)
    db.session.commit()

    resp = authenticated_client.post(f'/partner/customers/{cus.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_add_warehouse(authenticated_client):
    """添加仓库"""
    resp = authenticated_client.post('/partner/warehouses/new', data={
        'code': 'NEW_WH_001',
        'name': '新仓库',
        'address': '测试地址',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_edit_warehouse(authenticated_client, app, db_session):
    """编辑仓库"""
    wh = Warehouse(code='EDIT_WH', name='待编辑', address='测试地址')
    db.session.add(wh)
    db.session.commit()

    resp = authenticated_client.post(f'/partner/warehouses/{wh.id}/edit', data={
        'code': 'EDIT_WH',
        'name': '已编辑仓库',
        'address': '新地址',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_delete_warehouse(authenticated_client, app, db_session):
    """删除仓库"""
    wh = Warehouse(code='DEL_WH', name='待删除', address='测试地址')
    db.session.add(wh)
    db.session.commit()

    resp = authenticated_client.post(f'/partner/warehouses/{wh.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_suppliers_list(authenticated_client):
    """供应商列表"""
    resp = authenticated_client.get('/partner/suppliers')
    assert resp.status_code == 200


def test_customers_list(authenticated_client):
    """客户列表"""
    resp = authenticated_client.get('/partner/customers')
    assert resp.status_code == 200


def test_warehouses_list(authenticated_client):
    """仓库列表"""
    resp = authenticated_client.get('/partner/warehouses')
    assert resp.status_code == 200
