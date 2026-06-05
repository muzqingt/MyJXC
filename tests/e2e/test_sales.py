"""
销售流程 E2E 测试
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


def test_sales_order_create_page(driver, app_server):
    """创建销售订单页面"""
    login(driver, app_server)

    # 先创建客户
    driver.get(f'{app_server}/partner/customers/new')
    driver.find_element(By.NAME, 'code').send_keys('E2E_CUS_001')
    driver.find_element(By.NAME, 'name').send_keys('E2E测试客户')
    driver.find_element(By.NAME, 'contact_person').send_keys('联系人')
    driver.find_element(By.NAME, 'phone').send_keys('13900000001')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)

    # 创建销售订单
    driver.get(f'{app_server}/sales/orders/new')
    assert '新建销售订单' in driver.page_source or '销售订单' in driver.page_source


def test_sales_orders_list(driver, app_server):
    """销售订单列表"""
    login(driver, app_server)
    driver.get(f'{app_server}/sales/')
    assert '销售管理' in driver.page_source


def test_sales_returns_list(driver, app_server):
    """销售退货列表"""
    login(driver, app_server)
    driver.get(f'{app_server}/sales/returns')
    assert '退货' in driver.page_source


def test_stock_out_new_page(driver, app_server):
    """新建出库单页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/sales/stock-outs/new')
    assert '出库' in driver.page_source
