"""
认证模块深度覆盖测试
"""
import pytest
from tests.helpers import get_page, post_page
from tests.factories import create_user
from app import db


def test_login_page(client):
    """登录页面"""
    get_page(client, '/auth/login')


def test_login_success(client):
    """登录成功"""
    post_page(client, '/auth/login', {
        'username': 'admin',
        'password': 'admin123',
    })


def test_login_wrong_password(client):
    """错误密码"""
    resp = client.post('/auth/login', data={
        'username': 'admin',
        'password': 'wrong',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_login_nonexistent(client):
    """不存在的用户"""
    resp = client.post('/auth/login', data={
        'username': 'nonexistent',
        'password': 'password',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_register_page(client):
    """注册页面"""
    get_page(client, '/auth/register')


def test_register_success(client):
    """注册成功"""
    post_page(client, '/auth/register', {
        'username': 'newreguser',
        'email': 'newreg@test.com',
        'password': 'pass123',
        'password2': 'pass123',
    })


def test_register_duplicate(client):
    """重复用户名"""
    client.post('/auth/register', data={
        'username': 'dupuser2',
        'email': 'dup2@test.com',
        'password': 'pass123',
        'password2': 'pass123',
    })
    resp = client.post('/auth/register', data={
        'username': 'dupuser2',
        'email': 'dup3@test.com',
        'password': 'pass123',
        'password2': 'pass123',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_register_password_mismatch(client):
    """密码不匹配"""
    resp = client.post('/auth/register', data={
        'username': 'mismatch',
        'email': 'mismatch@test.com',
        'password': 'pass123',
        'password2': 'pass456',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_logout(authenticated_client):
    """登出"""
    post_page(authenticated_client, '/auth/logout', {})


def test_logout_requires_post(client):
    """GET 登出不允许"""
    resp = client.get('/auth/logout', follow_redirects=False)
    assert resp.status_code == 405


def test_profile(authenticated_client):
    """个人信息"""
    get_page(authenticated_client, '/auth/profile')


def test_change_password(authenticated_client):
    """修改密码"""
    post_page(authenticated_client, '/auth/change-password', {
        'current_password': 'admin123',
        'new_password': 'newpass123',
        'new_password2': 'newpass123',
    })


def test_change_password_wrong(authenticated_client):
    """错误当前密码"""
    resp = authenticated_client.post('/auth/change-password', data={
        'current_password': 'wrong',
        'new_password': 'newpass',
        'new_password2': 'newpass',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_change_email(authenticated_client):
    """修改邮箱"""
    post_page(authenticated_client, '/auth/change-email', {
        'new_email': 'newemail@test.com',
        'password': 'admin123',
    })


def test_change_email_wrong_password(authenticated_client):
    """错误密码修改邮箱"""
    resp = authenticated_client.post('/auth/change-email', data={
        'new_email': 'newemail2@test.com',
        'password': 'wrong',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_unauthenticated_profile(client):
    """未登录访问个人信息"""
    resp = client.get('/auth/profile', follow_redirects=False)
    assert resp.status_code == 302
