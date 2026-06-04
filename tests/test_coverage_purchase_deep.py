"""
采购模块深度覆盖 - 编辑和边界测试
"""
import pytest
from datetime import date
from decimal import Decimal
from tests.helpers import get_page, post_page
from tests.factories import create_supplier, create_warehouse, create_product, create_purchase_order
from app import db
from app.models import PurchaseOrder, StockIn, StockInItem


def test_edit_order_post_validation(app, authenticated_client, db_session):
    """编辑订单 - 验证失败"""
    supplier = create_supplier(code='EP_SUP01', name='验证供应商')
    warehouse = create_warehouse(code='EP_WH01', name='验证仓库')
    product = create_product(code='EP_PROD01', name='验证商品')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 50}],
    )
    db.session.commit()

    # 缺少必填字段
    resp = authenticated_client.post(f'/purchase/orders/{order.id}/edit', data={
        'supplier_id': '',
        'warehouse_id': str(warehouse.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_edit_order_completed(app, authenticated_client, db_session):
    """编辑已完成订单"""
    supplier = create_supplier(code='EP_SUP02', name='完成供应商')
    warehouse = create_warehouse(code='EP_WH02', name='完成仓库')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[],
        status='completed',
    )
    db.session.commit()

    resp = authenticated_client.get(f'/purchase/orders/{order.id}/edit', follow_redirects=True)
    assert resp.status_code == 200


def test_stock_in_edit_items_post(app, authenticated_client, db_session):
    """编辑入库明细 POST"""
    warehouse = create_warehouse(code='EP_WH03', name='入库编辑仓库')
    product = create_product(code='EP_PROD03', name='入库编辑商品')

    stock_in = StockIn(
        receipt_number='EP_SI001',
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

    resp = authenticated_client.post(f'/purchase/stock-ins/{stock_in.id}/items', data={
        'product_id[]': [str(product.id)],
        'quantity[]': ['20'],
        'unit_price[]': ['60'],
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_new_stock_in_post(app, authenticated_client, db_session):
    """创建入库单 POST"""
    warehouse = create_warehouse(code='EP_WH04', name='新入库仓库')
    product = create_product(code='EP_PROD04', name='新入库商品')

    resp = authenticated_client.post('/purchase/stock-ins/new', data={
        'warehouse_id': str(warehouse.id),
        'receipt_date': date.today().strftime('%Y-%m-%d'),
        'product_id[]': [str(product.id)],
        'quantity[]': ['15'],
        'unit_price[]': ['45'],
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_order_filter_date_range(app, authenticated_client, db_session):
    """订单日期范围筛选"""
    get_page(authenticated_client, '/purchase/?start_date=2026-01-01&end_date=2026-12-31')


def test_stock_in_filter_warehouse(app, authenticated_client, db_session):
    """入库单按仓库筛选"""
    warehouse = create_warehouse(code='EP_WH05', name='筛选仓库')
    get_page(authenticated_client, f'/purchase/?tab=stockins&warehouse_id={warehouse.id}')


def test_returns_filter(app, authenticated_client):
    """退货单筛选"""
    get_page(authenticated_client, '/purchase/?tab=returns')
