"""
表单验证 E2E 测试
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


def test_supplier_form_required_fields(driver, app_server):
    """供应商表单必填字段验证"""
    login(driver, app_server)
    driver.get(f'{app_server}/partner/suppliers/new')

    # 不填写任何字段直接提交
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)

    # 检查是否还在同一页面（表单验证失败）
    assert '/partner/suppliers/new' in driver.current_url


def test_customer_form_required_fields(driver, app_server):
    """客户表单必填字段验证"""
    login(driver, app_server)
    driver.get(f'{app_server}/partner/customers/new')

    # 不填写任何字段直接提交
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)

    # 检查是否还在同一页面（表单验证失败）
    assert '/partner/customers/new' in driver.current_url


def test_product_form_required_fields(driver, app_server):
    """商品表单必填字段验证"""
    login(driver, app_server)
    driver.get(f'{app_server}/product/products/new')

    # 不填写任何字段直接提交
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)

    # 检查是否还在同一页面（表单验证失败）
    assert '/product/products/new' in driver.current_url


def test_login_form_validation(driver, app_server):
    """登录表单验证"""
    driver.get(f'{app_server}/auth/login')

    # 不填写任何字段直接提交
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)

    # 检查是否还在登录页面
    assert '/auth/login' in driver.current_url


def test_password_change_validation(driver, app_server):
    """密码修改表单验证"""
    login(driver, app_server)
    driver.get(f'{app_server}/auth/profile')

    # 检查密码修改表单存在
    page_source = driver.page_source
    assert '修改密码' in page_source or '密码' in page_source
