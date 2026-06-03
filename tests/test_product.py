"""
商品模块测试 — 商品、分类 CRUD
"""
import pytest
from app import db
from app.models import Product, Category
from tests.factories import create_product, create_category


# ==================== 商品 ====================

def test_products_list(authenticated_client):
    """GET /product/products 返回 200"""
    resp = authenticated_client.get('/product/products', follow_redirects=True)
    assert resp.status_code == 200


def test_add_product_get(authenticated_client):
    """GET /product/products/new 返回 200"""
    resp = authenticated_client.get('/product/products/new', follow_redirects=True)
    assert resp.status_code == 200


def test_add_product_post(app, authenticated_client, db_session):
    """POST 添加商品"""
    category = create_category(name='测试分类')

    resp = authenticated_client.post('/product/products/new', data={
        'code': 'NEW_PROD01',
        'name': '新商品',
        'category_id': str(category.id),
        'unit': '个',
        'sale_price': '100.00',
        'purchase_price': '50.00',
        'safety_stock': '10',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        p = Product.query.filter_by(code='NEW_PROD01').first()
        assert p is not None
        assert p.name == '新商品'


def test_edit_product(app, authenticated_client, db_session):
    """编辑商品"""
    product = create_product(code='EDT_PROD01', name='编辑商品')

    resp = authenticated_client.get(f'/product/products/{product.id}/edit', follow_redirects=True)
    assert resp.status_code == 200


def test_edit_product_post(app, authenticated_client, db_session):
    """POST 更新商品"""
    product = create_product(code='EDT_PROD02', name='原名称')

    resp = authenticated_client.post(f'/product/products/{product.id}/edit', data={
        'code': 'EDT_PROD02',
        'name': '新商品名',
        'unit': '件',
        'sale_price': '200.00',
        'purchase_price': '100.00',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.name == '新商品名'


def test_delete_product(authenticated_client):
    """删除商品页面响应正常"""
    resp = authenticated_client.get('/product/products', follow_redirects=True)
    assert resp.status_code == 200


def test_view_product(app, authenticated_client, db_session):
    """查看商品详情"""
    product = create_product(code='VW_PROD01', name='查看商品')

    resp = authenticated_client.get(f'/product/products/{product.id}', follow_redirects=True)
    assert resp.status_code == 200


def test_product_not_found_404(authenticated_client):
    """不存在的商品返回 404"""
    resp = authenticated_client.get('/product/products/99999', follow_redirects=False)
    assert resp.status_code == 404


# ==================== 分类 ====================

def test_categories_list(authenticated_client):
    """GET /product/categories 返回 200"""
    resp = authenticated_client.get('/product/categories', follow_redirects=True)
    assert resp.status_code == 200


def test_add_category_get(authenticated_client):
    """GET /product/categories/new 返回 200"""
    resp = authenticated_client.get('/product/categories/new', follow_redirects=True)
    assert resp.status_code == 200


def test_add_category_post(app, authenticated_client, db_session):
    """POST 添加分类"""
    resp = authenticated_client.post('/product/categories/new', data={
        'name': '新分类',
        'description': '分类描述',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        c = Category.query.filter_by(name='新分类').first()
        assert c is not None


def test_edit_category(app, authenticated_client, db_session):
    """编辑分类"""
    category = create_category(name='编辑分类')

    resp = authenticated_client.get(f'/product/categories/{category.id}/edit', follow_redirects=True)
    assert resp.status_code == 200


def test_delete_category(app, authenticated_client, db_session):
    """删除分类"""
    category = create_category(name='删除分类')
    category_id = category.id

    resp = authenticated_client.post(f'/product/categories/{category.id}/delete', follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        assert db.session.get(Category, category_id) is None


# ==================== API ====================

def test_api_products(authenticated_client):
    """GET /product/api/products 返回 JSON"""
    resp = authenticated_client.get('/product/api/products')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_api_categories(authenticated_client):
    """GET /product/api/categories 返回 JSON"""
    resp = authenticated_client.get('/product/api/categories')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_unauthenticated_redirect(client):
    """未登录访问商品首页重定向"""
    resp = client.get('/product/products', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers.get('Location', '')
