"""
搜索组件 E2E 测试
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


def create_test_data(driver, base_url):
    """创建测试数据"""
    # 创建供应商
    driver.get(f'{base_url}/partner/suppliers/new')
    driver.find_element(By.NAME, 'code').send_keys('SEARCH_SUP_001')
    driver.find_element(By.NAME, 'name').send_keys('搜索测试供应商')
    driver.find_element(By.NAME, 'contact_person').send_keys('联系人')
    driver.find_element(By.NAME, 'phone').send_keys('13800000001')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)

    # 创建客户
    driver.get(f'{base_url}/partner/customers/new')
    driver.find_element(By.NAME, 'code').send_keys('SEARCH_CUS_001')
    driver.find_element(By.NAME, 'name').send_keys('搜索测试客户')
    driver.find_element(By.NAME, 'contact_person').send_keys('联系人')
    driver.find_element(By.NAME, 'phone').send_keys('13900000001')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)

    # 创建商品
    driver.get(f'{base_url}/product/products/new')
    driver.find_element(By.NAME, 'code').send_keys('SEARCH_PROD_001')
    driver.find_element(By.NAME, 'name').send_keys('搜索测试商品')
    driver.find_element(By.NAME, 'unit').send_keys('个')
    driver.find_element(By.NAME, 'purchase_price').send_keys('50')
    driver.find_element(By.NAME, 'sale_price').send_keys('100')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)


def test_supplier_search_in_purchase_order(driver, app_server):
    """采购订单中搜索供应商"""
    login(driver, app_server)
    create_test_data(driver, app_server)

    # 进入新建采购订单页面
    driver.get(f'{app_server}/purchase/orders/new')

    # 查找供应商搜索框
    search_input = driver.find_element(By.CSS_SELECTOR, '.entity-search-input')
    assert search_input.is_displayed()

    # 输入搜索关键词
    search_input.send_keys('搜索')
    time.sleep(1)

    # 检查下拉列表是否出现
    dropdown = driver.find_element(By.CSS_SELECTOR, '.entity-dropdown')
    assert dropdown.is_displayed()


def test_customer_search_in_sales_order(driver, app_server):
    """销售订单中搜索客户"""
    login(driver, app_server)
    create_test_data(driver, app_server)

    # 进入新建销售订单页面
    driver.get(f'{app_server}/sales/orders/new')

    # 查找客户搜索框
    search_input = driver.find_element(By.CSS_SELECTOR, '.entity-search-input')
    assert search_input.is_displayed()

    # 输入搜索关键词
    search_input.send_keys('搜索')
    time.sleep(1)

    # 检查下拉列表是否出现
    dropdown = driver.find_element(By.CSS_SELECTOR, '.entity-dropdown')
    assert dropdown.is_displayed()


def test_product_search_in_order(driver, app_server):
    """订单中搜索商品"""
    login(driver, app_server)
    create_test_data(driver, app_server)

    # 进入新建采购订单页面
    driver.get(f'{app_server}/purchase/orders/new')

    # 查找所有搜索框
    search_inputs = driver.find_elements(By.CSS_SELECTOR, '.entity-search-input')
    assert len(search_inputs) >= 1  # 至少有商品搜索框

    # 在商品搜索框输入
    product_search = search_inputs[-1]
    product_search.send_keys('搜索')
    time.sleep(1)

    # 检查下拉列表是否出现
    dropdowns = driver.find_elements(By.CSS_SELECTOR, '.entity-dropdown')
    assert any(d.is_displayed() for d in dropdowns)
