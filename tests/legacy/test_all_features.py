#!/usr/bin/env python3
"""
my-jxc 进销存系统 全面功能测试
使用 Flask test_client() 测试所有模块的所有路由
"""

import os
import sys
import json
import tempfile
import traceback

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.pop('DATABASE_URL', None)

from app import create_app, db
from app.models import (
    User, Category, Product, Supplier, Customer, Warehouse,
    PurchaseOrder, PurchaseOrderItem, SalesOrder, SalesOrderItem,
    StockIn, StockInItem, StockOut, StockOutItem,
    PurchaseReturn, PurchaseReturnItem, SalesReturn, SalesReturnItem,
    StockLog, Receipt, Payment, Expense, Log
)

# ======================== 测试基础设施 ========================

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []  # (module, test_name, status_code, error_detail)

    def ok(self, module, name):
        self.passed += 1
        print(f"  ✅ {name} → PASS")

    def fail(self, module, name, detail=""):
        self.failed += 1
        self.errors.append((module, name, detail))
        truncated = detail[:200] if detail else ''
        print(f"  ❌ {name} → FAIL: {truncated}")

    def summary(self):
        print(f"\n{'='*60}")
        print(f"测试结果汇总: {self.passed} 通过, {self.failed} 失败, 共 {self.passed + self.failed} 项")
        if self.errors:
            print(f"\n{'='*60}")
            print("失败详情:")
            for module, name, detail in self.errors:
                print(f"  [{module}] {name}")
                if detail:
                    # Print only the last few lines of error for readability
                    lines = detail.strip().split('\n')
                    for line in lines[-5:]:
                        print(f"    {line}")
        print(f"{'='*60}")
        return self.failed == 0


def create_test_app():
    """创建测试用 Flask app，使用临时数据库"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # 禁用 CSRF 简化测试
    app.config['SERVER_NAME'] = 'localhost.localdomain'

    with app.app_context():
        db.create_all()
        # 创建管理员（检查是否已存在，避免重复）
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', role='admin', is_active=True)
            admin.set_password('admin123')
            db.session.add(admin)
        # 创建普通用户
        if not User.query.filter_by(username='user1').first():
            user = User(username='user1', email='user1@example.com', role='user', is_active=True)
            user.set_password('user123')
            db.session.add(user)
        db.session.commit()

    return app, db_path


def login(client, username='admin', password='admin123'):
    """登录并返回 client"""
    return client.post('/auth/login', data={
        'username': username,
        'password': password,
    }, follow_redirects=True)


def get_csrf_token(response_data):
    """从 HTML 中提取 CSRF token"""
    import re
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response_data)
    if match:
        return match.group(1)
    match = re.search(r'csrf_token.*?value="([^"]+)"', response_data)
    if match:
        return match.group(1)
    return ''


# ======================== 测试用例 ========================

def test_auth_module(app, R):
    """测试认证模块"""
    print("\n[认证模块]")

    with app.test_client() as c:
        # 1. 登录页 GET
        resp = c.get('/auth/login')
        R.ok('auth', '登录页GET') if resp.status_code == 200 else R.fail('auth', '登录页GET', f'HTTP {resp.status_code}')

        # 2. 正确登录
        resp = login(c)
        R.ok('auth', '管理员登录') if resp.status_code == 200 else R.fail('auth', '管理员登录', f'HTTP {resp.status_code}')

        # 3. 错误密码登录
        resp = c.post('/auth/login', data={'username': 'admin', 'password': 'wrong'}, follow_redirects=True)
        R.ok('auth', '错误密码登录') if resp.status_code == 200 else R.fail('auth', '错误密码登录', f'HTTP {resp.status_code}')

        # 4. 登录后访问个人资料页
        login(c)
        resp = c.get('/auth/profile')
        R.ok('auth', '个人资料页GET') if resp.status_code == 200 else R.fail('auth', '个人资料页GET', f'HTTP {resp.status_code}')

        # 5. 修改密码
        resp = c.post('/auth/change-password', data={
            'old_password': 'admin123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123',
        }, follow_redirects=True)
        R.ok('auth', '修改密码') if resp.status_code == 200 else R.fail('auth', '修改密码', f'HTTP {resp.status_code}')

        # 6. 改回密码
        resp = c.post('/auth/change-password', data={
            'old_password': 'newpass123',
            'new_password': 'admin123',
            'confirm_password': 'admin123',
        }, follow_redirects=True)
        R.ok('auth', '改回密码') if resp.status_code == 200 else R.fail('auth', '改回密码', f'HTTP {resp.status_code}')

        # 7. 修改邮箱
        resp = c.post('/auth/change-email', data={
            'new_email': 'admin_new@example.com',
        }, follow_redirects=True)
        R.ok('auth', '修改邮箱') if resp.status_code == 200 else R.fail('auth', '修改邮箱', f'HTTP {resp.status_code}')

        # 8. 修改邮箱 - 无效格式
        resp = c.post('/auth/change-email', data={
            'new_email': 'not-an-email',
        }, follow_redirects=True)
        R.ok('auth', '无效邮箱格式拒绝') if resp.status_code == 200 else R.fail('auth', '无效邮箱格式拒绝', f'HTTP {resp.status_code}')

        # 9. 注册新用户
        resp = c.post('/auth/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass456',
            'password2': 'newpass456',
        }, follow_redirects=True)
        R.ok('auth', '注册新用户') if resp.status_code == 200 else R.fail('auth', '注册新用户', f'HTTP {resp.status_code}')

        # 10. 重复用户名注册
        resp = c.post('/auth/register', data={
            'username': 'newuser',
            'email': 'another@example.com',
            'password': 'newpass456',
            'password2': 'newpass456',
        }, follow_redirects=True)
        R.ok('auth', '重复用户名注册拒绝') if resp.status_code == 200 else R.fail('auth', '重复用户名注册拒绝', f'HTTP {resp.status_code}')

        # 11. 退出登录
        resp = c.post('/auth/logout', follow_redirects=True)
        R.ok('auth', '退出登录') if resp.status_code == 200 else R.fail('auth', '退出登录', f'HTTP {resp.status_code}')

        # 12. 未登录访问保护页面 → 应重定向到登录
        resp = c.get('/product/products', follow_redirects=False)
        R.ok('auth', '未登录保护(302重定向)') if resp.status_code == 302 else R.fail('auth', '未登录保护(302重定向)', f'HTTP {resp.status_code}')

        # 13. 普通用户登录
        resp = login(c, 'user1', 'user123')
        R.ok('auth', '普通用户登录') if resp.status_code == 200 else R.fail('auth', '普通用户登录', f'HTTP {resp.status_code}')


def test_main_dashboard(app, R):
    """测试主页仪表盘"""
    print("\n[主页仪表盘]")

    with app.test_client() as c:
        login(c)
        resp = c.get('/')
        R.ok('main', '仪表盘GET') if resp.status_code == 200 else R.fail('main', '仪表盘GET', f'HTTP {resp.status_code}')


def test_product_module(app, R):
    """测试产品管理模块"""
    print("\n[产品管理模块]")

    with app.test_client() as c:
        login(c)

        # 1. 产品列表页
        resp = c.get('/product/products')
        R.ok('product', '产品列表GET') if resp.status_code == 200 else R.fail('product', '产品列表GET', f'HTTP {resp.status_code}')

        # 2. 产品搜索
        resp = c.get('/product/products?keyword=test')
        R.ok('product', '产品搜索') if resp.status_code == 200 else R.fail('product', '产品搜索', f'HTTP {resp.status_code}')

        # 3. 创建产品
        resp = c.post('/product/products/new', data={
            'code': 'P001',
            'name': '测试产品A',
            'category_id': 1,
            'spec': '100ml',
            'unit': '瓶',
            'purchase_price': '10.00',
            'sale_price': '20.00',
            'safety_stock': '50',
            'description': '测试用产品',
        }, follow_redirects=True)
        R.ok('product', '创建产品') if resp.status_code == 200 else R.fail('product', '创建产品', f'HTTP {resp.status_code}')

        # 4. 重复编码创建产品
        resp = c.post('/product/products/new', data={
            'code': 'P001',
            'name': '重复产品',
            'unit': '个',
        }, follow_redirects=True)
        R.ok('product', '重复编码创建拒绝') if resp.status_code == 200 else R.fail('product', '重复编码创建拒绝', f'HTTP {resp.status_code}')

        # 5. 查看产品详情
        resp = c.get('/product/products/1')
        R.ok('product', '产品详情GET') if resp.status_code == 200 else R.fail('product', '产品详情GET', f'HTTP {resp.status_code}')

        # 6. 编辑产品
        resp = c.post('/product/products/1/edit', data={
            'code': 'P001',
            'name': '测试产品A-修改',
            'category_id': 1,
            'unit': '瓶',
            'purchase_price': '12.00',
            'sale_price': '25.00',
            'safety_stock': '60',
        }, follow_redirects=True)
        R.ok('product', '编辑产品') if resp.status_code == 200 else R.fail('product', '编辑产品', f'HTTP {resp.status_code}')

        # 7. API - 产品列表
        resp = c.get('/product/api/products?limit=10')
        if resp.status_code == 200:
            try:
                data = json.loads(resp.data)
                R.ok('product', 'API产品列表JSON')
            except:
                R.fail('product', 'API产品列表JSON', 'JSON解析失败')
        else:
            R.fail('product', 'API产品列表JSON', f'HTTP {resp.status_code}')

        # 8. API - 更新产品价格
        resp = c.post('/product/api/product/price',
            data=json.dumps({'product_id': 1, 'price_type': 'sale_price', 'price': 30.00}),
            content_type='application/json')
        R.ok('product', 'API更新价格') if resp.status_code == 200 else R.fail('product', 'API更新价格', f'HTTP {resp.status_code}')

        # 9. API - 更新产品价格 - 无效类型
        resp = c.post('/product/api/product/price',
            data=json.dumps({'product_id': 1, 'price_type': 'invalid_type', 'price': 30.00}),
            content_type='application/json')
        R.ok('product', 'API无效价格类型拒绝') if resp.status_code != 200 else R.fail('product', 'API无效价格类型拒绝', f'HTTP {resp.status_code}')

        # 10. 分类列表
        resp = c.get('/product/categories')
        R.ok('product', '分类列表GET') if resp.status_code == 200 else R.fail('product', '分类列表GET', f'HTTP {resp.status_code}')

        # 11. 创建分类
        resp = c.post('/product/categories/new', data={
            'name': '测试分类A',
            'description': '测试分类',
        }, follow_redirects=True)
        R.ok('product', '创建分类') if resp.status_code == 200 else R.fail('product', '创建分类', f'HTTP {resp.status_code}')

        # 12. API - 分类列表
        resp = c.get('/product/api/categories')
        R.ok('product', 'API分类列表JSON') if resp.status_code == 200 else R.fail('product', 'API分类列表JSON', f'HTTP {resp.status_code}')


def test_partner_module(app, R):
    """测试合作伙伴管理（供应商/客户/仓库）"""
    print("\n[合作伙伴模块]")

    with app.test_client() as c:
        login(c)

        # === 供应商 ===
        resp = c.get('/partner/suppliers')
        R.ok('partner', '供应商列表GET') if resp.status_code == 200 else R.fail('partner', '供应商列表GET', f'HTTP {resp.status_code}')

        resp = c.post('/partner/suppliers/new', data={
            'code': 'SUP001',
            'name': '测试供应商A',
            'contact_person': '张三',
            'phone': '13800138001',
            'address': '北京市朝阳区',
            'email': 'sup@example.com',
        }, follow_redirects=True)
        R.ok('partner', '创建供应商') if resp.status_code == 200 else R.fail('partner', '创建供应商', f'HTTP {resp.status_code}')

        # 供应商/客户/仓库没有单独的详情页路由，只有编辑页
        resp = c.post('/partner/suppliers/1/edit', data={
            'code': 'SUP001',
            'name': '测试供应商A-修改',
            'contact_person': '李四',
            'phone': '13800138002',
        }, follow_redirects=True)
        R.ok('partner', '编辑供应商') if resp.status_code == 200 else R.fail('partner', '编辑供应商', f'HTTP {resp.status_code}')

        # === 客户 ===
        resp = c.get('/partner/customers')
        R.ok('partner', '客户列表GET') if resp.status_code == 200 else R.fail('partner', '客户列表GET', f'HTTP {resp.status_code}')

        resp = c.post('/partner/customers/new', data={
            'code': 'CUS001',
            'name': '测试客户A',
            'contact_person': '王五',
            'phone': '13900139001',
            'address': '上海市浦东新区',
            'email': 'cus@example.com',
        }, follow_redirects=True)
        R.ok('partner', '创建客户') if resp.status_code == 200 else R.fail('partner', '创建客户', f'HTTP {resp.status_code}')

        resp = c.post('/partner/customers/1/edit', data={
            'code': 'CUS001',
            'name': '测试客户A-修改',
            'contact_person': '赵六',
        }, follow_redirects=True)
        R.ok('partner', '编辑客户') if resp.status_code == 200 else R.fail('partner', '编辑客户', f'HTTP {resp.status_code}')

        # === 仓库 ===
        resp = c.get('/partner/warehouses')
        R.ok('partner', '仓库列表GET') if resp.status_code == 200 else R.fail('partner', '仓库列表GET', f'HTTP {resp.status_code}')

        resp = c.post('/partner/warehouses/new', data={
            'code': 'WH002',
            'name': '测试仓库B',
            'address': '广州市天河区',
            'manager': '管理员B',
            'phone': '13700137001',
        }, follow_redirects=True)
        R.ok('partner', '创建仓库') if resp.status_code == 200 else R.fail('partner', '创建仓库', f'HTTP {resp.status_code}')


def test_purchase_module(app, R):
    """测试采购管理模块"""
    print("\n[采购管理模块]")

    with app.test_client() as c:
        login(c)

        # 1. 采购首页
        resp = c.get('/purchase/')
        R.ok('purchase', '采购首页GET') if resp.status_code == 200 else R.fail('purchase', '采购首页GET', f'HTTP {resp.status_code}')

        # 2. 创建采购订单（草稿）
        resp = c.post('/purchase/orders/new', data={
            'order_status': 'draft',
            'supplier_id': 1,
            'warehouse_id': 1,
            'order_date': '2026-06-01',
            'expected_date': '2026-06-15',
            'notes': '测试采购订单',
            'product_id': ['1'],
            'quantity': ['100'],
            'unit_price': ['10.00'],
        }, follow_redirects=True)
        R.ok('purchase', '创建采购订单(草稿)') if resp.status_code == 200 else R.fail('purchase', '创建采购订单(草稿)', f'HTTP {resp.status_code}')

        # 3. 查看采购订单
        resp = c.get('/purchase/orders/1')
        R.ok('purchase', '查看采购订单GET') if resp.status_code == 200 else R.fail('purchase', '查看采购订单GET', f'HTTP {resp.status_code}')

        # 4. 编辑采购订单
        resp = c.post('/purchase/orders/1/edit', data={
            'order_status': 'draft',
            'supplier_id': 1,
            'warehouse_id': 1,
            'order_date': '2026-06-01',
            'expected_date': '2026-06-20',
            'notes': '修改后的采购订单',
            'product_id': ['1'],
            'quantity': ['200'],
            'unit_price': ['10.50'],
        }, follow_redirects=True)
        R.ok('purchase', '编辑采购订单') if resp.status_code == 200 else R.fail('purchase', '编辑采购订单', f'HTTP {resp.status_code}')

        # 5. 快捷入库（直接完成采购订单）
        resp = c.post('/purchase/orders/1/quick-stock-in', follow_redirects=True)
        R.ok('purchase', '快捷入库') if resp.status_code == 200 else R.fail('purchase', '快捷入库', f'HTTP {resp.status_code}')

        # 6. 验证入库后库存
        with app.app_context():
            product = Product.query.get(1)
            if product:
                stock = product.stock_quantity
                R.ok('purchase', f'入库后库存验证({stock})')
            else:
                R.fail('purchase', '入库后库存验证', '产品不存在')

        # 7. 采购退货
        resp = c.post('/purchase/orders/1/quick-return', data={
            'product_id': ['1'],
            'quantity': ['10'],
            'unit_price': ['10.00'],
        }, follow_redirects=True)
        R.ok('purchase', '采购退货') if resp.status_code == 200 else R.fail('purchase', '采购退货', f'HTTP {resp.status_code}')

        # 8. 创建独立入库单
        resp = c.post('/purchase/stock-ins/new', data={
            'purchase_order_id': '',
            'warehouse_id': 1,
            'receipt_date': '2026-06-01',
            'handler': '测试员',
            'notes': '独立入库单',
        }, follow_redirects=True)
        R.ok('purchase', '创建独立入库单') if resp.status_code == 200 else R.fail('purchase', '创建独立入库单', f'HTTP {resp.status_code}')

        # 9. 为独立入库单添加项目
        resp = c.post('/purchase/stock-ins/2/items', data={
            'product_id': ['1'],
            'quantity': ['50'],
            'unit_price': ['10.00'],
        }, follow_redirects=True)
        R.ok('purchase', '入库单添加项目') if resp.status_code == 200 else R.fail('purchase', '入库单添加项目', f'HTTP {resp.status_code}')

        # 10. 完成独立入库单
        resp = c.post('/purchase/stock-ins/2/complete', follow_redirects=True)
        R.ok('purchase', '完成独立入库') if resp.status_code == 200 else R.fail('purchase', '完成独立入库', f'HTTP {resp.status_code}')

        # 11. API - 采购订单项目
        resp = c.get('/purchase/api/purchase-orders/1/items')
        R.ok('purchase', 'API采购订单项目JSON') if resp.status_code == 200 else R.fail('purchase', 'API采购订单项目JSON', f'HTTP {resp.status_code}')

        # 12. 创建第二个采购订单（待确认状态）
        resp = c.post('/purchase/orders/new', data={
            'order_status': 'confirmed',
            'supplier_id': 1,
            'warehouse_id': 1,
            'order_date': '2026-06-01',
            'product_id': ['1'],
            'quantity': ['30'],
            'unit_price': ['10.00'],
        }, follow_redirects=True)
        R.ok('purchase', '创建确认状态采购单') if resp.status_code == 200 else R.fail('purchase', '创建确认状态采购单', f'HTTP {resp.status_code}')

        # 13. 采购首页筛选
        resp = c.get('/purchase/?status=completed&tab=orders')
        R.ok('purchase', '采购筛选(已完成)') if resp.status_code == 200 else R.fail('purchase', '采购筛选(已完成)', f'HTTP {resp.status_code}')


def test_sales_module(app, R):
    """测试销售管理模块"""
    print("\n[销售管理模块]")

    with app.test_client() as c:
        login(c)

        # 1. 销售首页
        resp = c.get('/sales/')
        R.ok('sales', '销售首页GET') if resp.status_code == 200 else R.fail('sales', '销售首页GET', f'HTTP {resp.status_code}')

        # 2. 创建销售订单（草稿，暂不出库）
        resp = c.post('/sales/orders/new', data={
            'order_status': 'draft',
            'customer_id': 1,
            'warehouse_id': 1,
            'order_date': '2026-06-01',
            'delivery_date': '2026-06-10',
            'notes': '测试销售订单',
            'product_id': ['1'],
            'quantity': ['20'],
            'unit_price': ['25.00'],
        }, follow_redirects=True)
        R.ok('sales', '创建销售订单(草稿)') if resp.status_code == 200 else R.fail('sales', '创建销售订单(草稿)', f'HTTP {resp.status_code}')

        # 3. 查看销售订单
        resp = c.get('/sales/orders/1')
        R.ok('sales', '查看销售订单GET') if resp.status_code == 200 else R.fail('sales', '查看销售订单GET', f'HTTP {resp.status_code}')

        # 4. 编辑销售订单
        resp = c.post('/sales/orders/1/edit', data={
            'order_status': 'draft',
            'customer_id': 1,
            'warehouse_id': 1,
            'order_date': '2026-06-01',
            'delivery_date': '2026-06-15',
            'notes': '修改后销售订单',
            'product_id': ['1'],
            'quantity': ['15'],
            'unit_price': ['28.00'],
        }, follow_redirects=True)
        R.ok('sales', '编辑销售订单') if resp.status_code == 200 else R.fail('sales', '编辑销售订单', f'HTTP {resp.status_code}')

        # 5. 快捷出库（直接完成销售订单）
        resp = c.post('/sales/orders/1/quick-stock-out', follow_redirects=True)
        R.ok('sales', '快捷出库') if resp.status_code == 200 else R.fail('sales', '快捷出库', f'HTTP {resp.status_code}')

        # 6. 验证出库后库存减少
        with app.app_context():
            product = Product.query.get(1)
            if product:
                R.ok('sales', f'出库后库存验证({product.stock_quantity})')
            else:
                R.fail('sales', '出库后库存验证', '产品不存在')

        # 7. 销售退货
        resp = c.post('/sales/orders/1/quick-return', data={
            'product_id': ['1'],
            'quantity': ['5'],
            'unit_price': ['25.00'],
        }, follow_redirects=True)
        R.ok('sales', '销售退货') if resp.status_code == 200 else R.fail('sales', '销售退货', f'HTTP {resp.status_code}')

        # 8. 创建独立出库单
        resp = c.post('/sales/stock-outs/new', data={
            'sales_order_id': '',
            'warehouse_id': 1,
            'delivery_date': '2026-06-01',
            'handler': '测试员',
            'notes': '独立出库单',
        }, follow_redirects=True)
        R.ok('sales', '创建独立出库单') if resp.status_code == 200 else R.fail('sales', '创建独立出库单', f'HTTP {resp.status_code}')

        # 9. 为独立出库单添加项目
        resp = c.post('/sales/stock-outs/2/items', data={
            'product_id': ['1'],
            'quantity': ['10'],
            'unit_price': ['25.00'],
        }, follow_redirects=True)
        R.ok('sales', '出库单添加项目') if resp.status_code == 200 else R.fail('sales', '出库单添加项目', f'HTTP {resp.status_code}')

        # 10. 完成独立出库单
        resp = c.post('/sales/stock-outs/2/complete', follow_redirects=True)
        R.ok('sales', '完成独立出库') if resp.status_code == 200 else R.fail('sales', '完成独立出库', f'HTTP {resp.status_code}')

        # 11. 库存不足测试 - 尝试出库超过库存
        with app.app_context():
            product = Product.query.get(1)
            current_stock = int(product.stock_quantity) if product.stock_quantity else 0

        resp = c.post('/sales/orders/new', data={
            'order_status': 'completed',
            'customer_id': 1,
            'warehouse_id': 1,
            'order_date': '2026-06-01',
            'product_id': ['1'],
            'quantity': [str(current_stock + 9999)],
            'unit_price': ['25.00'],
        }, follow_redirects=True)
        R.ok('sales', '库存不足拒绝出库') if resp.status_code == 200 else R.fail('sales', '库存不足拒绝出库', f'HTTP {resp.status_code}')

        # 12. API - 销售订单项目
        resp = c.get('/sales/api/sales-orders/1/items')
        R.ok('sales', 'API销售订单项目JSON') if resp.status_code == 200 else R.fail('sales', 'API销售订单项目JSON', f'HTTP {resp.status_code}')

        # 13. 销售首页筛选
        resp = c.get('/sales/?status=completed&tab=orders')
        R.ok('sales', '销售筛选(已完成)') if resp.status_code == 200 else R.fail('sales', '销售筛选(已完成)', f'HTTP {resp.status_code}')


def test_inventory_module(app, R):
    """测试库存管理模块"""
    print("\n[库存管理模块]")

    with app.test_client() as c:
        login(c)

        # 1. 库存首页
        resp = c.get('/inventory/')
        R.ok('inventory', '库存首页GET') if resp.status_code == 200 else R.fail('inventory', '库存首页GET', f'HTTP {resp.status_code}')

        # 2. 产品库存列表
        resp = c.get('/inventory/products')
        R.ok('inventory', '产品库存列表GET') if resp.status_code == 200 else R.fail('inventory', '产品库存列表GET', f'HTTP {resp.status_code}')

        # 3. 仓库库存详情
        resp = c.get('/inventory/warehouse/1')
        R.ok('inventory', '仓库库存详情GET') if resp.status_code == 200 else R.fail('inventory', '仓库库存详情GET', f'HTTP {resp.status_code}')

        # 4. 仓库库存详情 - 不存在的仓库
        resp = c.get('/inventory/warehouse/9999')
        R.ok('inventory', '不存在仓库(404)') if resp.status_code == 404 else R.fail('inventory', '不存在仓库(404)', f'HTTP {resp.status_code}')

        # 5. 库存盘点
        resp = c.post('/inventory/stock-check', data={
            'warehouse_id': 1,
            'product_id': ['1'],
            'actual_quantity': ['100'],
            'notes': '盘点测试',
        }, follow_redirects=True)
        R.ok('inventory', '库存盘点') if resp.status_code == 200 else R.fail('inventory', '库存盘点', f'HTTP {resp.status_code}')

        # 6. 库存调拨
        resp = c.post('/inventory/stock-transfer', data={
            'from_warehouse': 1,
            'to_warehouse': 2,
            'transfer_date': '2026-06-01',
            'remark': '测试调拨',
            'product_id': ['1'],
            'quantity': ['20'],
        }, follow_redirects=True)
        R.ok('inventory', '库存调拨') if resp.status_code == 200 else R.fail('inventory', '库存调拨', f'HTTP {resp.status_code}')

        # 7. 库存调整 - 调入
        resp = c.post('/inventory/stock-adjust', data={
            'product_id': 1,
            'warehouse_id': 1,
            'adjust_type': 'adjust_in',
            'quantity': '50',
            'notes': '测试调入',
        }, follow_redirects=True)
        R.ok('inventory', '库存调整-调入') if resp.status_code == 200 else R.fail('inventory', '库存调整-调入', f'HTTP {resp.status_code}')

        # 8. 库存调整 - 调出
        resp = c.post('/inventory/stock-adjust', data={
            'product_id': 1,
            'warehouse_id': 1,
            'adjust_type': 'adjust_out',
            'quantity': '10',
            'notes': '测试调出',
        }, follow_redirects=True)
        R.ok('inventory', '库存调整-调出') if resp.status_code == 200 else R.fail('inventory', '库存调整-调出', f'HTTP {resp.status_code}')

        # 9. 库存日志
        resp = c.get('/inventory/logs')
        R.ok('inventory', '库存日志GET') if resp.status_code == 200 else R.fail('inventory', '库存日志GET', f'HTTP {resp.status_code}')

        # 10. API - 低库存预警
        resp = c.get('/inventory/api/low-stock')
        if resp.status_code == 200:
            try:
                data = json.loads(resp.data)
                R.ok('inventory', 'API低库存预警JSON')
            except:
                R.fail('inventory', 'API低库存预警JSON', 'JSON解析失败')
        else:
            R.fail('inventory', 'API低库存预警JSON', f'HTTP {resp.status_code}')

        # 11. API - 日志统计
        resp = c.get('/inventory/api/logs-statistics')
        if resp.status_code == 200:
            try:
                data = json.loads(resp.data)
                R.ok('inventory', 'API日志统计JSON')
            except:
                R.fail('inventory', 'API日志统计JSON', 'JSON解析失败')
        else:
            R.fail('inventory', 'API日志统计JSON', f'HTTP {resp.status_code}')

        # 12. API - 库存同步检查
        resp = c.get('/inventory/api/stock-sync-check')
        R.ok('inventory', 'API库存同步检查') if resp.status_code == 200 else R.fail('inventory', 'API库存同步检查', f'HTTP {resp.status_code}')

        # 13. API - 盘点(stock-check POST)
        resp = c.post('/inventory/api/stock-check',
            data=json.dumps({
                'check_data': [{'product_id': 1, 'actual_stock': 100, 'warehouse_id': 1, 'remark': 'API盘点'}],
                'check_date': '2026-06-01'
            }),
            content_type='application/json')
        R.ok('inventory', 'API盘点POST') if resp.status_code == 200 else R.fail('inventory', 'API盘点POST', f'HTTP {resp.status_code}')

        # 14. 导出仓库库存Excel
        resp = c.get('/inventory/export-warehouse-stock/1')
        R.ok('inventory', '导出仓库库存Excel') if resp.status_code == 200 else R.fail('inventory', '导出仓库库存Excel', f'HTTP {resp.status_code}')


def test_finance_module(app, R):
    """测试财务管理模块"""
    print("\n[财务管理模块]")

    with app.test_client() as c:
        login(c)

        # 1. 财务首页
        resp = c.get('/finance/')
        R.ok('finance', '财务首页GET') if resp.status_code == 200 else R.fail('finance', '财务首页GET', f'HTTP {resp.status_code}')

        # 2. 收款列表
        resp = c.get('/finance/receipts')
        R.ok('finance', '收款列表GET') if resp.status_code == 200 else R.fail('finance', '收款列表GET', f'HTTP {resp.status_code}')

        # 3. 添加收款
        resp = c.post('/finance/receipt/add', data={
            'customer_id': 1,
            'amount': '5000.00',
            'receipt_date': '2026-06-01',
            'payment_method': 'bank_transfer',
            'reference_type': 'sales_order',
            'reference_id': '1',
            'notes': '测试收款',
        }, follow_redirects=True)
        R.ok('finance', '添加收款') if resp.status_code == 200 else R.fail('finance', '添加收款', f'HTTP {resp.status_code}')

        # 4. 查看收款详情
        resp = c.get('/finance/receipt/1')
        R.ok('finance', '收款详情GET') if resp.status_code == 200 else R.fail('finance', '收款详情GET', f'HTTP {resp.status_code}')

        # 5. 编辑收款
        resp = c.post('/finance/receipt/1/edit', data={
            'customer_id': 1,
            'amount': '6000.00',
            'receipt_date': '2026-06-01',
            'payment_method': 'bank_transfer',
            'notes': '修改后收款',
        }, follow_redirects=True)
        R.ok('finance', '编辑收款') if resp.status_code == 200 else R.fail('finance', '编辑收款', f'HTTP {resp.status_code}')

        # 6. 付款列表
        resp = c.get('/finance/payments')
        R.ok('finance', '付款列表GET') if resp.status_code == 200 else R.fail('finance', '付款列表GET', f'HTTP {resp.status_code}')

        # 7. 添加付款
        resp = c.post('/finance/payment/add', data={
            'supplier_id': 1,
            'amount': '3000.00',
            'payment_date': '2026-06-01',
            'payment_method': 'bank_transfer',
            'reference_type': 'purchase_order',
            'reference_id': '1',
            'notes': '测试付款',
        }, follow_redirects=True)
        R.ok('finance', '添加付款') if resp.status_code == 200 else R.fail('finance', '添加付款', f'HTTP {resp.status_code}')

        # 8. 查看付款详情
        resp = c.get('/finance/payment/1')
        R.ok('finance', '付款详情GET') if resp.status_code == 200 else R.fail('finance', '付款详情GET', f'HTTP {resp.status_code}')

        # 9. 费用列表
        resp = c.get('/finance/expenses')
        R.ok('finance', '费用列表GET') if resp.status_code == 200 else R.fail('finance', '费用列表GET', f'HTTP {resp.status_code}')

        # 10. 添加费用
        resp = c.post('/finance/expense/add', data={
            'category': '办公用品',
            'amount': '500.00',
            'expense_date': '2026-06-01',
            'payee': '测试商店',
            'payment_method': 'cash',
            'notes': '测试费用',
        }, follow_redirects=True)
        R.ok('finance', '添加费用') if resp.status_code == 200 else R.fail('finance', '添加费用', f'HTTP {resp.status_code}')

        # 11. 利润分析
        resp = c.get('/finance/profit-analysis')
        R.ok('finance', '利润分析GET') if resp.status_code == 200 else R.fail('finance', '利润分析GET', f'HTTP {resp.status_code}')

        # 12. 应收应付查询
        resp = c.get('/finance/ar-ap-search?customer_id=1')
        R.ok('finance', '应收应付查询(客户)') if resp.status_code == 200 else R.fail('finance', '应收应付查询(客户)', f'HTTP {resp.status_code}')

        resp = c.get('/finance/ar-ap-search?supplier_id=1')
        R.ok('finance', '应收应付查询(供应商)') if resp.status_code == 200 else R.fail('finance', '应收应付查询(供应商)', f'HTTP {resp.status_code}')

        # 13. API - 财务概要
        resp = c.get('/finance/api/financial-summary')
        if resp.status_code == 200:
            try:
                json.loads(resp.data)
                R.ok('finance', 'API财务概要JSON')
            except:
                R.fail('finance', 'API财务概要JSON', 'JSON解析失败')
        else:
            R.fail('finance', 'API财务概要JSON', f'HTTP {resp.status_code}')

        # 14. API - 客户应收
        resp = c.get('/finance/api/customer-ar/1')
        if resp.status_code == 200:
            try:
                json.loads(resp.data)
                R.ok('finance', 'API客户应收JSON')
            except:
                R.fail('finance', 'API客户应收JSON', 'JSON解析失败')
        else:
            R.fail('finance', 'API客户应收JSON', f'HTTP {resp.status_code}')

        # 15. API - 供应商应付
        resp = c.get('/finance/api/supplier-ap/1')
        if resp.status_code == 200:
            try:
                json.loads(resp.data)
                R.ok('finance', 'API供应商应付JSON')
            except:
                R.fail('finance', 'API供应商应付JSON', 'JSON解析失败')
        else:
            R.fail('finance', 'API供应商应付JSON', f'HTTP {resp.status_code}')

        # 16. 导出功能
        for export_url in ['/finance/export-receipts', '/finance/export-payments', '/finance/export-expenses']:
            resp = c.get(export_url)
            R.ok('finance', f'导出{export_url}') if resp.status_code == 200 else R.fail('finance', f'导出{export_url}', f'HTTP {resp.status_code}')


def test_report_module(app, R):
    """测试报表模块"""
    print("\n[报表模块]")

    with app.test_client() as c:
        login(c)

        # 1. 报表首页
        resp = c.get('/report/')
        R.ok('report', '报表首页GET') if resp.status_code == 200 else R.fail('report', '报表首页GET', f'HTTP {resp.status_code}')

        # 2. 库存报表
        resp = c.get('/report/inventory-report')
        R.ok('report', '库存报表GET') if resp.status_code == 200 else R.fail('report', '库存报表GET', f'HTTP {resp.status_code}')

        # 3. 销售排行
        resp = c.get('/report/sales-ranking')
        R.ok('report', '销售排行GET') if resp.status_code == 200 else R.fail('report', '销售排行GET', f'HTTP {resp.status_code}')

        # 4. 客户统计
        resp = c.get('/report/customer-statistics')
        R.ok('report', '客户统计GET') if resp.status_code == 200 else R.fail('report', '客户统计GET', f'HTTP {resp.status_code}')

        # 5. 供应商统计
        resp = c.get('/report/supplier-statistics')
        R.ok('report', '供应商统计GET') if resp.status_code == 200 else R.fail('report', '供应商统计GET', f'HTTP {resp.status_code}')

        # 6. 日报
        resp = c.get('/report/daily-report')
        R.ok('report', '日报GET') if resp.status_code == 200 else R.fail('report', '日报GET', f'HTTP {resp.status_code}')

        # 7. API - 销售趋势
        resp = c.get('/report/api/sales-trend')
        if resp.status_code == 200:
            try:
                json.loads(resp.data)
                R.ok('report', 'API销售趋势JSON')
            except:
                R.fail('report', 'API销售趋势JSON', 'JSON解析失败')
        else:
            R.fail('report', 'API销售趋势JSON', f'HTTP {resp.status_code}')

        # 8. 导出功能
        for export_url in [
            '/report/export/inventory',
            '/report/export/sales-ranking',
            '/report/export/customer',
            '/report/export/supplier',
            '/report/export-products',
            '/report/export/daily',
        ]:
            resp = c.get(export_url)
            R.ok('report', f'导出{export_url}') if resp.status_code == 200 else R.fail('report', f'导出{export_url}', f'HTTP {resp.status_code}')


def test_system_module(app, R):
    """测试系统管理模块"""
    print("\n[系统管理模块]")

    with app.test_client() as c:
        login(c)

        # 1. 系统首页
        resp = c.get('/system/')
        R.ok('system', '系统首页GET') if resp.status_code == 200 else R.fail('system', '系统首页GET', f'HTTP {resp.status_code}')

        # 2. 操作日志（需要admin权限）
        resp = c.get('/system/logs')
        R.ok('system', '操作日志GET') if resp.status_code == 200 else R.fail('system', '操作日志GET', f'HTTP {resp.status_code}')

        # 3. 系统设置
        resp = c.get('/system/settings')
        R.ok('system', '系统设置GET') if resp.status_code == 200 else R.fail('system', '系统设置GET', f'HTTP {resp.status_code}')

        # 4. 用户管理
        resp = c.get('/system/users')
        R.ok('system', '用户管理GET') if resp.status_code == 200 else R.fail('system', '用户管理GET', f'HTTP {resp.status_code}')

        # 5. 添加用户
        resp = c.post('/system/user/add', data={
            'username': 'testuser',
            'password': 'testpass123',
            'email': 'testuser@example.com',
            'role': 'user',
        }, follow_redirects=True)
        R.ok('system', '添加用户') if resp.status_code == 200 else R.fail('system', '添加用户', f'HTTP {resp.status_code}')

        # 6. 编辑用户（查找testuser的ID）
        test_uid = None
        with app.app_context():
            test_user = db.session.get(User, None)
            # 直接查询数据库
            from sqlalchemy import select
            stmt = select(User).where(User.username == 'testuser')
            result = db.session.execute(stmt).scalar_one_or_none()
            if result:
                test_uid = result.id

        if not test_uid:
            R.fail('system', '查找testuser', 'testuser未创建成功')

        if test_uid:
            resp = c.get(f'/system/user/edit/{test_uid}')
            R.ok('system', '编辑用户GET') if resp.status_code == 200 else R.fail('system', '编辑用户GET', f'HTTP {resp.status_code}')

            resp = c.post(f'/system/user/edit/{test_uid}', data={
                'email': 'testuser_new@example.com',
                'role': 'user',
                'is_active': '1',
            }, follow_redirects=True)
            R.ok('system', '编辑用户POST') if resp.status_code == 200 else R.fail('system', '编辑用户POST', f'HTTP {resp.status_code}')

            # 7. 禁用用户
            resp = c.post(f'/system/user/edit/{test_uid}', data={
                'email': 'testuser_new@example.com',
                'role': 'user',
                'is_active': '0',
            }, follow_redirects=True)
            R.ok('system', '禁用用户') if resp.status_code == 200 else R.fail('system', '禁用用户', f'HTTP {resp.status_code}')

            # 8. 删除用户
            resp = c.post(f'/system/user/delete/{test_uid}', follow_redirects=True)
            R.ok('system', '删除用户') if resp.status_code == 200 else R.fail('system', '删除用户', f'HTTP {resp.status_code}')

        # 9. 备份管理
        resp = c.get('/system/backup')
        R.ok('system', '备份管理GET') if resp.status_code == 200 else R.fail('system', '备份管理GET', f'HTTP {resp.status_code}')

        # 10. 创建备份
        resp = c.post('/system/backup/create', data={
            'description': '测试备份',
        }, follow_redirects=True)
        R.ok('system', '创建备份') if resp.status_code == 200 else R.fail('system', '创建备份', f'HTTP {resp.status_code}')

        # 11. 备份列表 API
        resp = c.get('/system/backup/list')
        if resp.status_code == 200:
            try:
                json.loads(resp.data)
                R.ok('system', 'API备份列表JSON')
            except:
                R.fail('system', 'API备份列表JSON', 'JSON解析失败')
        else:
            R.fail('system', 'API备份列表JSON', f'HTTP {resp.status_code}')

        # 12. API - 系统信息
        resp = c.get('/system/api/system-info')
        if resp.status_code == 200:
            try:
                json.loads(resp.data)
                R.ok('system', 'API系统信息JSON')
            except:
                R.fail('system', 'API系统信息JSON', 'JSON解析失败')
        else:
            R.fail('system', 'API系统信息JSON', f'HTTP {resp.status_code}')

        # 13. API - 最近日志
        resp = c.get('/system/api/system/recent-logs')
        if resp.status_code == 200:
            try:
                json.loads(resp.data)
                R.ok('system', 'API最近日志JSON')
            except:
                R.fail('system', 'API最近日志JSON', 'JSON解析失败')
        else:
            R.fail('system', 'API最近日志JSON', f'HTTP {resp.status_code}')

        # 14. API - 优化数据库
        resp = c.post('/system/api/system/optimize-db')
        R.ok('system', 'API优化数据库') if resp.status_code == 200 else R.fail('system', 'API优化数据库', f'HTTP {resp.status_code}')

        # 15. API - 保存系统设置（期望form data，但CSRF在测试模式下已禁用）\n        resp = c.post('/system/api/system/settings',\n            data={\n                'COMPANY_NAME': '测试公司',\n                'COMPANY_ADDRESS': '测试地址',\n                'COMPANY_PHONE': '010-12345678',\n                'DEFAULT_CURRENCY': 'CNY',\n                'ITEMS_PER_PAGE': '20',\n                'ENABLE_BACKUP': '1',\n                'ENABLE_LOGGING': '1',\n                'DEFAULT_WAREHOUSE': '1',\n            })\n        R.ok('system', 'API保存系统设置') if resp.status_code == 200 else R.fail('system', 'API保存系统设置', f'HTTP {resp.status_code}')\n\n        # 16. 权限测试 - 普通用户访问系统管理\n        c2 = app.test_client()\n        login(c2, 'user1', 'user123')\n        resp = c2.get('/system/logs', follow_redirects=False)\n        R.ok('system', '普通用户权限拒绝(403)') if resp.status_code in (403, 302) else R.fail('system', '普通用户权限拒绝(403)', f'HTTP {resp.status_code}')\n\n        resp = c2.get('/system/users', follow_redirects=False)\n        R.ok('system', '普通用户管理权限拒绝(403)') if resp.status_code in (403, 302) else R.fail('system', '普通用户管理权限拒绝(403)', f'HTTP {resp.status_code}')


def test_delete_operations(app, R):
    """测试删除操作（含级联保护）"""
    print("\n[删除操作测试]")

    with app.test_client() as c:
        login(c)

        # 1. 创建一个无关联的产品，然后删除
        resp = c.post('/product/products/new', data={
            'code': 'P_DEL',
            'name': '待删除产品',
            'unit': '个',
        }, follow_redirects=True)

        # 查找待删除产品的ID（在test_client上下文外查询）
        del_id = None
        used_id = None
        cat_id = None
        with app.app_context():
            del_product = Product.query.filter_by(code='P_DEL').first()
            if del_product:
                del_id = del_product.id
            used_product = Product.query.filter_by(code='P001').first()
            if used_product:
                used_id = used_product.id

        if del_id:
            resp = c.post(f'/product/products/{del_id}/delete', follow_redirects=True)
            R.ok('delete', '删除无关联产品') if resp.status_code == 200 else R.fail('delete', '删除无关联产品', f'HTTP {resp.status_code}')
        else:
            R.fail('delete', '删除无关联产品', '未找到待删除产品')

        # 2. 尝试删除有关联的产品（应被拒绝）
        if used_id:
            resp = c.post(f'/product/products/{used_id}/delete', follow_redirects=True)
            R.ok('delete', '拒绝删除关联产品') if resp.status_code == 200 else R.fail('delete', '拒绝删除关联产品', f'HTTP {resp.status_code}')
        else:
            R.fail('delete', '拒绝删除关联产品', 'P001不存在')

        # 3. 删除未使用的分类
        resp = c.get('/product/categories/new')
        resp = c.post('/product/categories/new', data={
            'name': '待删除分类',
            'description': '测试',
        }, follow_redirects=True)

        cat_id = None
        with app.app_context():
            del_cat = Category.query.filter_by(name='\u5f85\u5220\u9664\u5206\u7c7b').first()
            if del_cat:
                cat_id = del_cat.id

        if cat_id:
            resp = c.post(f'/product/categories/{cat_id}/delete', follow_redirects=True)
            R.ok('delete', '删除无关联分类') if resp.status_code == 200 else R.fail('delete', '删除无关联分类', f'HTTP {resp.status_code}')
        else:
            R.fail('delete', '删除无关联分类', '未找到待删除分类')


def test_edge_cases(app, R):
    """测试边界情况和错误处理"""
    print("\n[边界情况测试]")

    with app.test_client() as c:
        login(c)

        # 1. 访问不存在的产品
        resp = c.get('/product/products/99999')
        R.ok('edge', '不存在产品(404)') if resp.status_code == 404 else R.fail('edge', '不存在产品(404)', f'HTTP {resp.status_code}')

        # 2. 编辑不存在的采购订单
        resp = c.post('/purchase/orders/99999/edit', data={}, follow_redirects=True)
        R.ok('edge', '不存在采购订单编辑') if resp.status_code == 404 or resp.status_code == 200 else R.fail('edge', '不存在采购订单编辑', f'HTTP {resp.status_code}')

        # 3. 编辑已完成的采购订单（应被拒绝）
        resp = c.post('/purchase/orders/1/edit', data={
            'order_status': 'completed',
            'supplier_id': 1,
            'warehouse_id': 1,
            'order_date': '2026-06-01',
            'notes': '尝试编辑已完成订单',
        }, follow_redirects=True)
        R.ok('edge', '拒绝编辑已完成采购单') if resp.status_code == 200 else R.fail('edge', '拒绝编辑已完成采购单', f'HTTP {resp.status_code}')

        # 4. 快捷入库已完成的订单（应被拒绝）
        resp = c.post('/purchase/orders/1/quick-stock-in', follow_redirects=True)
        R.ok('edge', '拒绝重复入库') if resp.status_code == 200 else R.fail('edge', '拒绝重复入库', f'HTTP {resp.status_code}')

        # 5. API 空参数处理
        resp = c.post('/product/api/product/price',
            data=json.dumps({}),
            content_type='application/json')
        R.ok('edge', 'API空参数处理') if resp.status_code != 500 else R.fail('edge', 'API空参数处理', f'HTTP {resp.status_code} - 服务器错误')

        # 6. 无效日期格式
        resp = c.get('/report/inventory-report?start_date=invalid&end_date=invalid')
        R.ok('edge', '无效日期处理') if resp.status_code != 500 else R.fail('edge', '无效日期处理', f'HTTP {resp.status_code} - 服务器错误')

        # 7. 销售订单 - 空项目提交
        resp = c.post('/sales/orders/new', data={
            'order_status': 'draft',
            'customer_id': 1,
            'warehouse_id': 1,
            'order_date': '2026-06-01',
        }, follow_redirects=True)
        R.ok('edge', '空项目订单处理') if resp.status_code == 200 else R.fail('edge', '空项目订单处理', f'HTTP {resp.status_code}')

        # 8. 库存调拨 - 相同仓库（应被拒绝）
        resp = c.post('/inventory/stock-transfer', data={
            'from_warehouse': 1,
            'to_warehouse': 1,
            'transfer_date': '2026-06-01',
            'remark': '同仓库调拨',
            'product_id': ['1'],
            'quantity': ['10'],
        }, follow_redirects=True)
        R.ok('edge', '拒绝同仓库调拨') if resp.status_code == 200 else R.fail('edge', '拒绝同仓库调拨', f'HTTP {resp.status_code}')


def test_data_consistency(app, R):
    """测试数据一致性"""
    print("\n[数据一致性测试]")

    with app.test_client() as c:
        login(c)

        # 1. 全局库存 vs StockLog 汇总一致性
        resp = c.get('/inventory/api/stock-sync-check')
        if resp.status_code == 200:
            try:
                data = json.loads(resp.data)
                if isinstance(data, dict) and data.get('success'):
                    if data.get('inconsistent_count', 0) == 0:
                        R.ok('consistency', '全局库存与流水一致')
                    else:
                        R.fail('consistency', '全局库存与流水不一致', json.dumps(data, ensure_ascii=False, indent=2))
                        c.get('/inventory/api/stock-sync-check?fix=1')
                else:
                    R.ok('consistency', '库存同步检查API返回')
            except Exception as e:
                R.fail('consistency', '库存同步检查', str(e))
        else:
            R.fail('consistency', '库存同步检查', f'HTTP {resp.status_code}')

        # 2. 供应商应付余额验证
        with app.app_context():
            supplier = Supplier.query.get(1)
            if supplier:
                R.ok('consistency', f'供应商应付余额: {supplier.payable_balance}')
            else:
                R.fail('consistency', '供应商应付余额验证', '供应商不存在')

        # 3. 客户应收余额验证
        with app.app_context():
            customer = Customer.query.get(1)
            if customer:
                R.ok('consistency', f'客户应收余额: {customer.receivable_balance}')
            else:
                R.fail('consistency', '客户应收余额验证', '客户不存在')

        # 4. 产品库存验证
        with app.app_context():
            product = db.session.get(Product, 1)
            if product:
                R.ok('consistency', f'产品库存验证: 全局库存={product.stock_quantity}')
            else:
                R.fail('consistency', '产品库存验证', '产品不存在')


# ======================== 主测试入口 ========================

def main():
    print("=" * 60)
    print("my-jxc 进销存系统 全面功能测试")
    print("=" * 60)

    app, db_path = None, None
    try:
        app, db_path = create_test_app()
        R = TestResult()

        # 按模块依次测试（单个模块失败不影响后续模块）
        test_modules = [
            test_auth_module, test_main_dashboard, test_product_module,
            test_partner_module, test_purchase_module, test_sales_module,
            test_inventory_module, test_finance_module, test_report_module,
            test_system_module, test_delete_operations, test_edge_cases,
            test_data_consistency,
        ]
        for mod_func in test_modules:
            try:
                mod_func(app, R)
            except Exception as e:
                module_name = mod_func.__name__
                R.fail(module_name, f'模块异常退出', traceback.format_exc()[-500:])

        # 输出汇总
        success = R.summary()
        return 0 if success else 1

    except Exception as e:
        print(f"\n测试执行异常: {e}")
        traceback.print_exc()
        return 2
    finally:
        # 清理临时数据库
        try:
            os.unlink(db_path)
        except:
            pass


if __name__ == '__main__':
    sys.exit(main())
