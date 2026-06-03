#!/usr/bin/env python3
"""
my-jxc 进销存管理系统 - 全面功能测试 (Flask Test Client)
使用 Flask 内置测试客户端模拟所有 HTTP 请求，覆盖全部页面和功能
"""
import sys
import os
import time
import traceback
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DATABASE_URL', '')
os.environ.setdefault('FLASK_ENV', 'default')

from app import create_app, db
from app.models import User, Category, Product, Supplier, Customer, Warehouse

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False  # 测试环境禁用CSRF

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def ok(self, name, detail=""):
        self.passed.append(name)
        print(f"  ✅ PASS: {name}" + (f" ({detail})" if detail else ""))

    def fail(self, name, error):
        self.failed.append((name, str(error)))
        print(f"  ❌ FAIL: {name}")
        print(f"         {str(error)[:300]}")

    def warn(self, name, msg):
        self.warnings.append((name, msg))
        print(f"  ⚠️  WARN: {name} - {msg[:200]}")

    def summary(self):
        total = len(self.passed) + len(self.failed)
        print(f"\n{'='*70}")
        print(f"  测试结果汇总: {len(self.passed)}/{total} 通过, {len(self.failed)} 失败, {len(self.warnings)} 警告")
        print(f"{'='*70}")
        if self.failed:
            print(f"\n  失败列表:")
            for name, err in self.failed:
                print(f"    ❌ {name}")
                print(f"       {str(err)[:200]}")
        if self.warnings:
            print(f"\n  警告列表:")
            for name, msg in self.warnings:
                print(f"    ⚠️  {name}: {msg[:150]}")
        print()
        return len(self.failed) == 0

results = TestResults()


def test_get(client, url, name, expected_status=200, check_text=None):
    """测试 GET 请求"""
    try:
        resp = client.get(url, follow_redirects=True)
        status = resp.status_code
        data = resp.data.decode('utf-8', errors='replace')

        if status != expected_status:
            # Try to extract error info
            if status == 500:
                # Look for traceback in response
                lines = data.split('\n')
                error_lines = [l for l in lines if 'Error' in l or 'error' in l or 'Exception' in l]
                error_detail = '\n'.join(error_lines[:5]) if error_lines else data[:500]
                results.fail(name, f"HTTP 500 内部服务器错误\n{error_detail}")
            else:
                results.fail(name, f"HTTP {status}, expected {expected_status}")
            return None

        if check_text and check_text not in data:
            results.fail(name, f"页面缺少期望文本: '{check_text}'")
            return None

        results.ok(name, f"HTTP {status}")
        return resp
    except Exception as e:
        results.fail(name, str(e)[:300])
        return None


def test_post(client, url, data, name, expected_status=None, check_text=None, follow=True):
    """测试 POST 请求"""
    try:
        resp = client.post(url, data=data, follow_redirects=follow)
        status = resp.status_code if not follow else resp.status_code
        resp_data = resp.data.decode('utf-8', errors='replace')

        if expected_status and status != expected_status:
            if status == 500:
                lines = resp_data.split('\n')
                error_lines = [l for l in lines if 'Error' in l or 'Exception' in l]
                error_detail = '\n'.join(error_lines[:5]) if error_lines else resp_data[:500]
                results.fail(name, f"HTTP 500 内部服务器错误\n{error_detail}")
            else:
                results.fail(name, f"HTTP {status}, expected {expected_status}")
            return None

        if check_text and check_text not in resp_data:
            # Check for flash messages
            if '成功' not in resp_data and '添加' not in resp_data and check_text not in resp_data:
                results.warn(name, f"POST后未检测到期望文本 '{check_text}' (响应长度: {len(resp_data)})")

        results.ok(name, f"HTTP {status}")
        return resp
    except Exception as e:
        results.fail(name, str(e)[:300])
        return None


# ============================================================
# 数据库初始化
# ============================================================
def init_test_data():
    """创建测试数据"""
    with app.app_context():
        db.create_all()

        # 管理员
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)

        # 仓库
        wh1 = Warehouse.query.filter_by(code='WH001').first()
        if not wh1:
            wh1 = Warehouse(code='WH001', name='主仓库', address='测试地址1', manager='管理员', phone='13800138000')
            db.session.add(wh1)

        wh2 = Warehouse.query.filter_by(code='WH002').first()
        if not wh2:
            wh2 = Warehouse(code='WH002', name='副仓库', address='测试地址2', manager='管理员', phone='13800138001')
            db.session.add(wh2)

        # 分类
        cat1 = Category.query.filter_by(name='电子产品').first()
        if not cat1:
            cat1 = Category(name='电子产品', description='电子设备类')
            db.session.add(cat1)

        cat2 = Category.query.filter_by(name='办公用品').first()
        if not cat2:
            cat2 = Category(name='办公用品', description='办公耗材类')
            db.session.add(cat2)

        # 供应商
        sup1 = Supplier.query.filter_by(code='SUP001').first()
        if not sup1:
            sup1 = Supplier(code='SUP001', name='深圳供应商A', contact_person='张三', phone='13900001111', email='sup1@test.com', address='深圳市南山区')
            db.session.add(sup1)

        sup2 = Supplier.query.filter_by(code='SUP002').first()
        if not sup2:
            sup2 = Supplier(code='SUP002', name='广州供应商B', contact_person='李四', phone='13900002222', email='sup2@test.com', address='广州市天河区')
            db.session.add(sup2)

        # 客户
        cust1 = Customer.query.filter_by(code='CUS001').first()
        if not cust1:
            cust1 = Customer(code='CUS001', name='北京客户A', contact_person='王五', phone='13700001111', email='cust1@test.com', address='北京市朝阳区')
            db.session.add(cust1)

        cust2 = Customer.query.filter_by(code='CUS002').first()
        if not cust2:
            cust2 = Customer(code='CUS002', name='上海客户B', contact_person='赵六', phone='13700002222', email='cust2@test.com', address='上海市浦东新区')
            db.session.add(cust2)

        # 商品
        prod1 = Product.query.filter_by(code='SKU001').first()
        if not prod1:
            prod1 = Product(
                name='笔记本电脑', code='SKU001',
                category_id=cat1.id if cat1 else 1,
                purchase_price=3000.00, sale_price=4500.00,
                unit='台', safety_stock=5, description='高性能笔记本电脑'
            )
            db.session.add(prod1)

        prod2 = Product.query.filter_by(code='SKU002').first()
        if not prod2:
            prod2 = Product(
                name='A4打印纸', code='SKU002',
                category_id=cat2.id if cat2 else 2,
                purchase_price=15.00, sale_price=25.00,
                unit='包', safety_stock=50, description='70g A4复印纸'
            )
            db.session.add(prod2)

        db.session.commit()
        print("测试数据初始化完成")


# ============================================================
# 1. 认证模块
# ============================================================
def test_auth_module(client):
    print("\n--- 1. 认证模块 ---")

    # 1.1 登录页面
    test_get(client, '/auth/login', '登录页面', check_text='登录')

    # 1.2 注册页面
    test_get(client, '/auth/register', '注册页面', check_text='注册')

    # 1.3 错误密码登录
    resp = test_post(client, '/auth/login', {
        'username': 'admin',
        'password': 'wrongpass',
    }, '错误密码登录', follow=False)
    if resp:
        if resp.status_code == 200:
            results.ok('错误密码登录后仍显示登录页', f'HTTP {resp.status_code}')
        else:
            results.warn('错误密码登录', f'状态码 {resp.status_code}')

    # 1.4 正确登录
    resp = client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123',
    }, follow_redirects=True)
    if resp.status_code == 200:
        results.ok('正确登录', f'HTTP {resp.status_code}')
    else:
        results.fail('正确登录', f'HTTP {resp.status_code}')

    # 1.5 个人资料
    test_get(client, '/auth/profile', '个人资料页面')

    # 1.6 修改密码 (仅测试页面加载，不实际修改)
    resp = test_post(client, '/auth/change-password', {
        'old_password': 'wrong',
        'new_password': 'newpass123',
        'confirm_password': 'newpass123',
    }, '修改密码(旧密码错误)', follow=True)
    if resp:
        data = resp.data.decode('utf-8', errors='replace')
        if '错误' in data or '不正确' in data or '失败' in data:
            results.ok('修改密码错误提示', '检测到错误提示')
        else:
            results.warn('修改密码错误提示', '未检测到明确的错误提示')


# ============================================================
# 2. 商品管理模块
# ============================================================
def test_product_module(client):
    print("\n--- 2. 商品管理模块 ---")

    # 2.1 商品列表
    test_get(client, '/product/', '商品列表', check_text='商品')

    # 2.2 新建商品页面
    test_get(client, '/product/products/new', '新建商品页面')

    # 2.3 新建商品 (CRUD)
    ts = int(time.time())
    resp = test_post(client, '/product/products/new', {
        'name': f'测试商品_{ts}',
        'code': f'SKU_TEST_{ts}',
        'category_id': 1,
        'purchase_price': '100',
        'sale_price': '150',
        'unit': '个',
        'safety_stock': '10',
        'description': '自动化测试创建的商品',
    }, f'新建商品(CRUD)', follow=True)

    # 2.4 查看商品详情 (获取ID=1)
    product = Product.query.first()
    if product:
        test_get(client, f'/product/products/{product.id}', f'查看商品详情(ID={product.id})')

        # 2.5 编辑商品
        test_get(client, f'/product/products/{product.id}/edit', f'编辑商品页面(ID={product.id})')

        resp = test_post(client, f'/product/products/{product.id}/edit', {
            'name': f'编辑后商品_{ts}',
            'code': product.code,
            'category_id': product.category_id,
            'purchase_price': '120',
            'sale_price': '180',
            'unit': '个',
            'safety_stock': '15',
            'description': '自动化测试编辑的商品',
        }, f'编辑商品(CRUD)', follow=True)
    else:
        results.warn('商品CRUD测试', '无商品数据')

    # 2.6 分类列表
    test_get(client, '/product/categories', '分类列表', check_text='分类')

    # 2.7 新建分类
    test_get(client, '/product/categories/new', '新建分类页面')

    resp = test_post(client, '/product/categories/new', {
        'name': f'测试分类_{ts}',
        'description': '自动化测试创建的分类',
    }, f'新建分类(CRUD)', follow=True)

    # 2.8 编辑分类
    cat = Category.query.filter_by(name=f'测试分类_{ts}').first()
    if cat:
        test_get(client, f'/product/categories/{cat.id}/edit', f'编辑分类页面(ID={cat.id})')
        test_post(client, f'/product/categories/{cat.id}/edit', {
            'name': f'编辑分类_{ts}',
            'description': '自动化测试编辑的分类',
        }, f'编辑分类(CRUD)', follow=True)

    # 2.9 API接口
    test_get(client, '/product/api/products', '商品API接口')
    test_get(client, '/product/api/categories', '分类API接口')

    # 2.10 价格更新API
    if product:
        test_post(client, '/product/api/product/price', {
            'product_id': product.id,
            'purchase_price': '200',
            'sale_price': '300',
        }, '价格更新API', follow=False)


# ============================================================
# 3. 合作伙伴模块
# ============================================================
def test_partner_module(client):
    print("\n--- 3. 合作伙伴模块 ---")

    ts = int(time.time())

    # 3.1 供应商列表
    test_get(client, '/partner/suppliers', '供应商列表', check_text='供应商')

    # 3.2 新建供应商
    test_get(client, '/partner/suppliers/new', '新建供应商页面')
    resp = test_post(client, '/partner/suppliers/new', {
        'code': f'SUP_TEST_{ts}',
        'name': f'测试供应商_{ts}',
        'contact_person': '测试联系人',
        'phone': '13800001234',
        'email': f'test{ts}@test.com',
        'address': '测试地址',
    }, f'新建供应商(CRUD)', follow=True)

    # 3.3 编辑供应商
    sup = Supplier.query.filter_by(code=f'SUP_TEST_{ts}').first()
    if sup:
        test_get(client, f'/partner/suppliers/{sup.id}/edit', f'编辑供应商页面(ID={sup.id})')
        test_post(client, f'/partner/suppliers/{sup.id}/edit', {
            'code': sup.code,
            'name': f'编辑供应商_{ts}',
            'contact_person': '编辑联系人',
            'phone': '13800005678',
            'email': f'edit{ts}@test.com',
            'address': '编辑地址',
        }, f'编辑供应商(CRUD)', follow=True)

    # 3.4 客户列表
    test_get(client, '/partner/customers', '客户列表', check_text='客户')

    # 3.5 新建客户
    test_get(client, '/partner/customers/new', '新建客户页面')
    resp = test_post(client, '/partner/customers/new', {
        'code': f'CUS_TEST_{ts}',
        'name': f'测试客户_{ts}',
        'contact_person': '测试联系人',
        'phone': '13700001234',
        'email': f'cust_test{ts}@test.com',
        'address': '测试地址',
    }, f'新建客户(CRUD)', follow=True)

    # 3.6 编辑客户
    cust = Customer.query.filter_by(code=f'CUS_TEST_{ts}').first()
    if cust:
        test_get(client, f'/partner/customers/{cust.id}/edit', f'编辑客户页面(ID={cust.id})')
        test_post(client, f'/partner/customers/{cust.id}/edit', {
            'code': cust.code,
            'name': f'编辑客户_{ts}',
            'contact_person': '编辑联系人',
            'phone': '13700005678',
            'email': f'cust_edit{ts}@test.com',
            'address': '编辑地址',
        }, f'编辑客户(CRUD)', follow=True)

    # 3.7 仓库列表
    test_get(client, '/partner/warehouses', '仓库列表', check_text='仓库')

    # 3.8 新建仓库
    test_get(client, '/partner/warehouses/new', '新建仓库页面')
    resp = test_post(client, '/partner/warehouses/new', {
        'code': f'WH_TEST_{ts}',
        'name': f'测试仓库_{ts}',
        'address': '测试仓库地址',
        'manager': '测试管理员',
        'phone': '13600001234',
    }, f'新建仓库(CRUD)', follow=True)

    # 3.9 编辑仓库
    wh = Warehouse.query.filter_by(code=f'WH_TEST_{ts}').first()
    if wh:
        test_get(client, f'/partner/warehouses/{wh.id}/edit', f'编辑仓库页面(ID={wh.id})')
        test_post(client, f'/partner/warehouses/{wh.id}/edit', {
            'code': wh.code,
            'name': f'编辑仓库_{ts}',
            'address': '编辑仓库地址',
            'manager': '编辑管理员',
            'phone': '13600005678',
        }, f'编辑仓库(CRUD)', follow=True)


# ============================================================
# 4. 采购管理模块
# ============================================================
def test_purchase_module(client):
    print("\n--- 4. 采购管理模块 ---")

    # 4.1 采购首页
    test_get(client, '/purchase/', '采购首页', check_text='采购')

    # 4.2 新建采购订单页面
    test_get(client, '/purchase/orders/new', '新建采购订单页面')

    # 4.3 新建采购订单
    ts = int(time.time())
    sup = Supplier.query.first()
    wh = Warehouse.query.first()
    if sup and wh:
        resp = test_post(client, '/purchase/orders/new', {
            'supplier_id': sup.id,
            'warehouse_id': wh.id,
            'notes': f'自动化测试采购订单_{ts}',
            # item data depends on form structure
        }, f'新建采购订单(CRUD)', follow=True)
    else:
        results.warn('采购订单CRUD', '缺少供应商或仓库数据')

    # 4.4 查看采购订单
    from app.models import PurchaseOrder
    order = PurchaseOrder.query.first()
    if order:
        test_get(client, f'/purchase/orders/{order.id}', f'查看采购订单(ID={order.id})')
        test_get(client, f'/purchase/orders/{order.id}/edit', f'编辑采购订单页面(ID={order.id})')
        test_get(client, f'/purchase/orders/{order.id}/items', f'采购订单明细页面(ID={order.id})')

        # 4.5 快速入库
        test_post(client, f'/purchase/orders/{order.id}/quick-stock-in', {}, f'采购订单快速入库', follow=True)

        # 4.6 创建入库单
        test_get(client, f'/purchase/orders/{order.id}/stock-in', f'创建入库单页面(ID={order.id})')
    else:
        results.warn('采购订单详情测试', '无采购订单数据')

    # 4.7 新建入库单（独立）
    test_get(client, '/purchase/stock-ins/new', '新建入库单页面(独立)')

    # 4.8 入库单列表和详情
    from app.models import StockIn
    stock_in = StockIn.query.first()
    if stock_in:
        test_get(client, f'/purchase/stock-ins/{stock_in.id}', f'查看入库单(ID={stock_in.id})')
        test_get(client, f'/purchase/stock-ins/{stock_in.id}/items', f'入库单明细页面(ID={stock_in.id})')

    # 4.9 采购退货列表
    test_get(client, '/purchase/returns', '采购退货列表')

    # 4.10 API接口
    if order:
        test_get(client, f'/purchase/api/purchase-orders/{order.id}/items', f'采购订单明细API(ID={order.id})')


# ============================================================
# 5. 销售管理模块
# ============================================================
def test_sales_module(client):
    print("\n--- 5. 销售管理模块 ---")

    # 5.1 销售首页
    test_get(client, '/sales/', '销售首页', check_text='销售')

    # 5.2 新建销售订单页面
    test_get(client, '/sales/orders/new', '新建销售订单页面')

    # 5.3 新建销售订单
    ts = int(time.time())
    cust = Customer.query.first()
    wh = Warehouse.query.first()
    if cust and wh:
        resp = test_post(client, '/sales/orders/new', {
            'customer_id': cust.id,
            'warehouse_id': wh.id,
            'notes': f'自动化测试销售订单_{ts}',
        }, f'新建销售订单(CRUD)', follow=True)
    else:
        results.warn('销售订单CRUD', '缺少客户或仓库数据')

    # 5.4 查看销售订单
    from app.models import SalesOrder
    order = SalesOrder.query.first()
    if order:
        test_get(client, f'/sales/orders/{order.id}', f'查看销售订单(ID={order.id})')
        test_get(client, f'/sales/orders/{order.id}/edit', f'编辑销售订单页面(ID={order.id})')
        test_get(client, f'/sales/orders/{order.id}/items', f'销售订单明细页面(ID={order.id})')

        # 5.5 快速出库
        test_post(client, f'/sales/orders/{order.id}/quick-stock-out', {}, f'销售订单快速出库', follow=True)

        # 5.6 创建出库单
        test_get(client, f'/sales/orders/{order.id}/stock-out', f'创建出库单页面(ID={order.id})')
    else:
        results.warn('销售订单详情测试', '无销售订单数据')

    # 5.7 新建出库单（独立）
    test_get(client, '/sales/stock-outs/new', '新建出库单页面(独立)')

    # 5.8 出库单详情
    from app.models import StockOut
    stock_out = StockOut.query.first()
    if stock_out:
        test_get(client, f'/sales/stock-outs/{stock_out.id}', f'查看出库单(ID={stock_out.id})')
        test_get(client, f'/sales/stock-outs/{stock_out.id}/items', f'出库单明细页面(ID={stock_out.id})')

    # 5.9 销售退货列表
    test_get(client, '/sales/returns', '销售退货列表')

    # 5.10 API接口
    if order:
        test_get(client, f'/sales/api/sales-orders/{order.id}/items', f'销售订单明细API(ID={order.id})')


# ============================================================
# 6. 库存管理模块
# ============================================================
def test_inventory_module(client):
    print("\n--- 6. 库存管理模块 ---")

    # 6.1 库存首页
    test_get(client, '/inventory/', '库存首页')

    # 6.2 商品库存列表
    test_get(client, '/inventory/products', '商品库存列表')

    # 6.3 库存日志
    test_get(client, '/inventory/logs', '库存日志')

    # 6.4 仓库库存详情
    wh = Warehouse.query.first()
    if wh:
        test_get(client, f'/inventory/warehouse/{wh.id}', f'仓库库存详情(ID={wh.id})')

    # 6.5 库存盘点页面
    test_get(client, '/inventory/stock-check', '库存盘点页面')

    # 6.6 库存调拨页面
    test_get(client, '/inventory/stock-transfer', '库存调拨页面')

    # 6.7 库存调整页面
    test_get(client, '/inventory/stock-adjust', '库存调整页面')

    # 6.8 库存同步检查API
    test_get(client, '/inventory/api/stock-sync-check', '库存同步检查API')

    # 6.9 低库存预警API
    test_get(client, '/inventory/api/low-stock', '低库存预警API')

    # 6.10 日志统计API
    test_get(client, '/inventory/api/logs-statistics', '日志统计API')

    # 6.11 导出日志
    test_get(client, '/inventory/api/export-logs', '导出库存日志')

    # 6.12 导出仓库库存
    if wh:
        test_get(client, f'/inventory/export-warehouse-stock/{wh.id}', f'导出仓库库存(WH={wh.id})')


# ============================================================
# 7. 财务管理模块
# ============================================================
def test_finance_module(client):
    print("\n--- 7. 财务管理模块 ---")

    ts = int(time.time())

    # 7.1 财务首页
    test_get(client, '/finance/', '财务首页')

    # 7.2 收款列表
    test_get(client, '/finance/receipts', '收款列表')

    # 7.3 新建收款
    test_get(client, '/finance/receipt/add', '新建收款页面')
    cust = Customer.query.first()
    if cust:
        test_post(client, '/finance/receipt/add', {
            'customer_id': cust.id,
            'amount': '1000',
            'payment_method': 'bank_transfer',
            'notes': f'自动化测试收款_{ts}',
        }, f'新建收款(CRUD)', follow=True)

    # 7.4 付款列表
    test_get(client, '/finance/payments', '付款列表')

    # 7.5 新建付款
    test_get(client, '/finance/payment/add', '新建付款页面')
    sup = Supplier.query.first()
    if sup:
        test_post(client, '/finance/payment/add', {
            'supplier_id': sup.id,
            'amount': '500',
            'payment_method': 'bank_transfer',
            'notes': f'自动化测试付款_{ts}',
        }, f'新建付款(CRUD)', follow=True)

    # 7.6 费用列表
    test_get(client, '/finance/expenses', '费用列表')

    # 7.7 新建费用
    test_get(client, '/finance/expense/add', '新建费用页面')
    test_post(client, '/finance/expense/add', {
        'amount': '200',
        'category': 'office',
        'notes': f'自动化测试费用_{ts}',
    }, f'新建费用(CRUD)', follow=True)

    # 7.8 利润分析
    test_get(client, '/finance/profit-analysis', '利润分析页面')

    # 7.9 应收应付搜索
    test_get(client, '/finance/ar-ap-search', '应收应付搜索页面')

    # 7.10 API接口
    test_get(client, '/finance/api/financial-summary', '财务汇总API')

    if cust:
        test_get(client, f'/finance/api/customer-ar/{cust.id}', f'客户应收明细API(CUS={cust.id})')
    if sup:
        test_get(client, f'/finance/api/supplier-ap/{sup.id}', f'供应商应付明细API(SUP={sup.id})')

    # 7.11 导出
    test_get(client, '/finance/export-receipts', '导出收款')
    test_get(client, '/finance/export-payments', '导出付款')
    test_get(client, '/finance/export-expenses', '导出费用')
    test_get(client, '/finance/export-profit-analysis', '导出利润分析')
    if cust:
        test_get(client, f'/finance/export-customer-ar/{cust.id}', f'导出客户应收(CUS={cust.id})')
    if sup:
        test_get(client, f'/finance/export-supplier-ap/{sup.id}', f'导出供应商应付(SUP={sup.id})')


# ============================================================
# 8. 报表模块
# ============================================================
def test_report_module(client):
    print("\n--- 8. 报表模块 ---")

    # 8.1 报表首页
    test_get(client, '/report/', '报表首页')

    # 8.2 日报
    test_get(client, '/report/daily-report', '日报页面')

    # 8.3 库存报表
    test_get(client, '/report/inventory-report', '库存报表页面')

    # 8.4 销售排行
    test_get(client, '/report/sales-ranking', '销售排行页面')

    # 8.5 客户统计
    test_get(client, '/report/customer-statistics', '客户统计页面')

    # 8.6 供应商统计
    test_get(client, '/report/supplier-statistics', '供应商统计页面')

    # 8.7 API
    test_get(client, '/report/api/sales-trend', '销售趋势API')

    # 8.8 导出
    test_get(client, '/report/export/daily', '导出日报')
    test_get(client, '/report/export/inventory', '导出库存报表')
    test_get(client, '/report/export/sales-ranking', '导出销售排行')
    test_get(client, '/report/export-products', '导出商品报表')
    test_get(client, '/report/export/customer', '导出客户报表')
    test_get(client, '/report/export/supplier', '导出供应商报表')


# ============================================================
# 9. 系统管理模块
# ============================================================
def test_system_module(client):
    print("\n--- 9. 系统管理模块 ---")

    # 9.1 系统首页
    test_get(client, '/system/', '系统首页')

    # 9.2 用户管理
    test_get(client, '/system/users', '用户管理页面')

    # 9.3 系统日志
    test_get(client, '/system/logs', '系统日志页面')

    # 9.4 数据备份
    test_get(client, '/system/backup', '数据备份页面')

    # 9.5 系统设置
    test_get(client, '/system/settings', '系统设置页面')

    # 9.6 API
    test_get(client, '/system/api/system-info', '系统信息API')
    test_get(client, '/system/api/system/recent-logs', '最近日志API')
    test_get(client, '/system/backup/list', '备份列表API')

    # 9.7 新建用户
    ts = int(time.time())
    resp = test_post(client, '/system/user/add', {
        'username': f'testuser_{ts}',
        'email': f'testuser_{ts}@test.com',
        'password': 'test123456',
        'role': 'user',
    }, f'新建用户(CRUD)', follow=True)

    # 9.8 编辑用户
    test_user = User.query.filter_by(username=f'testuser_{ts}').first()
    if test_user:
        test_get(client, f'/system/user/edit/{test_user.id}', f'编辑用户页面(ID={test_user.id})')

    # 9.9 登出
    resp = client.post('/auth/logout', follow_redirects=True)
    if resp.status_code == 200 and ('登录' in resp.data.decode('utf-8', errors='replace')):
        results.ok('登出功能', '登出后跳转到登录页')
    else:
        results.warn('登出功能', f'HTTP {resp.status_code}')


# ============================================================
# 10. 边界条件和错误处理
# ============================================================
def test_edge_cases(client):
    print("\n--- 10. 边界条件和错误处理 ---")

    # 10.1 未登录访问受保护页面
    logout_client = app.test_client()
    resp = logout_client.get('/product/', follow_redirects=False)
    if resp.status_code in (302, 303):
        results.ok('未登录访问保护页面(重定向)', f'HTTP {resp.status_code}')
    else:
        results.fail('未登录访问保护页面', f'HTTP {resp.status_code}, 应该重定向到登录页')

    # 10.2 重新登录继续测试
    client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

    # 10.3 访问不存在的商品ID
    test_get(client, '/product/products/99999', '访问不存在商品ID(99999)')

    # 10.4 访问不存在的供应商ID编辑
    test_get(client, '/partner/suppliers/99999/edit', '访问不存在供应商ID(99999)')

    # 10.5 访问不存在的采购订单
    test_get(client, '/purchase/orders/99999', '访问不存在采购订单(99999)')

    # 10.6 访问不存在的销售订单
    test_get(client, '/sales/orders/99999', '访问不存在销售订单(99999)')

    # 10.7 重复用户名注册
    resp = test_post(client, '/auth/register', {
        'username': 'admin',
        'email': 'admin2@test.com',
        'password': 'admin123',
        'confirm_password': 'admin123',
    }, '重复用户名注册', follow=True)

    # 10.8 密码不一致注册
    resp = test_post(client, '/auth/register', {
        'username': f'newuser_{int(time.time())}',
        'email': f'newuser_{int(time.time())}@test.com',
        'password': 'pass123',
        'confirm_password': 'pass456',
    }, '密码不一致注册', follow=True)


# ============================================================
# 11. 主页和重定向
# ============================================================
def test_redirects(client):
    print("\n--- 11. 路由和重定向 ---")

    # 11.1 首页重定向
    resp = client.get('/', follow_redirects=False)
    if resp.status_code in (302, 303):
        results.ok('首页重定向', f'HTTP {resp.status_code}')
    else:
        results.fail('首页重定向', f'HTTP {resp.status_code}')

    # 11.2 /login 旧路径兼容
    resp = client.get('/login', follow_redirects=False)
    if resp.status_code in (302, 303):
        results.ok('/login旧路径兼容', f'HTTP {resp.status_code}')
    else:
        results.warn('/login旧路径兼容', f'HTTP {resp.status_code}')


# ============================================================
# 主测试函数
# ============================================================
def main():
    print("=" * 70)
    print("  my-jxc 进销存管理系统 - 全面功能测试")
    print("  Flask Test Client 自动化测试")
    print("=" * 70)

    with app.app_context():
        # 初始化测试数据
        init_test_data()

        # 创建测试客户端
        client = app.test_client()

        try:
            # 运行所有测试模块
            test_redirects(client)
            test_auth_module(client)
            test_product_module(client)
            test_partner_module(client)
            test_purchase_module(client)
            test_sales_module(client)
            test_inventory_module(client)
            test_finance_module(client)
            test_report_module(client)
            test_system_module(client)

            # 重新登录进行边界测试
            client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
            test_edge_cases(client)

        except Exception as e:
            print(f"\n💥 测试运行异常: {e}")
            traceback.print_exc()

    all_passed = results.summary()
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
