"""
财务流程 E2E 测试
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


def test_finance_index(driver, app_server):
    """财务管理首页"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/')
    assert '财务' in driver.page_source


def test_receipts_list(driver, app_server):
    """收款列表"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/receipts')
    assert '收款' in driver.page_source


def test_payments_list(driver, app_server):
    """付款列表"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/payments')
    assert '付款' in driver.page_source


def test_expenses_list(driver, app_server):
    """费用列表"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/expenses')
    assert '费用' in driver.page_source


def test_profit_analysis(driver, app_server):
    """利润分析"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/profit-analysis')
    assert '利润' in driver.page_source


def test_ar_ap_search(driver, app_server):
    """应收应付查询"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/ar-ap-search')
    assert '应收' in driver.page_source or '应付' in driver.page_source


def test_receipt_add_page(driver, app_server):
    """添加收款页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/receipt/add')
    assert '收款' in driver.page_source


def test_payment_add_page(driver, app_server):
    """添加付款页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/payment/add')
    assert '付款' in driver.page_source


def test_expense_add_page(driver, app_server):
    """添加费用页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/finance/expense/add')
    assert '费用' in driver.page_source
