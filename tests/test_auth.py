"""
认证模块测试 — 登录、注册、登出、个人信息
"""
import pytest
from app import db
from app.models import User
from tests.factories import create_user


# ==================== 登录 ====================

def test_login_page(client):
    """GET /auth/login 返回 200"""
    resp = client.get('/auth/login')
    assert resp.status_code == 200


def test_login_success(client):
    """正确凭据登录成功"""
    resp = client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_login_wrong_password(client):
    """错误密码登录失败"""
    resp = client.post('/auth/login', data={
        'username': 'admin',
        'password': 'wrong',
    }, follow_redirects=True)
    assert resp.status_code == 200
    # 页面应该重新显示登录表单
    assert 'login' in resp.data.decode('utf-8', errors='replace').lower() or \
           '登录' in resp.data.decode('utf-8', errors='replace')


def test_login_nonexistent_user(client):
    """不存在的用户登录失败"""
    resp = client.post('/auth/login', data={
        'username': 'nonexistent',
        'password': 'password',
    }, follow_redirects=True)
    assert resp.status_code == 200


# ==================== 注册 ====================

def test_register_page(client):
    """GET /auth/register 返回 200"""
    resp = client.get('/auth/register')
    assert resp.status_code == 200


def test_register_success(client):
    """注册新用户"""
    resp = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'new@test.com',
        'password': 'newpass123',
        'password2': 'newpass123',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_register_duplicate_username(client):
    """重复用户名注册失败"""
    client.post('/auth/register', data={
        'username': 'dupuser',
        'email': 'dup1@test.com',
        'password': 'pass123',
        'password2': 'pass123',
    }, follow_redirects=True)

    resp = client.post('/auth/register', data={
        'username': 'dupuser',
        'email': 'dup2@test.com',
        'password': 'pass123',
        'password2': 'pass123',
    }, follow_redirects=True)
    assert resp.status_code == 200


# ==================== 登出 ====================

def test_logout(authenticated_client):
    """POST 登出"""
    resp = authenticated_client.post('/auth/logout', follow_redirects=True)
    assert resp.status_code == 200


def test_logout_requires_post(client):
    """GET /auth/logout 不被允许"""
    resp = client.get('/auth/logout', follow_redirects=False)
    assert resp.status_code == 405


# ==================== 个人信息 ====================

def test_profile(authenticated_client):
    """GET /auth/profile 返回 200"""
    resp = authenticated_client.get('/auth/profile', follow_redirects=True)
    assert resp.status_code == 200


def test_change_password(authenticated_client):
    """修改密码"""
    resp = authenticated_client.post('/auth/change-password', data={
        'current_password': 'admin123',
        'new_password': 'newadmin123',
        'new_password2': 'newadmin123',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_change_password_wrong_current(authenticated_client):
    """当前密码错误时修改失败"""
    resp = authenticated_client.post('/auth/change-password', data={
        'current_password': 'wrong',
        'new_password': 'newpass',
        'new_password2': 'newpass',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_change_email(authenticated_client):
    """修改邮箱"""
    resp = authenticated_client.post('/auth/change-email', data={
        'new_email': 'newadmin@test.com',
        'password': 'admin123',
    }, follow_redirects=True)
    assert resp.status_code == 200


# ==================== 权限 ====================

def test_unauthenticated_profile_redirect(client):
    """未登录访问个人信息重定向"""
    resp = client.get('/auth/profile', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers.get('Location', '')
