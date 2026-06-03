#!/usr/bin/env python3
"""
my-jxc 进销存管理系统 - 全面功能测试
使用 Playwright 自动化测试所有页面和功能
"""
import sys
import time
import traceback
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8080"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def ok(self, name):
        self.passed.append(name)
        print(f"  ✅ PASS: {name}")

    def fail(self, name, error):
        self.failed.append((name, str(error)))
        print(f"  ❌ FAIL: {name}")
        print(f"         Error: {error}")

    def warn(self, name, msg):
        self.warnings.append((name, msg))
        print(f"  ⚠️  WARN: {name} - {msg}")

    def summary(self):
        total = len(self.passed) + len(self.failed)
        print(f"\n{'='*60}")
        print(f"测试结果汇总: {len(self.passed)}/{total} 通过, {len(self.failed)} 失败, {len(self.warnings)} 警告")
        if self.failed:
            print(f"\n失败列表:")
            for name, err in self.failed:
                print(f"  ❌ {name}: {err[:200]}")
        if self.warnings:
            print(f"\n警告列表:")
            for name, msg in self.warnings:
                print(f"  ⚠️  {name}: {msg[:200]}")
        print(f"{'='*60}")
        return len(self.failed) == 0

results = TestResults()


def test_page(page, url, name, expected_text=None, expected_status=200):
    """测试页面是否正常加载"""
    try:
        resp = page.goto(url, wait_until="networkidle", timeout=15000)
        if resp is None:
            results.fail(name, "No response received")
            return False
        status = resp.status
        if status != expected_status:
            # Check if it's a redirect (302 -> login page)
            if status in (301, 302):
                # Follow redirects
                page.goto(url, wait_until="networkidle", timeout=15000)
                final_url = page.url
                if '/auth/login' in final_url and '/auth/login' not in url:
                    results.fail(name, f"Redirected to login (status {status})")
                    return False
            else:
                results.fail(name, f"HTTP {status}, expected {expected_status}")
                return False
        if expected_text:
            body_text = page.text_content("body")
            if expected_text not in (body_text or ""):
                results.fail(name, f"Page body missing expected text: '{expected_text[:50]}'")
                return False
        results.ok(name)
        return True
    except Exception as e:
        results.fail(name, str(e)[:300])
        return False


def login(page):
    """登录"""
    page.goto(f"{BASE_URL}/auth/login", wait_until="networkidle", timeout=15000)
    page.fill("input[name='username']", ADMIN_USER)
    page.fill("input[name='password']", ADMIN_PASS)
    page.click("button[type='submit']")
    page.wait_for_load_state("networkidle", timeout=10000)
    time.sleep(1)


def test_auth_module(page):
    """测试认证模块"""
    print("\n--- 1. 认证模块测试 ---")

    # 1.1 登录页面加载
    test_page(page, f"{BASE_URL}/auth/login", "登录页面加载", "登录")

    # 1.2 注册页面加载
    test_page(page, f"{BASE_URL}/auth/register", "注册页面加载", "注册")

    # 1.3 登录失败测试
    try:
        page.goto(f"{BASE_URL}/auth/login", wait_until="networkidle", timeout=15000)
        page.fill("input[name='username']", "wronguser")
        page.fill("input[name='password']", "wrongpass")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle", timeout=5000)
        body_text = page.text_content("body")
        if "错误" in (body_text or "") or "无效" in (body_text or ""):
            results.ok("登录失败提示")
        else:
            results.warn("登录失败提示", f"未检测到错误提示信息 (body: {str(body_text)[:100]})")
    except Exception as e:
        results.fail("登录失败提示", str(e)[:200])

    # 1.4 正确登录
    try:
        login(page)
        if page.url != f"{BASE_URL}/auth/login":
            results.ok("正确登录")
        else:
            results.fail("正确登录", "登录后仍在登录页面")
    except Exception as e:
        results.fail("正确登录", str(e)[:200])

    # 1.5 个人资料页面
    test_page(page, f"{BASE_URL}/auth/profile", "个人资料页面")


def test_product_module(page):
    """测试商品管理模块"""
    print("\n--- 2. 商品管理模块测试 ---")

    # 2.1 商品列表
    test_page(page, f"{BASE_URL}/product/", "商品列表页面", "商品")

    # 2.2 新建商品页面
    test_page(page, f"{BASE_URL}/product/products/new", "新建商品页面", "新建" if True else "")

    # 2.3 分类列表
    test_page(page, f"{BASE_URL}/product/categories", "分类列表页面", "分类")

    # 2.4 新建分类页面
    test_page(page, f"{BASE_URL}/product/categories/new", "新建分类页面")

    # 2.5 新建分类 (CRUD测试)
    try:
        ts = int(time.time())
        page.goto(f"{BASE_URL}/product/categories/new", wait_until="networkidle", timeout=15000)
        page.fill("input[name='name']", f"测试分类_{ts}")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle", timeout=10000)
        body = page.text_content("body") or ""
        if f"测试分类_{ts}" in body or "成功" in body or "添加" in body:
            results.ok("新建分类(CRUD)")
        else:
            results.warn("新建分类(CRUD)", f"未确认分类是否创建成功")
    except Exception as e:
        results.fail("新建分类(CRUD)", str(e)[:200])

    # 2.6 编辑分类
    try:
        page.goto(f"{BASE_URL}/product/categories", wait_until="networkidle", timeout=15000)
        edit_links = page.locator("a[href*='/categories/']").all()
        if edit_links:
            edit_links[0].click()
            page.wait_for_load_state("networkidle", timeout=10000)
            results.ok("编辑分类页面")
        else:
            results.warn("编辑分类页面", "无分类数据可编辑")
    except Exception as e:
        results.fail("编辑分类页面", str(e)[:200])

    # 2.7 新建商品 (CRUD测试)
    try:
        ts = int(time.time())
        page.goto(f"{BASE_URL}/product/products/new", wait_until="networkidle", timeout=15000)
        # Fill product form
        name_input = page.locator("input[name='name'], input[name='product_name'], #name")
        if name_input.count() > 0:
            name_input.first.fill(f"测试商品_{ts}")
            # Try filling other fields
            sku = page.locator("input[name='sku'], input[name='code'], #sku, #code")
            if sku.count() > 0:
                sku.first.fill(f"SKU_{ts}")
            price = page.locator("input[name='price'], input[name='purchase_price'], #price")
            if price.count() > 0:
                price.first.fill("100")
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle", timeout=10000)
            results.ok("新建商品(CRUD)")
        else:
            results.warn("新建商品(CRUD)", "未找到商品名称输入框")
    except Exception as e:
        results.fail("新建商品(CRUD)", str(e)[:200])

    # 2.8 API接口测试
    try:
        resp = page.goto(f"{BASE_URL}/product/api/products", wait_until="networkidle", timeout=10000)
        if resp and resp.status == 200:
            body = page.text_content("body") or ""
            results.ok("商品API接口")
        else:
            results.fail("商品API接口", f"HTTP {resp.status if resp else 'None'}")
    except Exception as e:
        results.fail("商品API接口", str(e)[:200])

    # 2.9 分类API接口
    try:
        resp = page.goto(f"{BASE_URL}/product/api/categories", wait_until="networkidle", timeout=10000)
        if resp and resp.status == 200:
            results.ok("分类API接口")
        else:
            results.fail("分类API接口", f"HTTP {resp.status if resp else 'None'}")
    except Exception as e:
        results.fail("分类API接口", str(e)[:200])


def test_partner_module(page):
    """测试合作伙伴模块"""
    print("\n--- 3. 合作伙伴模块测试 ---")

    # 3.1 供应商列表
    test_page(page, f"{BASE_URL}/partner/suppliers", "供应商列表页面", "供应商")

    # 3.2 新建供应商页面
    test_page(page, f"{BASE_URL}/partner/suppliers/new", "新建供应商页面")

    # 3.3 新建供应商 (CRUD)
    try:
        ts = int(time.time())
        page.goto(f"{BASE_URL}/partner/suppliers/new", wait_until="networkidle", timeout=15000)
        name_input = page.locator("input[name='name'], #name")
        if name_input.count() > 0:
            name_input.first.fill(f"测试供应商_{ts}")
            code = page.locator("input[name='code'], #code")
            if code.count() > 0:
                code.first.fill(f"SUP{ts}")
            phone = page.locator("input[name='phone'], #phone")
            if phone.count() > 0:
                phone.first.fill("13800138000")
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle", timeout=10000)
            results.ok("新建供应商(CRUD)")
        else:
            results.warn("新建供应商(CRUD)", "未找到供应商名称输入框")
    except Exception as e:
        results.fail("新建供应商(CRUD)", str(e)[:200])

    # 3.4 客户列表
    test_page(page, f"{BASE_URL}/partner/customers", "客户列表页面", "客户")

    # 3.5 新建客户页面
    test_page(page, f"{BASE_URL}/partner/customers/new", "新建客户页面")

    # 3.6 新建客户 (CRUD)
    try:
        ts = int(time.time())
        page.goto(f"{BASE_URL}/partner/customers/new", wait_until="networkidle", timeout=15000)
        name_input = page.locator("input[name='name'], #name")
        if name_input.count() > 0:
            name_input.first.fill(f"测试客户_{ts}")
            code = page.locator("input[name='code'], #code")
            if code.count() > 0:
                code.first.fill(f"CUS{ts}")
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle", timeout=10000)
            results.ok("新建客户(CRUD)")
        else:
            results.warn("新建客户(CRUD)", "未找到客户名称输入框")
    except Exception as e:
        results.fail("新建客户(CRUD)", str(e)[:200])

    # 3.7 仓库列表
    test_page(page, f"{BASE_URL}/partner/warehouses", "仓库列表页面", "仓库")

    # 3.8 新建仓库页面
    test_page(page, f"{BASE_URL}/partner/warehouses/new", "新建仓库页面")

    # 3.9 新建仓库 (CRUD)
    try:
        ts = int(time.time())
        page.goto(f"{BASE_URL}/partner/warehouses/new", wait_until="networkidle", timeout=15000)
        name_input = page.locator("input[name='name'], #name")
        if name_input.count() > 0:
            name_input.first.fill(f"测试仓库_{ts}")
            code = page.locator("input[name='code'], #code")
            if code.count() > 0:
                code.first.fill(f"WH{ts}")
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle", timeout=10000)
            results.ok("新建仓库(CRUD)")
        else:
            results.warn("新建仓库(CRUD)", "未找到仓库名称输入框")
    except Exception as e:
        results.fail("新建仓库(CRUD)", str(e)[:200])


def test_purchase_module(page):
    """测试采购管理模块"""
    print("\n--- 4. 采购管理模块测试 ---")

    # 4.1 采购首页
    test_page(page, f"{BASE_URL}/purchase/", "采购首页", "采购")

    # 4.2 新建采购订单
    test_page(page, f"{BASE_URL}/purchase/orders/new", "新建采购订单页面")

    # 4.3 新建采购订单 (CRUD)
    try:
        ts = int(time.time())
        page.goto(f"{BASE_URL}/purchase/orders/new", wait_until="networkidle", timeout=15000)
        # Fill order form
        supplier_select = page.locator("select[name='supplier_id'], select[name='supplier'], #supplier_id")
        if supplier_select.count() > 0:
            supplier_select.first.select_option(index=1)
        warehouse_select = page.locator("select[name='warehouse_id'], select[name='warehouse'], #warehouse_id")
        if warehouse_select.count() > 0:
            warehouse_select.first.select_option(index=1)

        # Add item if possible
        add_item_btn = page.locator("button:has-text('添加'), .add-item, #add_item")
        if add_item_btn.count() > 0:
            add_item_btn.first.click()
            time.sleep(0.5)

        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle", timeout=10000)
        results.ok("新建采购订单(CRUD)")
    except Exception as e:
        results.fail("新建采购订单(CRUD)", str(e)[:300])

    # 4.4 采购退货列表
    test_page(page, f"{BASE_URL}/purchase/returns", "采购退货列表页面")

    # 4.5 新建入库单
    test_page(page, f"{BASE_URL}/purchase/stock-ins/new", "新建入库单页面")


def test_sales_module(page):
    """测试销售管理模块"""
    print("\n--- 5. 销售管理模块测试 ---")

    # 5.1 销售首页
    test_page(page, f"{BASE_URL}/sales/", "销售首页", "销售")

    # 5.2 新建销售订单
    test_page(page, f"{BASE_URL}/sales/orders/new", "新建销售订单页面")

    # 5.3 新建销售订单 (CRUD)
    try:
        ts = int(time.time())
        page.goto(f"{BASE_URL}/sales/orders/new", wait_until="networkidle", timeout=15000)
        customer_select = page.locator("select[name='customer_id'], select[name='customer'], #customer_id")
        if customer_select.count() > 0:
            customer_select.first.select_option(index=1)
        warehouse_select = page.locator("select[name='warehouse_id'], select[name='warehouse'], #warehouse_id")
        if warehouse_select.count() > 0:
            warehouse_select.first.select_option(index=1)

        add_item_btn = page.locator("button:has-text('添加'), .add-item, #add_item")
        if add_item_btn.count() > 0:
            add_item_btn.first.click()
            time.sleep(0.5)

        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle", timeout=10000)
        results.ok("新建销售订单(CRUD)")
    except Exception as e:
        results.fail("新建销售订单(CRUD)", str(e)[:300])

    # 5.4 销售退货列表
    test_page(page, f"{BASE_URL}/sales/returns", "销售退货列表页面")

    # 5.5 新建出库单
    test_page(page, f"{BASE_URL}/sales/stock-outs/new", "新建出库单页面")


def test_inventory_module(page):
    """测试库存管理模块"""
    print("\n--- 6. 库存管理模块测试 ---")

    # 6.1 库存首页
    test_page(page, f"{BASE_URL}/inventory/", "库存首页", "库存")

    # 6.2 商品库存列表
    test_page(page, f"{BASE_URL}/inventory/products", "商品库存列表页面")

    # 6.3 库存日志
    test_page(page, f"{BASE_URL}/inventory/logs", "库存日志页面")

    # 6.4 库存盘点
    test_page(page, f"{BASE_URL}/inventory/stock-check", "库存盘点页面")

    # 6.5 库存调拨
    test_page(page, f"{BASE_URL}/inventory/stock-transfer", "库存调拨页面")

    # 6.6 库存调整
    test_page(page, f"{BASE_URL}/inventory/stock-adjust", "库存调整页面")


def test_finance_module(page):
    """测试财务管理模块"""
    print("\n--- 7. 财务管理模块测试 ---")

    # 7.1 财务首页
    test_page(page, f"{BASE_URL}/finance/", "财务首页", "财务")

    # 7.2 收款列表
    test_page(page, f"{BASE_URL}/finance/receipts", "收款列表页面")

    # 7.3 新建收款
    test_page(page, f"{BASE_URL}/finance/receipt/add", "新建收款页面")

    # 7.4 付款列表
    test_page(page, f"{BASE_URL}/finance/payments", "付款列表页面")

    # 7.5 新建付款
    test_page(page, f"{BASE_URL}/finance/payment/add", "新建付款页面")

    # 7.6 费用列表
    test_page(page, f"{BASE_URL}/finance/expenses", "费用列表页面")

    # 7.7 新建费用
    test_page(page, f"{BASE_URL}/finance/expense/add", "新建费用页面")

    # 7.8 利润分析
    test_page(page, f"{BASE_URL}/finance/profit-analysis", "利润分析页面")

    # 7.9 应收应付搜索
    test_page(page, f"{BASE_URL}/finance/ar-ap-search", "应收应付搜索页面")


def test_report_module(page):
    """测试报表模块"""
    print("\n--- 8. 报表模块测试 ---")

    # 8.1 报表首页
    test_page(page, f"{BASE_URL}/report/", "报表首页", "报表")

    # 8.2 日报
    test_page(page, f"{BASE_URL}/report/daily-report", "日报页面")

    # 8.3 库存报表
    test_page(page, f"{BASE_URL}/report/inventory-report", "库存报表页面")

    # 8.4 销售排行
    test_page(page, f"{BASE_URL}/report/sales-ranking", "销售排行页面")

    # 8.5 客户统计
    test_page(page, f"{BASE_URL}/report/customer-statistics", "客户统计页面")

    # 8.6 供应商统计
    test_page(page, f"{BASE_URL}/report/supplier-statistics", "供应商统计页面")


def test_system_module(page):
    """测试系统管理模块"""
    print("\n--- 9. 系统管理模块测试 ---")

    # 9.1 系统首页
    test_page(page, f"{BASE_URL}/system/", "系统首页")

    # 9.2 用户管理
    test_page(page, f"{BASE_URL}/system/users", "用户管理页面")

    # 9.3 系统日志
    test_page(page, f"{BASE_URL}/system/logs", "系统日志页面")

    # 9.4 数据备份
    test_page(page, f"{BASE_URL}/system/backup", "数据备份页面")

    # 9.5 系统设置
    test_page(page, f"{BASE_URL}/system/settings", "系统设置页面")

    # 9.6 系统信息API
    try:
        resp = page.goto(f"{BASE_URL}/system/api/system-info", wait_until="networkidle", timeout=10000)
        if resp and resp.status == 200:
            results.ok("系统信息API")
        else:
            results.fail("系统信息API", f"HTTP {resp.status if resp else 'None'}")
    except Exception as e:
        results.fail("系统信息API", str(e)[:200])

    # 9.7 修改密码页面
    try:
        page.goto(f"{BASE_URL}/auth/profile", wait_until="networkidle", timeout=15000)
        # Try to find change password form/link
        change_pwd = page.locator("a:has-text('修改密码'), a:has-text('密码'), button:has-text('修改密码')")
        if change_pwd.count() > 0:
            change_pwd.first.click()
            page.wait_for_load_state("networkidle", timeout=5000)
            results.ok("修改密码页面")
        else:
            results.warn("修改密码页面", "未找到修改密码入口")
    except Exception as e:
        results.fail("修改密码页面", str(e)[:200])


def test_logout(page):
    """测试登出"""
    print("\n--- 10. 登出测试 ---")
    try:
        page.goto(f"{BASE_URL}/auth/profile", wait_until="networkidle", timeout=15000)
        # Click logout button/link
        logout_btn = page.locator("a:has-text('退出'), a:has-text('注销'), button:has-text('退出'), form[action*='logout'] button, a[href*='logout']")
        if logout_btn.count() > 0:
            logout_btn.first.click()
            page.wait_for_load_state("networkidle", timeout=5000)
            # After logout, should redirect to login
            if '/auth/login' in page.url or '/login' in page.url:
                results.ok("登出功能")
            else:
                results.warn("登出功能", f"登出后URL: {page.url}")
        else:
            results.warn("登出功能", "未找到登出按钮")
    except Exception as e:
        results.fail("登出功能", str(e)[:200])


def test_error_pages(page):
    """测试错误页面处理"""
    print("\n--- 11. 错误页面测试 ---")

    # 11.1 访问不存在的页面
    try:
        resp = page.goto(f"{BASE_URL}/nonexistent-page-12345", wait_until="networkidle", timeout=10000)
        if resp:
            status = resp.status
            if status == 404:
                results.ok("404页面处理")
            elif status in (301, 302):
                # Redirect to some valid page is also OK
                results.ok("404页面处理(重定向)")
            else:
                results.warn("404页面处理", f"HTTP {status}")
    except Exception as e:
        results.fail("404页面处理", str(e)[:200])

    # 11.2 访问不存在的商品ID
    try:
        resp = page.goto(f"{BASE_URL}/product/products/99999", wait_until="networkidle", timeout=10000)
        if resp:
            status = resp.status
            if status in (404, 302):
                results.ok("不存在商品ID处理")
            else:
                results.warn("不存在商品ID处理", f"HTTP {status}")
    except Exception as e:
        results.fail("不存在商品ID处理", str(e)[:200])

    # 11.3 未登录访问受保护页面
    try:
        # First logout
        page.goto(f"{BASE_URL}/auth/login", wait_until="networkidle", timeout=10000)
        # Try accessing protected page without login
        resp = page.goto(f"{BASE_URL}/product/", wait_until="networkidle", timeout=10000)
        if resp:
            if '/auth/login' in page.url:
                results.ok("未登录访问受保护页面(重定向到登录)")
            elif resp.status in (301, 302):
                results.ok("未登录访问受保护页面")
            else:
                results.warn("未登录访问受保护页面", f"HTTP {resp.status}, URL: {page.url}")
    except Exception as e:
        results.fail("未登录访问受保护页面", str(e)[:200])


def test_js_console_errors(page):
    """检查JS控制台错误"""
    print("\n--- 12. JavaScript控制台错误检查 ---")
    try:
        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

        # Visit main pages
        main_pages = [
            f"{BASE_URL}/product/",
            f"{BASE_URL}/purchase/",
            f"{BASE_URL}/sales/",
            f"{BASE_URL}/inventory/",
            f"{BASE_URL}/finance/",
            f"{BASE_URL}/report/",
            f"{BASE_URL}/system/",
        ]
        for url in main_pages:
            try:
                page.goto(url, wait_until="networkidle", timeout=10000)
                time.sleep(1)
            except:
                pass

        if errors:
            unique_errors = list(set(errors))
            for err in unique_errors[:10]:
                results.warn("JS控制台错误", err[:200])
        else:
            results.ok("JavaScript控制台无错误")
    except Exception as e:
        results.fail("JavaScript控制台错误检查", str(e)[:200])


def capture_screenshots(page):
    """为每个主要页面截图"""
    print("\n--- 截图保存 ---")
    screenshot_dir = "/home/z/my-project/download/test_screenshots"
    import os
    os.makedirs(screenshot_dir, exist_ok=True)

    pages_to_capture = [
        ("login", f"{BASE_URL}/auth/login"),
        ("product_list", f"{BASE_URL}/product/"),
        ("category_list", f"{BASE_URL}/product/categories"),
        ("supplier_list", f"{BASE_URL}/partner/suppliers"),
        ("customer_list", f"{BASE_URL}/partner/customers"),
        ("warehouse_list", f"{BASE_URL}/partner/warehouses"),
        ("purchase_index", f"{BASE_URL}/purchase/"),
        ("sales_index", f"{BASE_URL}/sales/"),
        ("inventory_index", f"{BASE_URL}/inventory/"),
        ("finance_index", f"{BASE_URL}/finance/"),
        ("report_index", f"{BASE_URL}/report/"),
        ("system_index", f"{BASE_URL}/system/"),
    ]

    login(page)  # Make sure we're logged in
    for name, url in pages_to_capture:
        try:
            page.goto(url, wait_until="networkidle", timeout=10000)
            page.screenshot(path=f"{screenshot_dir}/{name}.png", full_page=True)
            print(f"  📸 {name}.png saved")
        except Exception as e:
            print(f"  ❌ {name} screenshot failed: {str(e)[:100]}")


def main():
    print("="*60)
    print("my-jxc 进销存管理系统 - 全面功能测试")
    print(f"目标地址: {BASE_URL}")
    print("="*60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # Collect JS errors
        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)

        try:
            # Run all tests
            test_auth_module(page)
            test_product_module(page)
            test_partner_module(page)
            test_purchase_module(page)
            test_sales_module(page)
            test_inventory_module(page)
            test_finance_module(page)
            test_report_module(page)
            test_system_module(page)
            test_logout(page)

            # Re-login for additional tests
            login(page)
            test_error_pages(page)
            test_js_console_errors(page)

            # Capture screenshots
            capture_screenshots(page)

        except Exception as e:
            print(f"\n💥 测试运行异常: {e}")
            traceback.print_exc()

        finally:
            context.close()
            browser.close()

    all_passed = results.summary()
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
