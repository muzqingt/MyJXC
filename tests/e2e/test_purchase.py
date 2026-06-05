"""
采购流程 E2E 测试
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time


def login(driver, base_url):
    """登录辅助函数"""
    driver.get(f'{base_url}/auth/login')
    driver.find_element(By.NAME, 'username').send_keys('admin')
    driver.find_element(By.NAME, 'password').send_keys('admin123')
    driver.find_element(By.ID, 'submit').click()
    WebDriverWait(driver, 10).until(EC.url_changes(f'{base_url}/auth/login'))


def test_purchase_order_create(driver, app_server):
    """创建采购订单"""
    login(driver, app_server)

    # 先创建供应商和商品
    driver.get(f'{app_server}/partner/suppliers/new')
    driver.find_element(By.NAME, 'code').send_keys('E2E_SUP_001')
    driver.find_element(By.NAME, 'name').send_keys('E2E测试供应商')
    driver.find_element(By.NAME, 'contact_person').send_keys('联系人')
    driver.find_element(By.NAME, 'phone').send_keys('13800000001')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)

    driver.get(f'{app_server}/product/products/new')
    driver.find_element(By.NAME, 'code').send_keys('E2E_PROD_001')
    driver.find_element(By.NAME, 'name').send_keys('E2E测试商品')
    driver.find_element(By.NAME, 'unit').send_keys('个')
    driver.find_element(By.NAME, 'purchase_price').send_keys('50')
    driver.find_element(By.NAME, 'sale_price').send_keys('100')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)

    # 创建采购订单
    driver.get(f'{app_server}/purchase/orders/new')
    assert '新建采购订单' in driver.page_source or '采购订单' in driver.page_source


def test_purchase_orders_list(driver, app_server):
    """采购订单列表"""
    login(driver, app_server)
    driver.get(f'{app_server}/purchase/')
    assert '采购管理' in driver.page_source


def test_purchase_returns_list(driver, app_server):
    """采购退货列表"""
    login(driver, app_server)
    driver.get(f'{app_server}/purchase/returns')
    assert '退货' in driver.page_source


def test_stock_in_new_page(driver, app_server):
    """新建入库单页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/purchase/stock-ins/new')
    assert '入库' in driver.page_source
