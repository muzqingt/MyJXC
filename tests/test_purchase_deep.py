"""
采购模块深度测试 — 编辑、入库明细、筛选
"""
import pytest
from datetime import date
from decimal import Decimal

from app import db
from app.models import PurchaseOrder, StockIn, StockInItem, Product
from tests.factories import (
    create_supplier, create_warehouse, create_product, create_purchase_order,
)
from tests.helpers import get_page, post_page


# ==================== 订单编辑 ====================

def test_edit_order_get(app, authenticated_client, db_session):
    """GET 编辑订单页面"""
    supplier = create_supplier(code='ED_SUP01', name='编辑供应商')
    warehouse = create_warehouse(code='ED_WH01', name='编辑仓库')
    product = create_product(code='ED_PROD01', name='编辑商品')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 5, 'unit_price': 100}],
    )

    get_page(authenticated_client, f'/purchase/orders/{order.id}/edit')


def test_edit_order_items_get(app, authenticated_client, db_session):
    """GET 编辑订单明细页面"""
    supplier = create_supplier(code='ED_SUP02', name='明细供应商')
    warehouse = create_warehouse(code='ED_WH02', name='明细仓库')
    product = create_product(code='ED_PROD02', name='明细商品')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 3, 'unit_price': 80}],
    )

    get_page(authenticated_client, f'/purchase/orders/{order.id}/items')


# ==================== 入库编辑 ====================

def test_edit_stock_in_items_get(app, authenticated_client, db_session):
    """GET 编辑入库明细页面"""
    warehouse = create_warehouse(code='SI_ED01', name='入库编辑仓库')
    product = create_product(code='SI_ED01', name='入库编辑商品')

    stock_in = StockIn(
        receipt_number='SI_ED_TEST001',
        warehouse_id=warehouse.id,
        receipt_date=date.today(),
        status='pending',
    )
    db.session.add(stock_in)
    db.session.flush()

    item = StockInItem(
        stock_in_id=stock_in.id,
        product_id=product.id,
        quantity=Decimal('10'),
        unit_price=Decimal('50.00'),
        amount=Decimal('500.00'),
    )
    db.session.add(item)
    db.session.commit()

    get_page(authenticated_client, f'/purchase/stock-ins/{stock_in.id}/items')


# ==================== 筛选和分页 ====================

def test_order_filter_by_status(app, authenticated_client, db_session):
    """按状态筛选订单"""
    supplier = create_supplier(code='FLT_SUP01', name='筛选供应商')
    warehouse = create_warehouse(code='FLT_WH01', name='筛选仓库')

    create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[],
        status='confirmed',
    )

    get_page(authenticated_client, '/purchase/?status=confirmed')


def test_order_filter_by_date(app, authenticated_client, db_session):
    """按日期筛选订单"""
    get_page(authenticated_client, '/purchase/?start_date=2026-01-01&end_date=2026-12-31')


def test_stock_in_filter(app, authenticated_client, db_session):
    """筛选入库单"""
    get_page(authenticated_client, '/purchase/?tab=stockins')


def test_returns_filter(app, authenticated_client, db_session):
    """筛选退货单"""
    get_page(authenticated_client, '/purchase/?tab=returns')
