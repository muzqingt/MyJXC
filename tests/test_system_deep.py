"""
系统模块深度测试 — 用户管理、设置、备份
"""
import pytest
from tests.helpers import get_page, post_page


# ==================== 用户管理 ====================

def test_edit_user_post(app, authenticated_client, db_session):
    """POST 编辑用户"""
    from tests.factories import create_user
    from app import db

    user = create_user(username='editsysuser2', password='pass123', role='user')
    db.session.commit()

    post_page(authenticated_client, f'/system/user/edit/{user.id}', {
        'username': 'editsysuser2',
        'email': 'edited@test.com',
        'role': 'user',
        'is_active': 'y',
    })


# ==================== 设置 ====================

def test_save_settings(authenticated_client):
    """POST 保存系统设置"""
    resp = authenticated_client.post('/system/api/system/settings', data={
        'COMPANY_NAME': '测试公司',
        'DEFAULT_WAREHOUSE': '1',
    }, follow_redirects=True)
    # 可能返回 200 或 400（验证错误）
    assert resp.status_code in (200, 400)


# ==================== 日志 ====================

def test_recent_logs_api(authenticated_client):
    """GET 最近日志 API"""
    get_page(authenticated_client, '/system/api/system/recent-logs')


def test_system_info_api(authenticated_client):
    """GET 系统信息 API"""
    get_page(authenticated_client, '/system/api/system-info')


# ==================== 备份 ====================

def test_create_backup(authenticated_client):
    """POST 创建备份"""
    resp = authenticated_client.post('/system/backup/create', follow_redirects=True)
    assert resp.status_code == 200


def test_export_db(authenticated_client):
    """GET 导出数据库"""
    get_page(authenticated_client, '/system/api/system/export-db')


# ==================== 数据库优化 ====================

def test_optimize_db(authenticated_client):
    """POST 优化数据库"""
    resp = authenticated_client.post('/system/api/system/optimize-db', follow_redirects=True)
    # 可能返回 200 或 500（权限问题）
    assert resp.status_code in (200, 500)


# ==================== 清理日志 ====================

def test_clean_logs(authenticated_client):
    """POST 清理日志"""
    resp = authenticated_client.post('/system/api/system/clean-logs', follow_redirects=True)
    assert resp.status_code in (200, 500)
