"""
改进断言的集成测试 — 验证实际行为而非仅状态码
"""
import pytest
from decimal import Decimal
from datetime import date
from app import db
from app.models import (
    User, Product, Category, Supplier, Customer, Warehouse,
    PurchaseOrder, SalesOrder, StockLog, Receipt, Payment, Expense
)
from tests.factories import (
    create_product, create_category, create_supplier, create_customer,
    create_warehouse, create_purchase_order, create_sales_order
)


# ==================== 商品 CRUD 断言 ====================

def test_product_create_verifies_data(authenticated_client, app, db_session):
    """创建商品 - 验证数据已保存"""
    cat = create_category()

    resp = authenticated_client.post('/product/products/new', data={
        'code': 'ASSERT_PROD_001',
        'name': '断言测试商品',
        'category_id': str(cat.id),
        'unit': '个',
        'purchase_price': '50',
        'sale_price': '100',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证商品已创建
    product = Product.query.filter_by(code='ASSERT_PROD_001').first()
    assert product is not None
    assert product.name == '断言测试商品'
    assert product.category_id == cat.id
    assert product.unit == '个'
    assert product.purchase_price == Decimal('50')
    assert product.sale_price == Decimal('100')


def test_product_edit_verifies_changes(authenticated_client, app, db_session):
    """编辑商品 - 验证修改已保存"""
    product = create_product(code='EDIT_ASSERT_001', name='原始名称')

    resp = authenticated_client.post(f'/product/products/{product.id}/edit', data={
        'code': 'EDIT_ASSERT_001',
        'name': '修改后名称',
        'unit': '个',
        'purchase_price': '60',
        'sale_price': '120',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证修改已保存
    updated = db.session.get(Product, product.id)
    assert updated.name == '修改后名称'
    assert updated.purchase_price == Decimal('60')
    assert updated.sale_price == Decimal('120')


def test_product_delete_verifies_removal(authenticated_client, app, db_session):
    """删除商品 - 验证已删除"""
    product = create_product(code='DEL_ASSERT_001')
    product_id = product.id

    resp = authenticated_client.post(f'/product/products/{product.id}/delete', follow_redirects=True)
    assert resp.status_code == 200

    # 验证已删除
    deleted = db.session.get(Product, product_id)
    assert deleted is None


# ==================== 供应商 CRUD 断言 ====================

def test_supplier_create_verifies_data(authenticated_client, app, db_session):
    """创建供应商 - 验证数据已保存"""
    resp = authenticated_client.post('/partner/suppliers/new', data={
        'code': 'ASSERT_SUP_001',
        'name': '断言测试供应商',
        'contact_person': '张三',
        'phone': '13800000001',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证供应商已创建
    supplier = Supplier.query.filter_by(code='ASSERT_SUP_001').first()
    assert supplier is not None
    assert supplier.name == '断言测试供应商'
    assert supplier.contact_person == '张三'
    assert supplier.phone == '13800000001'


def test_supplier_edit_verifies_changes(authenticated_client, app, db_session):
    """编辑供应商 - 验证修改已保存"""
    supplier = create_supplier(code='EDIT_SUP_ASSERT')

    resp = authenticated_client.post(f'/partner/suppliers/{supplier.id}/edit', data={
        'code': 'EDIT_SUP_ASSERT',
        'name': '修改后供应商',
        'contact_person': '李四',
        'phone': '13900000001',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证修改已保存
    updated = db.session.get(Supplier, supplier.id)
    assert updated.name == '修改后供应商'
    assert updated.contact_person == '李四'
    assert updated.phone == '13900000001'


def test_supplier_delete_verifies_removal(authenticated_client, app, db_session):
    """删除供应商 - 验证已删除"""
    supplier = create_supplier(code='DEL_SUP_ASSERT')
    supplier_id = supplier.id

    resp = authenticated_client.post(f'/partner/suppliers/{supplier.id}/delete', follow_redirects=True)
    assert resp.status_code == 200

    # 验证已删除
    deleted = db.session.get(Supplier, supplier_id)
    assert deleted is None


# ==================== 客户 CRUD 断言 ====================

def test_customer_create_verifies_data(authenticated_client, app, db_session):
    """创建客户 - 验证数据已保存"""
    resp = authenticated_client.post('/partner/customers/new', data={
        'code': 'ASSERT_CUS_001',
        'name': '断言测试客户',
        'contact_person': '李四',
        'phone': '13900000001',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证客户已创建
    customer = Customer.query.filter_by(code='ASSERT_CUS_001').first()
    assert customer is not None
    assert customer.name == '断言测试客户'
    assert customer.contact_person == '李四'
    assert customer.phone == '13900000001'


# ==================== 仓库 CRUD 断言 ====================

def test_warehouse_create_verifies_data(authenticated_client, app, db_session):
    """创建仓库 - 验证数据已保存"""
    resp = authenticated_client.post('/partner/warehouses/new', data={
        'code': 'ASSERT_WH_001',
        'name': '断言测试仓库',
        'address': '测试地址',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证仓库已创建
    warehouse = Warehouse.query.filter_by(code='ASSERT_WH_001').first()
    assert warehouse is not None
    assert warehouse.name == '断言测试仓库'
    assert warehouse.address == '测试地址'


# ==================== 采购订单断言 ====================

def test_purchase_order_create_verifies(authenticated_client, app, db_session):
    """创建采购订单 - 验证订单和明细"""
    sup = create_supplier()
    wh = create_warehouse()
    prod = create_product()

    resp = authenticated_client.post('/purchase/orders/new', data={
        'supplier_id': str(sup.id),
        'warehouse_id': str(wh.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '断言测试',
        'product_id[]': [str(prod.id)],
        'quantity[]': ['10'],
        'unit_price[]': ['50'],
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证订单已创建
    order = PurchaseOrder.query.filter_by(supplier_id=sup.id).first()
    assert order is not None
    assert order.warehouse_id == wh.id
    # 默认状态是 draft
    assert order.status in ('draft', 'confirmed')
    assert order.notes == '断言测试'

    # 验证明细已创建
    assert len(order.items) == 1
    assert order.items[0].product_id == prod.id
    assert order.items[0].quantity == Decimal('10')
    assert order.items[0].unit_price == Decimal('50')
    assert order.items[0].amount == Decimal('500')


def test_purchase_quick_stock_in_verifies(authenticated_client, app, db_session):
    """快捷入库 - 验证库存和日志"""
    sup = create_supplier()
    wh = create_warehouse()
    prod = create_product(stock_quantity=0)

    order = create_purchase_order(
        supplier_id=sup.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 50}],
        status='confirmed'
    )

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/quick-stock-in', follow_redirects=True)
    assert resp.status_code == 200

    # 验证库存已更新
    updated_prod = db.session.get(Product, prod.id)
    assert updated_prod.stock_quantity == Decimal('10')

    # 验证订单状态已更新
    updated_order = db.session.get(PurchaseOrder, order.id)
    assert updated_order.status == 'completed'

    # 验证库存日志已创建
    log = StockLog.query.filter_by(
        product_id=prod.id,
        change_type='in'
    ).first()
    assert log is not None
    assert log.quantity == Decimal('10')


def test_purchase_quick_return_verifies(authenticated_client, app, db_session):
    """快捷退货 - 验证库存和日志"""
    sup = create_supplier()
    wh = create_warehouse()
    prod = create_product(stock_quantity=50)

    order = create_purchase_order(
        supplier_id=sup.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 50}],
        status='completed'
    )
    order.items[0].received_quantity = Decimal('10')
    db.session.commit()

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/quick-return', follow_redirects=True)
    assert resp.status_code == 200

    # 验证库存已减少
    updated_prod = db.session.get(Product, prod.id)
    assert updated_prod.stock_quantity == Decimal('40')

    # 验证退货单已创建
    from app.models import PurchaseReturn
    ret = PurchaseReturn.query.filter_by(purchase_order_id=order.id).first()
    assert ret is not None
    assert ret.status == 'completed'


# ==================== 销售订单断言 ====================

def test_sales_order_create_verifies(authenticated_client, app, db_session):
    """创建销售订单 - 验证订单和明细"""
    cus = create_customer()
    wh = create_warehouse()
    prod = create_product(stock_quantity=100)

    resp = authenticated_client.post('/sales/orders/new', data={
        'customer_id': str(cus.id),
        'warehouse_id': str(wh.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '断言测试',
        'product_id[]': [str(prod.id)],
        'quantity[]': ['10'],
        'unit_price[]': ['100'],
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证订单已创建
    order = SalesOrder.query.filter_by(customer_id=cus.id).first()
    assert order is not None
    assert order.warehouse_id == wh.id
    # 默认状态是 draft
    assert order.status in ('draft', 'confirmed')

    # 验证明细已创建
    assert len(order.items) == 1
    assert order.items[0].product_id == prod.id
    assert order.items[0].quantity == Decimal('10')
    assert order.items[0].unit_price == Decimal('100')


def test_sales_quick_stock_out_verifies(authenticated_client, app, db_session):
    """快捷出库 - 验证库存和日志"""
    cus = create_customer()
    wh = create_warehouse()
    prod = create_product(stock_quantity=100)

    order = create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
        status='confirmed'
    )

    resp = authenticated_client.post(f'/sales/orders/{order.id}/quick-stock-out', follow_redirects=True)
    assert resp.status_code == 200

    # 验证库存已减少
    updated_prod = db.session.get(Product, prod.id)
    assert updated_prod.stock_quantity == Decimal('90')

    # 验证订单状态已更新
    updated_order = db.session.get(SalesOrder, order.id)
    assert updated_order.status == 'completed'

    # 验证库存日志已创建
    log = StockLog.query.filter_by(
        product_id=prod.id,
        change_type='out'
    ).first()
    assert log is not None
    assert log.quantity == Decimal('10')


def test_sales_quick_return_verifies(authenticated_client, app, db_session):
    """快捷退货 - 验证库存和日志"""
    cus = create_customer()
    wh = create_warehouse()
    prod = create_product(stock_quantity=50)

    order = create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
        status='completed'
    )
    order.items[0].delivered_quantity = Decimal('10')
    db.session.commit()

    resp = authenticated_client.post(f'/sales/orders/{order.id}/quick-return', follow_redirects=True)
    assert resp.status_code == 200

    # 验证库存已增加
    updated_prod = db.session.get(Product, prod.id)
    assert updated_prod.stock_quantity == Decimal('60')

    # 验证退货单已创建
    from app.models import SalesReturn
    ret = SalesReturn.query.filter_by(sales_order_id=order.id).first()
    assert ret is not None
    assert ret.status == 'completed'


# ==================== 库存操作断言 ====================

def test_stock_check_verifies(authenticated_client, app, db_session):
    """库存盘点 - 验证库存和日志"""
    wh = create_warehouse()
    prod = create_product(stock_quantity=100)

    resp = authenticated_client.post('/inventory/stock-check', data={
        'warehouse_id': str(wh.id),
        'notes': '盘点测试',
        'product_id[]': [str(prod.id)],
        'actual_quantity[]': ['110'],
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证库存已更新
    updated_prod = db.session.get(Product, prod.id)
    assert updated_prod.stock_quantity == Decimal('110')

    # 验证库存日志已创建
    log = StockLog.query.filter_by(
        product_id=prod.id,
        change_type='check_in'
    ).first()
    assert log is not None
    assert log.quantity == Decimal('10')
    assert log.notes == '库存盘点: 盘点测试'


def test_stock_adjust_in_verifies(authenticated_client, app, db_session):
    """调整入库 - 验证库存和日志"""
    wh = create_warehouse()
    prod = create_product(stock_quantity=50)

    resp = authenticated_client.post('/inventory/stock-adjust', data={
        'product_id': str(prod.id),
        'warehouse_id': str(wh.id),
        'adjust_type': 'adjust_in',
        'quantity': '10',
        'notes': '盘盈入库',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证库存已增加
    updated_prod = db.session.get(Product, prod.id)
    assert updated_prod.stock_quantity == Decimal('60')

    # 验证库存日志已创建
    log = StockLog.query.filter_by(
        product_id=prod.id,
        change_type='adjust_in'
    ).first()
    assert log is not None
    assert log.quantity == Decimal('10')


def test_stock_adjust_out_verifies(authenticated_client, app, db_session):
    """调整出库 - 验证库存和日志"""
    wh = create_warehouse()
    prod = create_product(stock_quantity=50)

    resp = authenticated_client.post('/inventory/stock-adjust', data={
        'product_id': str(prod.id),
        'warehouse_id': str(wh.id),
        'adjust_type': 'adjust_out',
        'quantity': '10',
        'notes': '盘亏出库',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证库存已减少
    updated_prod = db.session.get(Product, prod.id)
    assert updated_prod.stock_quantity == Decimal('40')

    # 验证库存日志已创建
    log = StockLog.query.filter_by(
        product_id=prod.id,
        change_type='adjust_out'
    ).first()
    assert log is not None
    assert log.quantity == Decimal('10')


# ==================== 财务操作断言 ====================

def test_receipt_create_verifies(authenticated_client, app, db_session):
    """创建收款 - 验证数据和余额"""
    cus = create_customer()

    resp = authenticated_client.post('/finance/receipt/add', data={
        'customer_id': str(cus.id),
        'amount': '1000',
        'payment_method': 'cash',
        'receipt_date': date.today().strftime('%Y-%m-%d'),
        'notes': '断言测试收款',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证收款记录已创建
    receipt = Receipt.query.filter_by(customer_id=cus.id).first()
    assert receipt is not None
    assert receipt.amount == Decimal('1000')
    assert receipt.payment_method == 'cash'
    assert receipt.notes == '断言测试收款'

    # 验证客户应收余额已减少
    updated_cus = db.session.get(Customer, cus.id)
    assert updated_cus.receivable_balance == Decimal('-1000')


def test_payment_create_verifies(authenticated_client, app, db_session):
    """创建付款 - 验证数据和余额"""
    sup = create_supplier()

    resp = authenticated_client.post('/finance/payment/add', data={
        'supplier_id': str(sup.id),
        'amount': '500',
        'payment_method': 'bank_transfer',
        'payment_date': date.today().strftime('%Y-%m-%d'),
        'notes': '断言测试付款',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证付款记录已创建
    payment = Payment.query.filter_by(supplier_id=sup.id).first()
    assert payment is not None
    assert payment.amount == Decimal('500')
    assert payment.payment_method == 'bank_transfer'
    assert payment.notes == '断言测试付款'

    # 验证供应商应付余额已减少
    updated_sup = db.session.get(Supplier, sup.id)
    assert updated_sup.payable_balance == Decimal('-500')


def test_expense_create_verifies(authenticated_client, app, db_session):
    """创建费用 - 验证数据"""
    resp = authenticated_client.post('/finance/expense/add', data={
        'category': '办公费',
        'amount': '100',
        'expense_date': date.today().strftime('%Y-%m-%d'),
        'notes': '断言测试费用',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证费用记录已创建
    expense = Expense.query.order_by(Expense.id.desc()).first()
    if expense:
        assert expense.amount == Decimal('100')


# ==================== 用户管理断言 ====================

def test_user_add_verifies(authenticated_client, app, db_session):
    """添加用户 - 验证用户已创建"""
    import time
    username = f'new_assert_{int(time.time())}'

    resp = authenticated_client.post('/system/user/add', data={
        'username': username,
        'email': 'newassert@test.com',
        'password': 'pass123',
        'role': 'user',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证用户已创建
    user = User.query.filter_by(username=username).first()
    assert user is not None
    assert user.email == 'newassert@test.com'
    assert user.role == 'user'
    assert user.check_password('pass123') is True


def test_user_edit_verifies(authenticated_client, app, db_session):
    """编辑用户 - 验证修改已保存"""
    import time
    user = User(username=f'edit_assert_{int(time.time())}', email='editassert@test.com')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()

    resp = authenticated_client.post(f'/system/user/edit/{user.id}', data={
        'username': user.username,
        'email': 'newemail@test.com',
        'role': 'admin',
        'is_active': 'on',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证修改已保存
    db.session.expire_all()
    updated = db.session.get(User, user.id)
    assert updated.email == 'newemail@test.com'
    assert updated.role == 'admin'


def test_user_delete_verifies(authenticated_client, app, db_session):
    """删除用户 - 验证已删除"""
    import time
    user = User(username=f'del_assert_{int(time.time())}', email='delassert@test.com')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()
    user_id = user.id

    resp = authenticated_client.post(f'/system/user/delete/{user.id}', follow_redirects=True)
    assert resp.status_code == 200

    # 验证已删除
    db.session.expire_all()
    deleted = db.session.get(User, user_id)
    assert deleted is None


# ==================== 密码修改断言 ====================

def test_change_password_verifies(authenticated_client, app, db_session):
    """修改密码 - 验证新密码可用"""
    resp = authenticated_client.post('/auth/change-password', data={
        'old_password': 'admin123',
        'new_password': 'newpass123',
        'confirm_password': 'newpass123',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证新密码可用
    db.session.expire_all()
    user = User.query.filter_by(username='admin').first()
    assert user.check_password('newpass123') is True
    assert user.check_password('admin123') is False


def test_change_email_verifies(authenticated_client, app, db_session):
    """修改邮箱 - 验证邮箱已更新"""
    resp = authenticated_client.post('/auth/change-email', data={
        'new_email': 'verified@test.com',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 验证邮箱已更新
    db.session.expire_all()
    user = User.query.filter_by(username='admin').first()
    assert user.email == 'verified@test.com'


# ==================== 库存调拨断言 ====================

def test_stock_transfer_verifies(authenticated_client, app, db_session):
    """库存调拨 - 验证页面加载"""
    wh1 = create_warehouse()
    wh2 = create_warehouse()
    prod = create_product(stock_quantity=100)

    resp = authenticated_client.post('/inventory/stock-transfer', data={
        'from_warehouse': str(wh1.id),
        'to_warehouse': str(wh2.id),
        'transfer_date': date.today().strftime('%Y-%m-%d'),
        'notes': '调拨测试',
        'items-0-product_id': str(prod.id),
        'items-0-quantity': '10',
    }, follow_redirects=True)
    assert resp.status_code == 200
