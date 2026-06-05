"""
库存操作 E2E 测试
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def login(driver, base_url):
    """登录辅助函数"""
    driver.get(f'{base_url}/auth/login')
    driver.find_element(By.NAME, 'username').send_keys('admin')
    driver.find_element(By.NAME, 'password').send_keys('admin123')
    driver.find_element(By.ID, 'submit').click()
    WebDriverWait(driver, 10).until(EC.url_changes(f'{base_url}/auth/login'))


def test_inventory_index(driver, app_server):
    """库存管理首页"""
    login(driver, app_server)
    driver.get(f'{app_server}/inventory/')
    assert '库存管理' in driver.page_source


def test_product_list(driver, app_server):
    """商品库存列表"""
    login(driver, app_server)
    driver.get(f'{app_server}/inventory/products')
    assert '商品库存' in driver.page_source


def test_stock_check_page(driver, app_server):
    """库存盘点页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/inventory/stock-check')
    assert '盘点' in driver.page_source


def test_stock_transfer_page(driver, app_server):
    """库存调拨页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/inventory/stock-transfer')
    assert '调拨' in driver.page_source


def test_stock_adjust_page(driver, app_server):
    """库存调整页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/inventory/stock-adjust')
    assert '调整' in driver.page_source


def test_stock_logs(driver, app_server):
    """库存日志"""
    login(driver, app_server)
    driver.get(f'{app_server}/inventory/logs')
    assert '日志' in driver.page_source or '库存' in driver.page_source
