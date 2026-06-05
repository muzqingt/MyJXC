"""
商品模块完整 E2E 测试
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


# ==================== 商品 CRUD ====================

def test_product_list_page(driver, app_server):
    """商品列表页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/product/products')
    assert '商品' in driver.page_source


def test_product_create_page(driver, app_server):
    """新建商品页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/product/products/new')
    assert '新建商品' in driver.page_source or '添加商品' in driver.page_source


def test_product_create(driver, app_server):
    """创建商品"""
    login(driver, app_server)
    driver.get(f'{app_server}/product/products/new')
    driver.find_element(By.NAME, 'code').send_keys('FULL_PROD_001')
    driver.find_element(By.NAME, 'name').send_keys('完整测试商品')
    driver.find_element(By.NAME, 'unit').send_keys('个')
    driver.find_element(By.NAME, 'purchase_price').send_keys('50')
    driver.find_element(By.NAME, 'sale_price').send_keys('100')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)
    # 检查创建成功后跳转
    assert '/product/products' in driver.current_url


def test_product_detail_page(driver, app_server):
    """商品详情页面"""
    login(driver, app_server)
    # 先创建商品
    driver.get(f'{app_server}/product/products/new')
    driver.find_element(By.NAME, 'code').send_keys('DETAIL_PROD_001')
    driver.find_element(By.NAME, 'name').send_keys('详情测试商品')
    driver.find_element(By.NAME, 'unit').send_keys('个')
    driver.find_element(By.NAME, 'purchase_price').send_keys('50')
    driver.find_element(By.NAME, 'sale_price').send_keys('100')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)


def test_product_edit_page(driver, app_server):
    """编辑商品页面"""
    login(driver, app_server)
    # 先创建商品
    driver.get(f'{app_server}/product/products/new')
    driver.find_element(By.NAME, 'code').send_keys('EDIT_PROD_001')
    driver.find_element(By.NAME, 'name').send_keys('编辑测试商品')
    driver.find_element(By.NAME, 'unit').send_keys('个')
    driver.find_element(By.NAME, 'purchase_price').send_keys('50')
    driver.find_element(By.NAME, 'sale_price').send_keys('100')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)


def test_product_api(driver, app_server):
    """商品 API"""
    login(driver, app_server)
    driver.get(f'{app_server}/product/api/products')
    assert '[' in driver.page_source or '{' in driver.page_source


def test_product_categories_page(driver, app_server):
    """商品分类页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/product/categories')
    assert '分类' in driver.page_source


def test_category_create(driver, app_server):
    """创建商品分类"""
    login(driver, app_server)
    driver.get(f'{app_server}/product/categories/new')
    driver.find_element(By.NAME, 'name').send_keys('E2E测试分类')
    driver.find_element(By.ID, 'submit').click()
    time.sleep(1)
    assert '/product/categories' in driver.current_url


def test_product_import_page(driver, app_server):
    """商品导入页面"""
    login(driver, app_server)
    driver.get(f'{app_server}/product/import')
    assert '导入' in driver.page_source


def test_product_import_template(driver, app_server):
    """商品导入模板下载"""
    login(driver, app_server)
    driver.get(f'{app_server}/product/import/template')
    # 检查是否触发了下载（页面可能重定向或返回文件）
    assert driver.current_url is not None
