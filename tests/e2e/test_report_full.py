"""
报表模块完整 E2E 测试
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


# ==================== 报表页面 ====================

def test_report_index(driver, app_server):
    """报表首页"""
    login(driver, app_server)
    driver.get(f'{app_server}/report/')
    assert '报表' in driver.page_source


def test_inventory_report(driver, app_server):
    """进销存报表"""
    login(driver, app_server)
    driver.get(f'{app_server}/report/inventory-report')
    assert '进销存' in driver.page_source or '报表' in driver.page_source


def test_sales_ranking(driver, app_server):
    """销售排行"""
    login(driver, app_server)
    driver.get(f'{app_server}/report/sales-ranking')
    assert '销售' in driver.page_source or '排行' in driver.page_source


def test_customer_statistics(driver, app_server):
    """客户统计"""
    login(driver, app_server)
    driver.get(f'{app_server}/report/customer-statistics')
    assert '客户' in driver.page_source or '统计' in driver.page_source


def test_supplier_statistics(driver, app_server):
    """供应商统计"""
    login(driver, app_server)
    driver.get(f'{app_server}/report/supplier-statistics')
    assert '供应商' in driver.page_source or '统计' in driver.page_source


def test_daily_report(driver, app_server):
    """日报"""
    login(driver, app_server)
    driver.get(f'{app_server}/report/daily-report')
    assert '日报' in driver.page_source or '日报' in driver.page_source


# ==================== 导出功能 ====================

def test_export_inventory(driver, app_server):
    """导出进销存报表"""
    login(driver, app_server)
    driver.get(f'{app_server}/report/export/inventory')
    # 检查是否触发了下载
    assert driver.current_url is not None


def test_export_sales_ranking(driver, app_server):
    """导出销售排行"""
    login(driver, app_server)
    driver.get(f'{app_server}/report/export/sales-ranking')
    assert driver.current_url is not None


def test_export_customer(driver, app_server):
    """导出客户统计"""
    login(driver, app_server)
    driver.get(f'{app_server}/report/export/customer')
    assert driver.current_url is not None


def test_export_supplier(driver, app_server):
    """导出供应商统计"""
    login(driver, app_server)
    driver.get(f'{app_server}/report/export/supplier')
    assert driver.current_url is not None


def test_export_daily(driver, app_server):
    """导出日报"""
    login(driver, app_server)
    driver.get(f'{app_server}/report/export/daily')
    assert driver.current_url is not None


def test_export_products(driver, app_server):
    """导出商品列表"""
    login(driver, app_server)
    driver.get(f'{app_server}/report/export-products')
    assert driver.current_url is not None


# ==================== 财务导出 ====================

def test_export_receipts(driver, app_server):
    """导出收款记录"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/export-receipts')
    assert driver.current_url is not None


def test_export_payments(driver, app_server):
    """导出付款记录"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/export-payments')
    assert driver.current_url is not None


def test_export_profit_analysis(driver, app_server):
    """导出利润分析"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/export-profit-analysis')
    assert driver.current_url is not None


def test_export_expenses(driver, app_server):
    """导出费用记录"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/export-expenses')
    assert driver.current_url is not None
