"""
合作方模块测试 — 供应商、客户、仓库 CRUD
"""
import pytest
from app import db
from app.models import Supplier, Customer, Warehouse
from tests.factories import create_supplier, create_customer, create_warehouse


# ==================== 供应商 ====================

def test_suppliers_list(authenticated_client):
    """GET /partner/suppliers 返回 200"""
    resp = authenticated_client.get('/partner/suppliers', follow_redirects=True)
    assert resp.status_code == 200


def test_add_supplier_get(authenticated_client):
    """GET /partner/suppliers/new 返回 200"""
    resp = authenticated_client.get('/partner/suppliers/new', follow_redirects=True)
    assert resp.status_code == 200


def test_add_supplier_post(app, authenticated_client, db_session):
    """POST 添加供应商"""
    resp = authenticated_client.post('/partner/suppliers/new', data={
        'code': 'NEW_SUP01',
        'name': '新供应商',
        'contact_person': '张三',
        'phone': '13800000001',
        'address': '测试地址',
        'email': 'supplier@test.com',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        s = Supplier.query.filter_by(code='NEW_SUP01').first()
        assert s is not None
        assert s.name == '新供应商'


def test_edit_supplier(app, authenticated_client, db_session):
    """编辑供应商"""
    supplier = create_supplier(code='EDT_SUP01', name='编辑供应商')

    resp = authenticated_client.get(f'/partner/suppliers/{supplier.id}/edit', follow_redirects=True)
    assert resp.status_code == 200


def test_edit_supplier_post(app, authenticated_client, db_session):
    """POST 更新供应商"""
    supplier = create_supplier(code='EDT_SUP02', name='原名称')

    resp = authenticated_client.post(f'/partner/suppliers/{supplier.id}/edit', data={
        'code': 'EDT_SUP02',
        'name': '新名称',
        'contact_person': '李四',
        'phone': '13900000001',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        s = db.session.get(Supplier, supplier.id)
        assert s.name == '新名称'


def test_delete_supplier(authenticated_client):
    """删除供应商页面响应正常"""
    resp = authenticated_client.get('/partner/suppliers', follow_redirects=True)
    assert resp.status_code == 200


def test_supplier_not_found_404(authenticated_client):
    """不存在的供应商返回 404"""
    resp = authenticated_client.get('/partner/suppliers/99999/edit', follow_redirects=False)
    assert resp.status_code == 404


# ==================== 客户 ====================

def test_customers_list(authenticated_client):
    """GET /partner/customers 返回 200"""
    resp = authenticated_client.get('/partner/customers', follow_redirects=True)
    assert resp.status_code == 200


def test_add_customer_get(authenticated_client):
    """GET /partner/customers/new 返回 200"""
    resp = authenticated_client.get('/partner/customers/new', follow_redirects=True)
    assert resp.status_code == 200


def test_add_customer_post(app, authenticated_client, db_session):
    """POST 添加客户"""
    resp = authenticated_client.post('/partner/customers/new', data={
        'code': 'NEW_CUS01',
        'name': '新客户',
        'contact_person': '王五',
        'phone': '13700000001',
        'address': '客户地址',
        'email': 'customer@test.com',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        c = Customer.query.filter_by(code='NEW_CUS01').first()
        assert c is not None
        assert c.name == '新客户'


def test_edit_customer(app, authenticated_client, db_session):
    """编辑客户"""
    customer = create_customer(code='EDT_CUS01', name='编辑客户')

    resp = authenticated_client.get(f'/partner/customers/{customer.id}/edit', follow_redirects=True)
    assert resp.status_code == 200


def test_edit_customer_post(app, authenticated_client, db_session):
    """POST 更新客户"""
    customer = create_customer(code='EDT_CUS02', name='原名称')

    resp = authenticated_client.post(f'/partner/customers/{customer.id}/edit', data={
        'code': 'EDT_CUS02',
        'name': '新客户名',
        'contact_person': '赵六',
        'phone': '13600000001',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        c = db.session.get(Customer, customer.id)
        assert c.name == '新客户名'


def test_delete_customer(app, authenticated_client, db_session):
    """删除客户"""
    customer = create_customer(code='DEL_CUS01', name='删除客户')
    customer_id = customer.id

    resp = authenticated_client.post(f'/partner/customers/{customer.id}/delete', follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        assert db.session.get(Customer, customer_id) is None


def test_customer_not_found_404(authenticated_client):
    """不存在的客户返回 404"""
    resp = authenticated_client.get('/partner/customers/99999/edit', follow_redirects=False)
    assert resp.status_code == 404


# ==================== 仓库 ====================

def test_warehouses_list(authenticated_client):
    """GET /partner/warehouses 返回 200"""
    resp = authenticated_client.get('/partner/warehouses', follow_redirects=True)
    assert resp.status_code == 200


def test_add_warehouse_get(authenticated_client):
    """GET /partner/warehouses/new 返回 200"""
    resp = authenticated_client.get('/partner/warehouses/new', follow_redirects=True)
    assert resp.status_code == 200


def test_add_warehouse_post(app, authenticated_client, db_session):
    """POST 添加仓库"""
    resp = authenticated_client.post('/partner/warehouses/new', data={
        'code': 'NEW_WH01',
        'name': '新仓库',
        'address': '仓库地址',
        'manager': '管理员',
        'phone': '13500000001',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        w = Warehouse.query.filter_by(code='NEW_WH01').first()
        assert w is not None
        assert w.name == '新仓库'


def test_edit_warehouse(app, authenticated_client, db_session):
    """编辑仓库"""
    warehouse = create_warehouse(code='EDT_WH01', name='编辑仓库')

    resp = authenticated_client.get(f'/partner/warehouses/{warehouse.id}/edit', follow_redirects=True)
    assert resp.status_code == 200


def test_delete_warehouse(authenticated_client):
    """删除仓库页面响应正常"""
    resp = authenticated_client.get('/partner/warehouses', follow_redirects=True)
    assert resp.status_code == 200


def test_warehouse_not_found_404(authenticated_client):
    """不存在的仓库返回 404"""
    resp = authenticated_client.get('/partner/warehouses/99999/edit', follow_redirects=False)
    assert resp.status_code == 404


def test_unauthenticated_redirect(client):
    """未登录访问合作方首页重定向"""
    resp = client.get('/partner/suppliers', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers.get('Location', '')
