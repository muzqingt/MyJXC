"""
合作伙伴模块完整 E2E 测试
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


# ==================== 供应商 ====================

def test_suppliers_list(driver, app_server):
    """供应商列表"""
    login(driver, app_server)
    driver.get(f'{app_server}/partner/suppliers')
    assert '供应商' in driver.page_source


def test_supplier_create_page(driver, app_server):
    """新建供应商页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/partner/suppliers/new')
    assert '供应商' in driver.page_source


def test_supplier_create(driver, app_server):
    """创建供应商"""
    login(driver, app_server)
    driver.get(f'{app_server}/partner/suppliers/new')
    driver.find_element(By.NAME, 'code').send_keys('FULL_SUP_001')
    driver.find_element(By.NAME, 'name').send_keys('完整测试供应商')
    driver.find_element(By.NAME, 'contact_person').send_keys('张三')
    driver.find_element(By.NAME, 'phone').send_keys('13800000001')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)
    assert '/partner/suppliers' in driver.current_url


def test_supplier_edit_page(driver, app_server):
    """编辑供应商页面"""
    login(driver, app_server)
    # 先创建供应商
    driver.get(f'{app_server}/partner/suppliers/new')
    driver.find_element(By.NAME, 'code').send_keys('EDIT_SUP_001')
    driver.find_element(By.NAME, 'name').send_keys('编辑测试供应商')
    driver.find_element(By.NAME, 'contact_person').send_keys('张三')
    driver.find_element(By.NAME, 'phone').send_keys('13800000001')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)


def test_supplier_import_page(driver, app_server):
    """供应商导入页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/partner/suppliers/import')
    assert '导入' in driver.page_source


# ==================== 客户 ====================

def test_customers_list(driver, app_server):
    """客户列表"""
    login(driver, app_server)
    driver.get(f'{app_server}/partner/customers')
    assert '客户' in driver.page_source


def test_customer_create_page(driver, app_server):
    """新建客户页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/partner/customers/new')
    assert '客户' in driver.page_source


def test_customer_create(driver, app_server):
    """创建客户"""
    login(driver, app_server)
    driver.get(f'{app_server}/partner/customers/new')
    driver.find_element(By.NAME, 'code').send_keys('FULL_CUS_001')
    driver.find_element(By.NAME, 'name').send_keys('完整测试客户')
    driver.find_element(By.NAME, 'contact_person').send_keys('李四')
    driver.find_element(By.NAME, 'phone').send_keys('13900000001')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)
    assert '/partner/customers' in driver.current_url


def test_customer_edit_page(driver, app_server):
    """编辑客户页面"""
    login(driver, app_server)
    # 先创建客户
    driver.get(f'{app_server}/partner/customers/new')
    driver.find_element(By.NAME, 'code').send_keys('EDIT_CUS_001')
    driver.find_element(By.NAME, 'name').send_keys('编辑测试客户')
    driver.find_element(By.NAME, 'contact_person').send_keys('李四')
    driver.find_element(By.NAME, 'phone').send_keys('13900000001')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)


def test_customer_import_page(driver, app_server):
    """客户导入页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/partner/customers/import')
    assert '导入' in driver.page_source


# ==================== 仓库 ====================

def test_warehouses_list(driver, app_server):
    """仓库列表"""
    login(driver, app_server)
    driver.get(f'{app_server}/partner/warehouses')
    assert '仓库' in driver.page_source


def test_warehouse_create_page(driver, app_server):
    """新建仓库页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/partner/warehouses/new')
    assert '仓库' in driver.page_source


def test_warehouse_create(driver, app_server):
    """创建仓库"""
    login(driver, app_server)
    driver.get(f'{app_server}/partner/warehouses/new')
    driver.find_element(By.NAME, 'code').send_keys('FULL_WH_001')
    driver.find_element(By.NAME, 'name').send_keys('完整测试仓库')
    driver.find_element(By.NAME, 'address').send_keys('测试地址')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)
    assert '/partner/warehouses' in driver.current_url


def test_warehouse_edit_page(driver, app_server):
    """编辑仓库页面"""
    login(driver, app_server)
    # 先创建仓库
    driver.get(f'{app_server}/partner/warehouses/new')
    driver.find_element(By.NAME, 'code').send_keys('EDIT_WH_001')
    driver.find_element(By.NAME, 'name').send_keys('编辑测试仓库')
    driver.find_element(By.NAME, 'address').send_keys('测试地址')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)
