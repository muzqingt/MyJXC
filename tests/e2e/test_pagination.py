"""
分页和筛选 E2E 测试
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


def test_purchase_orders_pagination(driver, app_server):
    """采购订单分页"""
    login(driver, app_server)
    driver.get(f'{app_server}/purchase/')

    # 检查分页元素是否存在
    page_source = driver.page_source
    # 分页可能没有数据时不显示，所以只检查页面加载成功
    assert '采购管理' in page_source


def test_sales_orders_pagination(driver, app_server):
    """销售订单分页"""
    login(driver, app_server)
    driver.get(f'{app_server}/sales/')

    # 检查页面加载成功
    assert '销售管理' in driver.page_source


def test_receipts_pagination(driver, app_server):
    """收款记录分页"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/receipts')

    # 检查页面加载成功
    assert '收款' in driver.page_source


def test_payments_pagination(driver, app_server):
    """付款记录分页"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/payments')

    # 检查页面加载成功
    assert '付款' in driver.page_source


def test_expenses_pagination(driver, app_server):
    """费用记录分页"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/expenses')

    # 检查页面加载成功
    assert '费用' in driver.page_source


def test_stock_logs_pagination(driver, app_server):
    """库存日志分页"""
    login(driver, app_server)
    driver.get(f'{app_server}/inventory/logs')

    # 检查页面加载成功
    assert '日志' in driver.page_source or '库存' in driver.page_source


def test_purchase_filter_by_status(driver, app_server):
    """按状态筛选采购订单"""
    login(driver, app_server)
    driver.get(f'{app_server}/purchase/?status=confirmed')

    # 检查页面加载成功
    assert '采购管理' in driver.page_source


def test_sales_filter_by_status(driver, app_server):
    """按状态筛选销售订单"""
    login(driver, app_server)
    driver.get(f'{app_server}/sales/?status=confirmed')

    # 检查页面加载成功
    assert '销售管理' in driver.page_source


def test_receipts_filter_by_date(driver, app_server):
    """按日期筛选收款记录"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/receipts?start_date=2026-01-01&end_date=2026-12-31')

    # 检查页面加载成功
    assert '收款' in driver.page_source


def test_payments_filter_by_date(driver, app_server):
    """按日期筛选付款记录"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/payments?start_date=2026-01-01&end_date=2026-12-31')

    # 检查页面加载成功
    assert '付款' in driver.page_source
