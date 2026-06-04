"""
集成测试 — 端到端业务流程
"""
import pytest
from datetime import date
from decimal import Decimal

from app import db
from app.models import (
    Product, PurchaseOrder, SalesOrder, StockIn, StockOut,
    StockLog, Receipt, Payment, Customer, Supplier,
)
from tests.factories import (
    create_supplier, create_customer, create_warehouse, create_product,
)
from tests.helpers import get_page, post_page


def test_purchase_to_payment_flow(app, authenticated_client, db_session):
    """采购完整流程：创建订单 → 入库 → 付款 → 验证库存和财务"""
    # 1. 创建供应商和商品
    supplier = create_supplier(code='INT_SUP01', name='集成供应商')
    warehouse = create_warehouse(code='INT_WH01', name='集成仓库')
    product = create_product(code='INT_PROD01', name='集成商品', stock_quantity=0)

    # 2. 创建采购订单
    resp = authenticated_client.post('/purchase/orders/new', data={
        'supplier_id': str(supplier.id),
        'warehouse_id': str(warehouse.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'action': 'save',
        'order_status': 'confirmed',
        'product_id[]': [str(product.id)],
        'quantity[]': ['100'],
        'unit_price[]': ['50.00'],
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 3. 获取订单
    order = PurchaseOrder.query.filter_by(supplier_id=supplier.id).first()
    assert order is not None
    assert order.total_amount == Decimal('5000.00')

    # 4. 快速入库
    resp = authenticated_client.post(
        f'/purchase/orders/{order.id}/quick-stock-in', follow_redirects=True
    )
    assert resp.status_code == 200

    # 5. 验证库存增加
    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('100')

    # 6. 添加付款
    resp = authenticated_client.post('/finance/payment/add', data={
        'supplier_id': str(supplier.id),
        'amount': '5000.00',
        'payment_date': date.today().strftime('%Y-%m-%d'),
        'payment_method': 'bank_transfer',
        'reference_type': 'purchase_order',
        'reference_id': str(order.id),
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 7. 验证付款记录
    with app.app_context():
        payment = Payment.query.filter_by(supplier_id=supplier.id).first()
        assert payment is not None
        assert payment.amount == Decimal('5000.00')


def test_sales_to_receipt_flow(app, authenticated_client, db_session):
    """销售完整流程：创建订单 → 出库 → 收款 → 验证库存和财务"""
    # 1. 创建客户和商品（有库存）
    customer = create_customer(code='INT_CUS01', name='集成客户')
    warehouse = create_warehouse(code='INT_WH02', name='集成仓库2')
    product = create_product(code='INT_PROD02', name='集成商品2', stock_quantity=200)

    # 2. 创建销售订单
    resp = authenticated_client.post('/sales/orders/new', data={
        'customer_id': str(customer.id),
        'warehouse_id': str(warehouse.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'action': 'save',
        'order_status': 'confirmed',
        'product_id[]': [str(product.id)],
        'quantity[]': ['50'],
        'unit_price[]': ['100.00'],
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 3. 获取订单
    order = SalesOrder.query.filter_by(customer_id=customer.id).first()
    assert order is not None
    assert order.total_amount == Decimal('5000.00')

    # 4. 快速出库
    resp = authenticated_client.post(
        f'/sales/orders/{order.id}/quick-stock-out', follow_redirects=True
    )
    assert resp.status_code == 200

    # 5. 验证库存减少
    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('150')

    # 6. 添加收款
    resp = authenticated_client.post('/finance/receipt/add', data={
        'customer_id': str(customer.id),
        'amount': '5000.00',
        'receipt_date': date.today().strftime('%Y-%m-%d'),
        'payment_method': 'bank_transfer',
        'reference_type': 'sales_order',
        'reference_id': str(order.id),
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 7. 验证收款记录
    with app.app_context():
        receipt = Receipt.query.filter_by(customer_id=customer.id).first()
        assert receipt is not None
        assert receipt.amount == Decimal('5000.00')


def test_inventory_check_flow(app, authenticated_client, db_session):
    """库存盘点流程：创建商品 → 盘点 → 验证库存和日志"""
    # 1. 创建商品
    warehouse = create_warehouse(code='INT_WH03', name='盘点仓库')
    product = create_product(code='INT_PROD03', name='盘点商品', stock_quantity=100)

    # 2. 执行盘点（盘盈）
    resp = authenticated_client.post('/inventory/stock-check', data={
        'warehouse_id': str(warehouse.id),
        'notes': '集成测试盘点',
        'product_id[]': [str(product.id)],
        'actual_quantity[]': ['120'],
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 3. 验证库存更新
    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('120')

    # 4. 验证日志
    with app.app_context():
        log = StockLog.query.filter_by(
            product_id=product.id, change_type='check_in'
        ).first()
        assert log is not None
        assert log.quantity == Decimal('20')


def test_stock_adjust_flow(app, authenticated_client, db_session):
    """库存调整流程：创建商品 → 调整入库 → 调整出库 → 验证"""
    # 1. 创建商品
    warehouse = create_warehouse(code='INT_WH04', name='调整仓库')
    product = create_product(code='INT_PROD04', name='调整商品', stock_quantity=50)

    # 2. 调整入库
    resp = authenticated_client.post('/inventory/stock-adjust', data={
        'product_id': str(product.id),
        'warehouse_id': str(warehouse.id),
        'adjust_type': 'adjust_in',
        'quantity': '30',
        'notes': '调整入库测试',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 3. 验证库存
    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('80')

    # 4. 调整出库
    resp = authenticated_client.post('/inventory/stock-adjust', data={
        'product_id': str(product.id),
        'warehouse_id': str(warehouse.id),
        'adjust_type': 'adjust_out',
        'quantity': '10',
        'notes': '调整出库测试',
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 5. 验证最终库存
    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('70')
