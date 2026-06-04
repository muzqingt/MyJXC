"""
销售模块深度测试 — 编辑、出库明细、筛选
"""
import pytest
from datetime import date
from decimal import Decimal

from app import db
from app.models import SalesOrder, StockOut, StockOutItem, Product
from tests.factories import (
    create_customer, create_warehouse, create_product, create_sales_order,
)
from tests.helpers import get_page, post_page


# ==================== 订单编辑 ====================

def test_edit_order_get(app, authenticated_client, db_session):
    """GET 编辑销售订单页面"""
    customer = create_customer(code='SED_CUS01', name='编辑客户')
    warehouse = create_warehouse(code='SED_WH01', name='编辑仓库')
    product = create_product(code='SED_PROD01', name='编辑商品')

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 5, 'unit_price': 200}],
    )

    get_page(authenticated_client, f'/sales/orders/{order.id}/edit')


def test_edit_order_items_get(app, authenticated_client, db_session):
    """GET 编辑销售订单明细页面"""
    customer = create_customer(code='SED_CUS02', name='明细客户')
    warehouse = create_warehouse(code='SED_WH02', name='明细仓库')
    product = create_product(code='SED_PROD02', name='明细商品')

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 3, 'unit_price': 150}],
    )

    get_page(authenticated_client, f'/sales/orders/{order.id}/items')


# ==================== 出库编辑 ====================

def test_edit_stock_out_items_get(app, authenticated_client, db_session):
    """GET 编辑出库明细页面"""
    warehouse = create_warehouse(code='SO_ED01', name='出库编辑仓库')
    product = create_product(code='SO_ED01', name='出库编辑商品')

    stock_out = StockOut(
        delivery_number='SO_ED_TEST001',
        warehouse_id=warehouse.id,
        delivery_date=date.today(),
        status='pending',
    )
    db.session.add(stock_out)
    db.session.flush()

    item = StockOutItem(
        stock_out_id=stock_out.id,
        product_id=product.id,
        quantity=Decimal('10'),
        unit_price=Decimal('100.00'),
        amount=Decimal('1000.00'),
    )
    db.session.add(item)
    db.session.commit()

    get_page(authenticated_client, f'/sales/stock-outs/{stock_out.id}/items')


# ==================== 筛选和分页 ====================

def test_order_filter_by_status(app, authenticated_client, db_session):
    """按状态筛选销售订单"""
    customer = create_customer(code='SFLT_CUS01', name='筛选客户')
    warehouse = create_warehouse(code='SFLT_WH01', name='筛选仓库')

    create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[],
        status='confirmed',
    )

    get_page(authenticated_client, '/sales/?status=confirmed')


def test_order_filter_by_date(app, authenticated_client, db_session):
    """按日期筛选销售订单"""
    get_page(authenticated_client, '/sales/?start_date=2026-01-01&end_date=2026-12-31')


def test_stock_out_filter(app, authenticated_client, db_session):
    """筛选出库单"""
    get_page(authenticated_client, '/sales/?tab=stockouts')


def test_returns_filter(app, authenticated_client, db_session):
    """筛选退货单"""
    get_page(authenticated_client, '/sales/?tab=returns')
