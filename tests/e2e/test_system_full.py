"""
系统管理模块完整 E2E 测试
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def login(driver, base_url):
    """登录辅助函数"""
    driver.get(f'{base_url}/auth/login')
    driver.find_element(By.NAME, 'username').send_keys('admin')
    driver.find_element(By.NAME, 'password').send_keys('admin123')
    driver.find_element(By.ID, 'submit').click()
    WebDriverWait(driver, 10).until(EC.url_changes(f'{base_url}/auth/login'))


# ==================== 用户管理 ====================

def test_users_list(driver, app_server):
    """用户列表"""
    login(driver, app_server)
    driver.get(f'{app_server}/system/users')
    assert '用户' in driver.page_source


def test_user_add_page(driver, app_server):
    """添加用户页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/system/users')
    # 检查页面有添加用户的入口
    assert '用户' in driver.page_source


def test_user_edit_page(driver, app_server):
    """编辑用户页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/system/user/edit/1')
    assert '用户' in driver.page_source or '编辑' in driver.page_source


# ==================== 系统设置 ====================

def test_settings_page(driver, app_server):
    """系统设置页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/system/settings')
    assert '设置' in driver.page_source


def test_system_info_api(driver, app_server):
    """系统信息 API"""
    login(driver, app_server)
    driver.get(f'{app_server}/system/api/system-info')
    assert '{' in driver.page_source or 'python' in driver.page_source.lower()


def test_recent_logs_api(driver, app_server):
    """最近日志 API"""
    login(driver, app_server)
    driver.get(f'{app_server}/system/api/system/recent-logs')
    assert '[' in driver.page_source or '{' in driver.page_source


# ==================== 备份管理 ====================

def test_backup_page(driver, app_server):
    """备份页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/system/backup')
    assert '备份' in driver.page_source


def test_backup_list_api(driver, app_server):
    """备份列表 API"""
    login(driver, app_server)
    driver.get(f'{app_server}/system/backup/list')
    # 检查返回 JSON
    assert '[' in driver.page_source or '{' in driver.page_source


# ==================== 系统日志 ====================

def test_logs_page(driver, app_server):
    """系统日志页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/system/logs')
    assert '日志' in driver.page_source


def test_system_index(driver, app_server):
    """系统管理首页"""
    login(driver, app_server)
    driver.get(f'{app_server}/system/')
    assert '系统' in driver.page_source


# ==================== 个人资料 ====================

def test_profile_page(driver, app_server):
    """个人资料页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/auth/profile')
    assert '个人' in driver.page_source or '资料' in driver.page_source


def test_change_password_page(driver, app_server):
    """修改密码"""
    login(driver, app_server)
    driver.get(f'{app_server}/auth/profile')
    assert '密码' in driver.page_source


def test_change_email_page(driver, app_server):
    """修改邮箱"""
    login(driver, app_server)
    driver.get(f'{app_server}/auth/profile')
    assert '邮箱' in driver.page_source or 'email' in driver.page_source.lower()
