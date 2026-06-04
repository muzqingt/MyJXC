"""
Services 层单元测试
"""
import pytest
from datetime import date
from decimal import Decimal

from app import db
from app.models import PurchaseOrder, SalesOrder, Product, StockLog
from app.services import PurchaseService, SalesService, InventoryService
from tests.factories import (
    create_supplier, create_customer, create_warehouse, create_product,
)


# ==================== PurchaseService ====================

def test_purchase_service_create_order(app, db_session):
    """PurchaseService.create_order 创建订单"""
    supplier = create_supplier(code='SVC_SUP01', name='服务供应商')
    warehouse = create_warehouse(code='SVC_WH01', name='服务仓库')
    product = create_product(code='SVC_PROD01', name='服务商品')

    order, error = PurchaseService.create_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        order_date=date.today().strftime('%Y-%m-%d'),
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 50}],
        user_id=1,
    )

    assert error is None
    assert order is not None
    assert order.total_amount == Decimal('500.00')


def test_purchase_service_create_order_validation(app, db_session):
    """PurchaseService.create_order 验证失败"""
    order, error = PurchaseService.create_order(
        supplier_id=None,
        warehouse_id=1,
        order_date='2026-06-04',
        items=[],
    )

    assert order is None
    assert error is not None


def test_purchase_service_quick_stock_in(app, db_session):
    """PurchaseService.quick_stock_in 快速入库"""
    supplier = create_supplier(code='SVC_SUP02', name='入库供应商')
    warehouse = create_warehouse(code='SVC_WH02', name='入库仓库')
    product = create_product(code='SVC_PROD02', name='入库商品', stock_quantity=0)

    order, _ = PurchaseService.create_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        order_date=date.today().strftime('%Y-%m-%d'),
        items=[{'product_id': product.id, 'quantity': 20, 'unit_price': 30}],
        user_id=1,
    )
    db.session.commit()

    success, error = PurchaseService.quick_stock_in(order.id, user_id=1)
    db.session.commit()

    assert success is True
    assert error is None

    p = db.session.get(Product, product.id)
    assert p.stock_quantity == Decimal('20')


# ==================== SalesService ====================

def test_sales_service_create_order(app, db_session):
    """SalesService.create_order 创建订单"""
    customer = create_customer(code='SVC_CUS01', name='服务客户')
    warehouse = create_warehouse(code='SVC_WH03', name='服务仓库3')
    product = create_product(code='SVC_PROD03', name='服务商品3')

    order, error = SalesService.create_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        order_date=date.today().strftime('%Y-%m-%d'),
        items=[{'product_id': product.id, 'quantity': 5, 'unit_price': 100}],
        user_id=1,
    )

    assert error is None
    assert order is not None
    assert order.total_amount == Decimal('500.00')


def test_sales_service_quick_stock_out(app, db_session):
    """SalesService.quick_stock_out 快速出库"""
    customer = create_customer(code='SVC_CUS02', name='出库客户')
    warehouse = create_warehouse(code='SVC_WH04', name='出库仓库')
    product = create_product(code='SVC_PROD04', name='出库商品', stock_quantity=100)

    order, _ = SalesService.create_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        order_date=date.today().strftime('%Y-%m-%d'),
        items=[{'product_id': product.id, 'quantity': 30, 'unit_price': 80}],
        user_id=1,
    )
    db.session.commit()

    success, error = SalesService.quick_stock_out(order.id, user_id=1)
    db.session.commit()

    assert success is True
    assert error is None

    p = db.session.get(Product, product.id)
    assert p.stock_quantity == Decimal('70')


# ==================== InventoryService ====================

def test_inventory_service_stock_check(app, db_session):
    """InventoryService.stock_check 库存盘点"""
    warehouse = create_warehouse(code='SVC_WH05', name='盘点仓库')
    product = create_product(code='SVC_PROD05', name='盘点商品', stock_quantity=50)

    success, error = InventoryService.stock_check(
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'actual_quantity': 60}],
        notes='测试盘点',
        user_id=1,
    )
    db.session.commit()

    assert success is True
    assert error is None

    p = db.session.get(Product, product.id)
    assert p.stock_quantity == Decimal('60')


def test_inventory_service_stock_adjust_in(app, db_session):
    """InventoryService.stock_adjust 调整入库"""
    warehouse = create_warehouse(code='SVC_WH06', name='调整仓库')
    product = create_product(code='SVC_PROD06', name='调整商品', stock_quantity=30)

    success, error = InventoryService.stock_adjust(
        product_id=product.id,
        warehouse_id=warehouse.id,
        adjust_type='adjust_in',
        quantity=20,
        user_id=1,
    )
    db.session.commit()

    assert success is True
    assert error is None

    p = db.session.get(Product, product.id)
    assert p.stock_quantity == Decimal('50')


def test_inventory_service_stock_adjust_out_insufficient(app, db_session):
    """InventoryService.stock_adjust 库存不足"""
    warehouse = create_warehouse(code='SVC_WH07', name='不足仓库')
    product = create_product(code='SVC_PROD07', name='不足商品', stock_quantity=5)

    success, error = InventoryService.stock_adjust(
        product_id=product.id,
        warehouse_id=warehouse.id,
        adjust_type='adjust_out',
        quantity=10,
        user_id=1,
    )

    assert success is False
    assert '库存不足' in error
