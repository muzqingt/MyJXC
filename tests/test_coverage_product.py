"""
商品模块深度覆盖测试
"""
import pytest
from tests.helpers import get_page, post_page
from tests.factories import create_product, create_category
from app import db
from app.models import Product, Category


def test_products_list(authenticated_client):
    """商品列表"""
    get_page(authenticated_client, '/product/products')


def test_product_new_get(authenticated_client):
    """新建商品页面"""
    get_page(authenticated_client, '/product/products/new')


def test_product_new_post(app, authenticated_client, db_session):
    """创建商品"""
    category = create_category(name='新建分类')
    post_page(authenticated_client, '/product/products/new', {
        'code': 'NEWP01',
        'name': '新建商品',
        'category_id': str(category.id),
        'unit': '个',
        'sale_price': '100.00',
        'purchase_price': '50.00',
    })


def test_product_edit_get(app, authenticated_client, db_session):
    """编辑商品页面"""
    product = create_product(code='EDTP01', name='编辑商品')
    get_page(authenticated_client, f'/product/products/{product.id}/edit')


def test_product_edit_post(app, authenticated_client, db_session):
    """POST 编辑商品"""
    product = create_product(code='EDTP02', name='编辑商品2')
    category = create_category(name='编辑分类')
    post_page(authenticated_client, f'/product/products/{product.id}/edit', {
        'code': 'EDTP02',
        'name': '新名称',
        'category_id': str(category.id),
        'unit': '个',
        'sale_price': '200.00',
        'purchase_price': '100.00',
    })


def test_product_view(app, authenticated_client, db_session):
    """查看商品详情"""
    product = create_product(code='VWP01', name='查看商品')
    get_page(authenticated_client, f'/product/products/{product.id}')


def test_product_not_found(authenticated_client):
    """不存在的商品"""
    resp = authenticated_client.get('/product/products/99999', follow_redirects=False)
    assert resp.status_code == 404


def test_categories_list(authenticated_client):
    """分类列表"""
    get_page(authenticated_client, '/product/categories')


def test_category_new_get(authenticated_client):
    """新建分类页面"""
    get_page(authenticated_client, '/product/categories/new')


def test_category_new_post(app, authenticated_client, db_session):
    """创建分类"""
    post_page(authenticated_client, '/product/categories/new', {
        'name': '新建测试分类',
        'description': '描述',
    })


def test_category_edit_get(app, authenticated_client, db_session):
    """编辑分类页面"""
    category = create_category(name='编辑测试分类')
    get_page(authenticated_client, f'/product/categories/{category.id}/edit')


def test_category_edit_post(app, authenticated_client, db_session):
    """POST 编辑分类"""
    category = create_category(name='编辑测试分类2')
    post_page(authenticated_client, f'/product/categories/{category.id}/edit', {
        'name': '新分类名',
        'description': '新描述',
    })


def test_category_delete(app, authenticated_client, db_session):
    """删除分类"""
    category = create_category(name='删除测试分类')
    resp = authenticated_client.post(
        f'/product/categories/{category.id}/delete', follow_redirects=True
    )
    assert resp.status_code == 200


def test_api_products(authenticated_client):
    """商品 API"""
    get_page(authenticated_client, '/product/api/products')


def test_api_categories(authenticated_client):
    """分类 API"""
    get_page(authenticated_client, '/product/api/categories')


def test_unauthenticated(client):
    """未登录重定向"""
    resp = client.get('/product/products', follow_redirects=False)
    assert resp.status_code == 302
