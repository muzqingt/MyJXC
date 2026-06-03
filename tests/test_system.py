"""
系统管理模块测试 — 用户管理、设置、备份、日志
"""
import pytest
from app import db
from app.models import User
from tests.factories import create_user


# ==================== 系统首页 ====================

def test_system_index(authenticated_client):
    """GET /system/ 返回 200"""
    resp = authenticated_client.get('/system/', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 日志 ====================

def test_logs(authenticated_client):
    """GET /system/logs 返回 200"""
    resp = authenticated_client.get('/system/logs', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 用户管理 ====================

def test_user_management(authenticated_client):
    """GET /system/users 返回 200"""
    resp = authenticated_client.get('/system/users', follow_redirects=True)
    assert resp.status_code == 200


def test_add_user(authenticated_client):
    """POST 添加用户"""
    resp = authenticated_client.post('/system/user/add', data={
        'username': 'newsysuser',
        'email': 'sysuser@test.com',
        'password': 'pass123',
        'role': 'user',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_edit_user(app, authenticated_client, db_session):
    """编辑用户页面"""
    user = create_user(username='editsysuser', password='pass123')
    db.session.commit()

    resp = authenticated_client.get(f'/system/user/edit/{user.id}', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 备份 ====================

def test_backup_page(authenticated_client):
    """GET /system/backup 返回 200"""
    resp = authenticated_client.get('/system/backup', follow_redirects=True)
    assert resp.status_code == 200


def test_backup_list(authenticated_client):
    """GET /system/backup/list 返回 200"""
    resp = authenticated_client.get('/system/backup/list', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 设置 ====================

def test_settings(authenticated_client):
    """GET /system/settings 返回 200"""
    resp = authenticated_client.get('/system/settings', follow_redirects=True)
    assert resp.status_code == 200


# ==================== API ====================

def test_system_info_api(authenticated_client):
    """GET /system/api/system-info 返回 JSON"""
    resp = authenticated_client.get('/system/api/system-info')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)


def test_recent_logs_api(authenticated_client):
    """GET /system/api/system/recent-logs 返回 JSON"""
    resp = authenticated_client.get('/system/api/system/recent-logs')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, (list, dict))


# ==================== 权限 ====================

def test_unauthenticated_redirect(client):
    """未登录访问系统首页重定向"""
    resp = client.get('/system/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers.get('Location', '')
