"""
冒烟测试 — 验证测试基础设施可用
"""
import pytest


def test_app_creation(app):
    """app fixture 创建成功，config 为 TESTING"""
    assert app.config['TESTING'] is True
    assert app.config['WTF_CSRF_ENABLED'] is False


def test_home_redirect(client):
    """未登录访问首页重定向到登录页"""
    resp = client.get('/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers.get('Location', '')


def test_login_logout(client):
    """登录/登出流程正常"""
    resp = client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123',
    }, follow_redirects=True)
    assert resp.status_code == 200

    resp = client.post('/auth/logout', follow_redirects=True)
    assert resp.status_code == 200


def test_factory_user(app, db_session):
    """create_user 工厂函数可用"""
    from tests.factories import create_user
    user = create_user(username='factory_user', password='pass123')
    assert user.id is not None
    assert user.username == 'factory_user'
    assert user.check_password('pass123')


def test_factory_product(app, db_session, sample_category):
    """create_product 工厂函数可用"""
    from tests.factories import create_product
    product = create_product(
        code='FAC001',
        name='工厂商品',
        category_id=sample_category.id,
    )
    assert product.id is not None
    assert product.code == 'FAC001'


def test_authenticated_access(authenticated_client):
    """登录后可访问首页"""
    resp = authenticated_client.get('/', follow_redirects=True)
    assert resp.status_code == 200
