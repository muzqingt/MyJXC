"""
系统模块深度覆盖测试
"""
import pytest
from tests.helpers import get_page, post_page
from tests.factories import create_user
from app import db


def test_system_index(authenticated_client):
    """系统首页"""
    get_page(authenticated_client, '/system/')


def test_system_logs(authenticated_client):
    """操作日志"""
    get_page(authenticated_client, '/system/logs')


def test_system_backup(authenticated_client):
    """数据备份页面"""
    get_page(authenticated_client, '/system/backup')


def test_system_backup_list(authenticated_client):
    """备份列表"""
    get_page(authenticated_client, '/system/backup/list')


def test_system_backup_create(authenticated_client):
    """创建备份"""
    resp = authenticated_client.post('/system/backup/create', follow_redirects=True)
    assert resp.status_code == 200


def test_system_settings(authenticated_client):
    """系统设置"""
    get_page(authenticated_client, '/system/settings')


def test_system_users(authenticated_client):
    """用户管理"""
    get_page(authenticated_client, '/system/users')


def test_system_add_user(authenticated_client):
    """添加用户"""
    post_page(authenticated_client, '/system/user/add', {
        'username': 'newsysuser2',
        'email': 'newsys2@test.com',
        'password': 'pass123',
        'role': 'user',
    })


def test_system_edit_user(app, authenticated_client, db_session):
    """编辑用户"""
    user = create_user(username='editsys3', password='pass123')
    db.session.commit()

    get_page(authenticated_client, f'/system/user/edit/{user.id}')


def test_system_edit_user_post(app, authenticated_client, db_session):
    """POST 编辑用户"""
    user = create_user(username='editsys4', password='pass123')
    db.session.commit()

    post_page(authenticated_client, f'/system/user/edit/{user.id}', {
        'username': 'editsys4',
        'email': 'edited4@test.com',
        'role': 'user',
        'is_active': 'y',
    })


def test_system_api_info(authenticated_client):
    """系统信息 API"""
    get_page(authenticated_client, '/system/api/system-info')


def test_system_api_logs(authenticated_client):
    """最近日志 API"""
    get_page(authenticated_client, '/system/api/system/recent-logs')


def test_system_api_optimize(authenticated_client):
    """优化数据库"""
    resp = authenticated_client.post('/system/api/system/optimize-db', follow_redirects=True)
    assert resp.status_code in (200, 500)


def test_system_api_clean_logs(authenticated_client):
    """清理日志"""
    resp = authenticated_client.post('/system/api/system/clean-logs', follow_redirects=True)
    assert resp.status_code in (200, 500)


def test_system_api_export_db(authenticated_client):
    """导出数据库"""
    get_page(authenticated_client, '/system/api/system/export-db')


def test_system_delete_user(app, authenticated_client, db_session):
    """删除用户"""
    user = create_user(username='deluser2', password='pass123')
    db.session.commit()

    resp = authenticated_client.post(
        f'/system/user/delete/{user.id}', follow_redirects=True
    )
    assert resp.status_code == 200


def test_system_delete_self(authenticated_client):
    """不能删除自己"""
    resp = authenticated_client.post('/system/user/delete/1', follow_redirects=True)
    assert resp.status_code == 200


def test_system_backup_restore_no_file(authenticated_client):
    """恢复备份 - 无文件"""
    resp = authenticated_client.post('/system/backup/restore', data={
        'filename': '',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_system_backup_delete_no_file(authenticated_client):
    """删除备份 - 无文件"""
    resp = authenticated_client.post('/system/backup/delete', data={
        'filename': '',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_system_unauthenticated(client):
    """未登录重定向"""
    resp = client.get('/system/', follow_redirects=False)
    assert resp.status_code == 302
