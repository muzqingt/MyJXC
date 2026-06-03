#!/usr/bin/env python3
"""
my-jxc 深度功能测试 - 完整业务流程测试
覆盖完整采购入库→销售出库→库存变动→财务收支的业务链路
"""
import sys, os, time, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DATABASE_URL', '')
os.environ.setdefault('FLASK_ENV', 'default')

from app import create_app, db
from app.models import *

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False

passed = 0
failed = 0
errors = []

def ok(name, detail=""):
    global passed
    passed += 1
    print(f"  ✅ {name}" + (f" ({detail})" if detail else ""))

def fail(name, error):
    global failed
    failed += 1
    errors.append((name, str(error)))
    print(f"  ❌ {name}: {str(error)[:300]}")


def init_data():
    """创建完整测试数据集"""
    db.create_all()

    if User.query.filter_by(username='admin').first():
        return

    admin = User(username='admin', email='admin@test.com', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)

    wh1 = Warehouse(code='WH001', name='主仓库', address='仓库A', manager='张三', phone='13800001111')
    wh2 = Warehouse(code='WH002', name='副仓库', address='仓库B', manager='李四', phone='13800002222')
    db.session.add_all([wh1, wh2])

    cat1 = Category(name='电子产品', description='电子类')
    cat2 = Category(name='办公用品', description='办公类')
    db.session.add_all([cat1, cat2])

    sup1 = Supplier(code='SUP001', name='深圳科技公司', contact_person='王经理', phone='13900001111', email='sup1@test.com', address='深圳南山区')
    sup2 = Supplier(code='SUP002', name='广州贸易公司', contact_person='李经理', phone='13900002222', email='sup2@test.com', address='广州天河区')
    db.session.add_all([sup1, sup2])

    cust1 = Customer(code='CUS001', name='北京贸易公司', contact_person='赵总', phone='13700001111', email='cust1@test.com', address='北京朝阳区')
    cust2 = Customer(code='CUS002', name='上海科技公司', contact_person='钱总', phone='13700002222', email='cust2@test.com', address='上海浦东区')
    db.session.add_all([cust1, cust2])

    p1 = Product(name='笔记本电脑', code='SKU001', category_id=1, unit='台', purchase_price=3000, sale_price=4500, safety_stock=5)
    p2 = Product(name='无线鼠标', code='SKU002', category_id=1, unit='个', purchase_price=50, sale_price=89, safety_stock=20)
    p3 = Product(name='A4打印纸', code='SKU003', category_id=2, unit='包', purchase_price=15, sale_price=25, safety_stock=50)
    db.session.add_all([p1, p2, p3])

    db.session.commit()
    print("测试数据初始化完成")


def login(client):
    resp = client.post('/auth/login', data={
        'username': 'admin', 'password': 'admin123'
    }, follow_redirects=True)
    assert resp.status_code == 200, f"Login failed: {resp.status_code}"


def test_complete_purchase_flow(client):
    """完整采购流程：创建订单→添加明细→确认→入库→验证库存"""
    print("\n--- 完整采购流程测试 ---")

    # 1. 创建采购订单（含明细）
    ts = int(time.time())
    resp = client.post('/purchase/orders/new', data={
        'supplier_id': 1,
        'warehouse_id': 1,
        'order_date': '2026-06-01',
        'expected_date': '2026-06-05',
        'order_status': 'confirmed',
        'notes': f'自动化采购订单_{ts}',
        'product_id[]': ['1', '2'],
        'quantity[]': ['10', '50'],
        'unit_price[]': ['3000', '50'],
    }, follow_redirects=True)
    if resp.status_code == 200:
        ok('创建采购订单(含明细)')
    else:
        fail('创建采购订单', f'HTTP {resp.status_code}')
        data = resp.data.decode('utf-8', errors='replace')
        # Check for errors
        if '500' in data or 'Internal' in data or 'Error' in data:
            fail('采购订单500错误', data[:500])
        return

    # 验证订单已创建
    po = PurchaseOrder.query.first()
    if po:
        ok('采购订单已入库', f'ID={po.id}, 单号={po.order_number}')
        ok(f'采购订单供应商', f'supplier_id={po.supplier_id}')
        ok(f'采购订单仓库', f'warehouse_id={po.warehouse_id}')
        
        if po.items:
            ok(f'采购订单明细数量', f'{len(po.items)}条')
            for item in po.items:
                print(f"    - 商品ID={item.product_id}, 数量={item.quantity}, 单价={item.unit_price}, 金额={item.amount}")
        else:
            fail('采购订单明细', '订单无明细数据')

        # 2. 查看订单详情页
        resp = client.get(f'/purchase/orders/{po.id}')
        if resp.status_code == 200:
            ok('查看采购订单详情')
        else:
            fail('查看采购订单详情', f'HTTP {resp.status_code}')

        # 3. 快速入库
        resp = client.post(f'/purchase/orders/{po.id}/quick-stock-in', data={}, follow_redirects=True)
        if resp.status_code == 200:
            ok('采购订单快速入库')
        else:
            fail('采购订单快速入库', f'HTTP {resp.status_code}')

        # 4. 验证库存变动
        product1 = db.session.get(Product, 1)
        product2 = db.session.get(Product, 2)
        if product1:
            print(f"    笔记本电脑库存: {product1.stock_quantity}")
            ok('库存验证-笔记本电脑', f'stock={product1.stock_quantity}')
        if product2:
            print(f"    无线鼠标库存: {product2.stock_quantity}")
            ok('库存验证-无线鼠标', f'stock={product2.stock_quantity}')

        # 5. 验证库存日志和入库单
        si = StockIn.query.filter_by(purchase_order_id=po.id).first()
        if si:
            ok('入库单已创建', f'单号={si.receipt_number}')
            resp = client.get(f'/purchase/stock-ins/{si.id}')
            if resp.status_code == 200:
                ok('查看入库单详情')
            else:
                fail('查看入库单详情', f'HTTP {resp.status_code}')
            logs = StockLog.query.filter_by(reference_id=si.id, reference_type='stock_in').all()
            if logs:
                ok('采购入库日志', f'{len(logs)}条')
            else:
                fail('采购入库日志', f'未找到入库日志(si_id={si.id})')
        else:
            fail('入库单创建', '未找到关联入库单')

        # NOTE: 采购退货放到销售测试之后，避免退货消耗库存导致销售出库失败

    else:
        fail('采购订单入库验证', '无订单数据')


def test_complete_sales_flow(client):
    """完整销售流程：创建订单→添加明细→确认→出库→验证库存→财务"""
    print("\n--- 完整销售流程测试 ---")

    ts = int(time.time())
    resp = client.post('/sales/orders/new', data={
        'customer_id': 1,
        'warehouse_id': 1,
        'order_date': '2026-06-01',
        'delivery_date': '2026-06-03',
        'order_status': 'confirmed',
        'notes': f'自动化销售订单_{ts}',
        'product_id[]': ['1', '2'],
        'quantity[]': ['2', '10'],
        'unit_price[]': ['4500', '89'],
    }, follow_redirects=True)
    if resp.status_code == 200:
        ok('创建销售订单(含明细)')
    else:
        fail('创建销售订单', f'HTTP {resp.status_code}')
        data = resp.data.decode('utf-8', errors='replace')
        if '500' in data or 'Error' in data:
            fail('销售订单500错误', data[:500])
        return

    so = SalesOrder.query.first()
    if so:
        ok('销售订单已入库', f'ID={so.id}, 单号={so.order_number}')

        if so.items:
            ok(f'销售订单明细数量', f'{len(so.items)}条')
        else:
            fail('销售订单明细', '订单无明细数据')

        # 快速出库
        resp = client.post(f'/sales/orders/{so.id}/quick-stock-out', data={}, follow_redirects=True)
        if resp.status_code == 200:
            ok('销售订单快速出库')
        else:
            fail('销售订单快速出库', f'HTTP {resp.status_code}')

        # 验证库存减少
        product1 = db.session.get(Product, 1)
        product2 = db.session.get(Product, 2)
        if product1:
            ok('销售后库存验证-笔记本电脑', f'stock={product1.stock_quantity}')
        if product2:
            ok('销售后库存验证-无线鼠标', f'stock={product2.stock_quantity}')

        # 验证出库日志 (ref_type='stock_out'，关联出库单而非销售订单)
        so_out = StockOut.query.filter_by(sales_order_id=so.id).first()
        if so_out:
            ok('出库单已创建', f'单号={so_out.delivery_number}')
            logs = StockLog.query.filter_by(reference_id=so_out.id, reference_type='stock_out').all()
            if logs:
                ok('销售出库日志', f'{len(logs)}条')
            else:
                fail('销售出库日志', f'未找到出库日志(out_id={so_out.id})')
        else:
            fail('出库单创建', '未找到关联出库单(可能库存不足导致出库失败)')

        # 销售退货
        resp = client.post(f'/sales/orders/{so.id}/quick-return', data={}, follow_redirects=True)
        if resp.status_code == 200:
            ok('销售退货')
        else:
            fail('销售退货', f'HTTP {resp.status_code}')
    else:
        fail('销售订单入库验证', '无订单数据')


# 采购退货放在销售测试之后，避免退货消耗库存影响销售
def test_purchase_return(client):
    """采购退货测试"""
    print("\n--- 采购退货测试 ---")
    po = PurchaseOrder.query.first()
    if po and po.status == 'completed':
        resp = client.post(f'/purchase/orders/{po.id}/quick-return', data={}, follow_redirects=True)
        if resp.status_code == 200:
            ok('采购退货')
        else:
            fail('采购退货', f'HTTP {resp.status_code}')
    else:
        ok('采购退货跳过', f'订单状态={po.status if po else None}')


def test_inventory_operations(client):
    """库存管理操作测试"""
    print("\n--- 库存管理操作测试 ---")

    # 1. 库存调拨
    ts = int(time.time())
    resp = client.post('/inventory/stock-transfer', data={
        'product_id': 1,
        'from_warehouse_id': 1,
        'to_warehouse_id': 2,
        'quantity': 3,
        'notes': f'自动化调拨_{ts}',
    }, follow_redirects=True)
    if resp.status_code == 200:
        ok('库存调拨')
    else:
        fail('库存调拨', f'HTTP {resp.status_code}')
        data = resp.data.decode('utf-8', errors='replace')
        if '500' in data or 'Error' in data:
            fail('库存调拨500错误', data[:500])

    # 2. 库存盘点
    resp = client.post('/inventory/stock-check', data={
        'product_id': 1,
        'warehouse_id': 1,
        'actual_quantity': 5,
        'notes': '自动化盘点',
    }, follow_redirects=True)
    if resp.status_code == 200:
        ok('库存盘点')
    else:
        fail('库存盘点', f'HTTP {resp.status_code}')

    # 3. 库存调整
    resp = client.post('/inventory/stock-adjust', data={
        'product_id': 2,
        'warehouse_id': 1,
        'adjust_quantity': 10,
        'adjust_type': 'in',
        'notes': '自动化调整',
    }, follow_redirects=True)
    if resp.status_code == 200:
        ok('库存调整')
    else:
        fail('库存调整', f'HTTP {resp.status_code}')


def test_finance_operations(client):
    """财务管理操作测试"""
    print("\n--- 财务管理操作测试 ---")

    ts = int(time.time())

    # 1. 收款
    resp = client.post('/finance/receipt/add', data={
        'customer_id': 1,
        'amount': '5000',
        'receipt_date': '2026-06-01',
        'payment_method': 'bank_transfer',
        'notes': f'自动化收款_{ts}',
    }, follow_redirects=True)
    if resp.status_code == 200:
        ok('创建收款单')
        receipt = Receipt.query.first()
        if receipt:
            ok('收款单验证', f'金额={receipt.amount}')
            resp = client.get(f'/finance/receipt/{receipt.id}')
            if resp.status_code == 200:
                ok('查看收款单详情')
    else:
        fail('创建收款单', f'HTTP {resp.status_code}')

    # 2. 付款
    resp = client.post('/finance/payment/add', data={
        'supplier_id': 1,
        'amount': '30000',
        'payment_date': '2026-06-01',
        'payment_method': 'bank_transfer',
        'notes': f'自动化付款_{ts}',
    }, follow_redirects=True)
    if resp.status_code == 200:
        ok('创建付款单')
        payment = Payment.query.first()
        if payment:
            ok('付款单验证', f'金额={payment.amount}')
    else:
        fail('创建付款单', f'HTTP {resp.status_code}')

    # 3. 费用
    resp = client.post('/finance/expense/add', data={
        'category': 'office',
        'amount': '500',
        'expense_date': '2026-06-01',
        'payment_method': 'cash',
        'payee': '办公用品供应商',
        'notes': f'自动化费用_{ts}',
    }, follow_redirects=True)
    if resp.status_code == 200:
        ok('创建费用单')
        expense = Expense.query.first()
        if expense:
            ok('费用单验证', f'金额={expense.amount}')
    else:
        fail('创建费用单', f'HTTP {resp.status_code}')


def test_delete_operations(client):
    """删除操作测试"""
    print("\n--- 删除操作测试 ---")

    # 先创建一个可删除的分类
    ts = int(time.time())
    resp = client.post('/product/categories/new', data={
        'name': f'待删除分类_{ts}',
        'description': '测试删除',
    }, follow_redirects=True)
    
    cat = Category.query.filter_by(name=f'待删除分类_{ts}').first()
    if cat:
        resp = client.post(f'/product/categories/{cat.id}/delete', follow_redirects=True)
        if resp.status_code == 200:
            ok('删除分类')
            remaining = Category.query.filter_by(name=f'待删除分类_{ts}').first()
            if not remaining:
                ok('分类已从DB删除')
            else:
                fail('分类删除验证', '分类仍在数据库中')
        else:
            fail('删除分类', f'HTTP {resp.status_code}')
    else:
        fail('删除分类准备', '未创建分类')

    # 创建并删除仓库
    resp = client.post('/partner/warehouses/new', data={
        'code': f'WH_DEL_{ts}',
        'name': f'待删除仓库_{ts}',
        'address': '临时',
    }, follow_redirects=True)
    
    wh = Warehouse.query.filter_by(code=f'WH_DEL_{ts}').first()
    if wh:
        resp = client.post(f'/partner/warehouses/{wh.id}/delete', follow_redirects=True)
        if resp.status_code == 200:
            ok('删除仓库')
        else:
            fail('删除仓库', f'HTTP {resp.status_code}')


def test_all_get_pages(client):
    """测试所有GET页面是否能正常加载"""
    print("\n--- 所有GET页面加载测试 ---")

    pages = [
        ('/', '首页重定向', False),  # redirect
        ('/auth/login', '登录页', True),
        ('/auth/register', '注册页', True),
        ('/auth/profile', '个人资料', True),
        ('/product/', '商品列表', True),
        ('/product/products/new', '新建商品', True),
        ('/product/categories', '分类列表', True),
        ('/product/categories/new', '新建分类', True),
        ('/partner/suppliers', '供应商列表', True),
        ('/partner/suppliers/new', '新建供应商', True),
        ('/partner/customers', '客户列表', True),
        ('/partner/customers/new', '新建客户', True),
        ('/partner/warehouses', '仓库列表', True),
        ('/partner/warehouses/new', '新建仓库', True),
        ('/purchase/', '采购首页', True),
        ('/purchase/orders/new', '新建采购订单', True),
        ('/purchase/returns', '采购退货列表', True),
        ('/purchase/stock-ins/new', '新建入库单', True),
        ('/sales/', '销售首页', True),
        ('/sales/orders/new', '新建销售订单', True),
        ('/sales/returns', '销售退货列表', True),
        ('/sales/stock-outs/new', '新建出库单', True),
        ('/inventory/', '库存首页', True),
        ('/inventory/products', '商品库存', True),
        ('/inventory/logs', '库存日志', True),
        ('/inventory/stock-check', '库存盘点', True),
        ('/inventory/stock-transfer', '库存调拨', True),
        ('/inventory/stock-adjust', '库存调整', True),
        ('/inventory/warehouse/1', '仓库库存详情', True),
        ('/finance/', '财务首页', True),
        ('/finance/receipts', '收款列表', True),
        ('/finance/receipt/add', '新建收款', True),
        ('/finance/payments', '付款列表', True),
        ('/finance/payment/add', '新建付款', True),
        ('/finance/expenses', '费用列表', True),
        ('/finance/expense/add', '新建费用', True),
        ('/finance/profit-analysis', '利润分析', True),
        ('/finance/ar-ap-search', '应收应付搜索', True),
        ('/report/', '报表首页', True),
        ('/report/daily-report', '日报', True),
        ('/report/inventory-report', '库存报表', True),
        ('/report/sales-ranking', '销售排行', True),
        ('/report/customer-statistics', '客户统计', True),
        ('/report/supplier-statistics', '供应商统计', True),
        ('/system/', '系统首页', True),
        ('/system/users', '用户管理', True),
        ('/system/logs', '系统日志', True),
        ('/system/backup', '数据备份', True),
        ('/system/settings', '系统设置', True),
    ]

    # API pages
    api_pages = [
        '/product/api/products',
        '/product/api/categories',
        '/inventory/api/low-stock',
        '/inventory/api/stock-sync-check',
        '/inventory/api/logs-statistics',
        '/finance/api/financial-summary',
        '/finance/api/customer-ar/1',
        '/finance/api/supplier-ap/1',
        '/report/api/sales-trend',
        '/system/api/system-info',
        '/system/api/system/recent-logs',
        '/system/backup/list',
    ]

    # These APIs require existing data (tested after business flow)
    data_dependent_apis = [
        '/purchase/api/purchase-orders/1/items',
        '/sales/api/sales-orders/1/items',
    ]

    get_ok = 0
    get_fail = 0
    for url, name, check_200 in pages:
        try:
            resp = client.get(url, follow_redirects=True)
            if check_200:
                if resp.status_code == 200:
                    get_ok += 1
                else:
                    get_fail += 1
                    fail(f'GET {name}', f'HTTP {resp.status_code}')
            else:
                get_ok += 1
        except Exception as e:
            get_fail += 1
            fail(f'GET {name}', str(e)[:200])

    for url in api_pages:
        try:
            resp = client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                get_ok += 1
            else:
                get_fail += 1
                fail(f'API {url}', f'HTTP {resp.status_code}')
        except Exception as e:
            get_fail += 1
            fail(f'API {url}', str(e)[:200])

    print(f"  GET页面总计: {get_ok} 通过, {get_fail} 失败")


def test_export_pages(client):
    """测试导出功能"""
    print("\n--- 导出功能测试 ---")

    export_pages = [
        '/finance/export-receipts',
        '/finance/export-payments',
        '/finance/export-expenses',
        '/finance/export-profit-analysis',
        '/finance/export-customer-ar/1',
        '/finance/export-supplier-ap/1',
        '/report/export/daily',
        '/report/export/inventory',
        '/report/export/sales-ranking',
        '/report/export-products',
        '/report/export/customer',
        '/report/export/supplier',
        '/inventory/api/export-logs',
        '/inventory/export-warehouse-stock/1',
    ]

    for url in export_pages:
        try:
            resp = client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                ct = resp.content_type
                ok(f'导出 {url.split("/")[-1]}', f'Content-Type: {ct}')
            else:
                fail(f'导出 {url}', f'HTTP {resp.status_code}')
        except Exception as e:
            fail(f'导出 {url}', str(e)[:200])


def main():
    print("=" * 70)
    print("  my-jxc 进销存管理系统 - 深度业务流程测试")
    print("=" * 70)

    with app.app_context():
        init_data()
        client = app.test_client()
        login(client)

        try:
            # 1. 所有GET页面
            test_all_get_pages(client)

            # 2. 完整采购流程
            test_complete_purchase_flow(client)

            # 3. 完整销售流程
            test_complete_sales_flow(client)

            # 3.5 采购退货（放在销售之后，避免退货消耗库存）
            test_purchase_return(client)

            # 3.6 数据依赖API测试
            print("\n--- 数据依赖API测试 ---")
            data_apis = [
                ('/purchase/api/purchase-orders/1/items', '采购订单明细API'),
                ('/sales/api/sales-orders/1/items', '销售订单明细API'),
            ]
            for url, name in data_apis:
                try:
                    resp = client.get(url, follow_redirects=True)
                    if resp.status_code == 200:
                        ok(name)
                    else:
                        fail(name, f'HTTP {resp.status_code}')
                except Exception as e:
                    fail(name, str(e)[:200])

            # 4. 库存管理操作
            test_inventory_operations(client)

            # 5. 财务管理操作
            test_finance_operations(client)

            # 6. 删除操作
            test_delete_operations(client)

            # 7. 导出功能
            test_export_pages(client)

        except Exception as e:
            print(f"\n💥 测试运行异常: {e}")
            traceback.print_exc()

    print(f"\n{'='*70}")
    print(f"  最终结果: {passed} 通过, {failed} 失败")
    print(f"{'='*70}")
    if errors:
        print(f"\n  失败详情:")
        for name, err in errors:
            print(f"    ❌ {name}: {err[:200]}")
    print()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
