"""
MyJXC Playwright 自动化测试
运行方式: pytest test_playwright.py -v
"""
import pytest
from playwright.sync_api import sync_playwright, expect


BASE_URL = "http://127.0.0.1:5001"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


def login(page):
    """登录"""
    page.goto(f"{BASE_URL}/auth/login")
    page.fill("input[name='username']", ADMIN_USER)
    page.fill("input[name='password']", ADMIN_PASS)
    page.click("button[type='submit']")
    page.wait_for_url("**/system/**")


class TestAuth:
    """认证测试"""
    
    def test_login_success(self, page):
        login(page)
        expect(page.locator("body")).to_contain_text("系统功能")
    
    def test_login_invalid(self, page):
        page.goto(f"{BASE_URL}/auth/login")
        page.fill("input[name='username']", "wrong")
        page.fill("input[name='password']", "wrong")
        page.click("button[type='submit']")
        expect(page.locator(".alert")).to_contain_text("用户名或密码错误")


class TestProduct:
    """商品管理测试"""
    
    def test_product_list(self, page):
        login(page)
        page.goto(f"{BASE_URL}/product/")
        expect(page.locator("body")).to_contain_text("商品")
    
    def test_category_list(self, page):
        login(page)
        page.goto(f"{BASE_URL}/product/categories")
        expect(page.locator("body")).to_contain_text("分类")
    
    def test_supplier_list(self, page):
        login(page)
        page.goto(f"{BASE_URL}/product/suppliers")
        expect(page.locator("body")).to_contain_text("供应商")
    
    def test_customer_list(self, page):
        login(page)
        page.goto(f"{BASE_URL}/product/customers")
        expect(page.locator("body")).to_contain_text("客户")
    
    def test_warehouse_list(self, page):
        login(page)
        page.goto(f"{BASE_URL}/product/warehouses")
        expect(page.locator("body")).to_contain_text("仓库")


class TestPurchase:
    """采购管理测试"""
    
    def test_purchase_index(self, page):
        login(page)
        page.goto(f"{BASE_URL}/purchase/")
        expect(page.locator("body")).to_contain_text("采购")
    
    def test_new_purchase_order(self, page):
        login(page)
        page.goto(f"{BASE_URL}/purchase/new")
        expect(page.locator("body")).to_contain_text("新建采购订单")


class TestSales:
    """销售管理测试"""
    
    def test_sales_index(self, page):
        login(page)
        page.goto(f"{BASE_URL}/sales/")
        expect(page.locator("body")).to_contain_text("销售")
    
    def test_new_sales_order(self, page):
        login(page)
        page.goto(f"{BASE_URL}/sales/new")
        expect(page.locator("body")).to_contain_text("新建销售订单")


class TestInventory:
    """库存管理测试"""
    
    def test_inventory_index(self, page):
        login(page)
        page.goto(f"{BASE_URL}/inventory/")
        expect(page.locator("body")).to_contain_text("库存")
    
    def test_stock_transfer(self, page):
        login(page)
        page.goto(f"{BASE_URL}/inventory/stock_transfer")
        expect(page.locator("body")).to_contain_text("调拨")
    
    def test_stock_check(self, page):
        login(page)
        page.goto(f"{BASE_URL}/inventory/stock_check")
        expect(page.locator("body")).to_contain_text("盘点")
    
    def test_stock_adjust(self, page):
        login(page)
        page.goto(f"{BASE_URL}/inventory/stock_adjust")
        expect(page.locator("body")).to_contain_text("调整")


class TestFinance:
    """财务管理测试"""
    
    def test_finance_index(self, page):
        login(page)
        page.goto(f"{BASE_URL}/finance/")
        expect(page.locator("body")).to_contain_text("财务")
    
    def test_receipts(self, page):
        login(page)
        page.goto(f"{BASE_URL}/finance/receipts")
        expect(page.locator("body")).to_contain_text("收款")
    
    def test_payments(self, page):
        login(page)
        page.goto(f"{BASE_URL}/finance/payments")
        expect(page.locator("body")).to_contain_text("付款")
    
    def test_expenses(self, page):
        login(page)
        page.goto(f"{BASE_URL}/finance/expenses")
        expect(page.locator("body")).to_contain_text("费用")


class TestReport:
    """报表测试"""
    
    def test_report_index(self, page):
        login(page)
        page.goto(f"{BASE_URL}/report/")
        expect(page.locator("body")).to_contain_text("报表")
    
    def test_inventory_report(self, page):
        login(page)
        page.goto(f"{BASE_URL}/report/inventory_report")
        expect(page.locator("body")).to_contain_text("库存")
    
    def test_sales_ranking(self, page):
        login(page)
        page.goto(f"{BASE_URL}/report/sales_ranking")
        expect(page.locator("body")).to_contain_text("销售排行")


class TestSystem:
    """系统管理测试"""
    
    def test_system_index(self, page):
        login(page)
        page.goto(f"{BASE_URL}/system/")
        expect(page.locator("body")).to_contain_text("系统功能")
    
    def test_users(self, page):
        login(page)
        page.goto(f"{BASE_URL}/system/users")
        expect(page.locator("body")).to_contain_text("用户")
    
    def test_logs(self, page):
        login(page)
        page.goto(f"{BASE_URL}/system/logs")
        expect(page.locator("body")).to_contain_text("日志")
    
    def test_backup(self, page):
        login(page)
        page.goto(f"{BASE_URL}/system/backup")
        expect(page.locator("body")).to_contain_text("备份")
    
    def test_settings(self, page):
        login(page)
        page.goto(f"{BASE_URL}/system/settings")
        expect(page.locator("body")).to_contain_text("设置")


class TestCRUD:
    """CRUD功能测试"""
    
    def test_create_category(self, page):
        login(page)
        page.goto(f"{BASE_URL}/product/categories")
        
        # 点击新建
        page.click("a:has-text('添加分类')")
        page.wait_for_url("**/categories/new")
        
        # 填写表单
        page.fill("input[name='name']", "测试分类")
        page.click("button[type='submit']")
        
        # 验证添加成功
        expect(page.locator("body")).to_contain_text("测试分类")
    
    def test_create_supplier(self, page):
        login(page)
        page.goto(f"{BASE_URL}/product/suppliers/new")
        
        page.fill("input[name='code']", "SUP001")
        page.fill("input[name='name']", "测试供应商")
        page.fill("input[name='phone']", "13800138000")
        page.click("button[type='submit']")
        
        expect(page.locator("body")).to_contain_text("测试供应商")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
