"""
销售模块深度覆盖 - 编辑和边界测试
"""
import pytest
from datetime import date
from decimal import Decimal
from tests.helpers import get_page, post_page
from tests.factories import create_customer, create_warehouse, create_product, create_sales_order
from app import db
from app.models import SalesOrder, StockOut, StockOutItem


def test_edit_order_post_validation(app, authenticated_client, db_session):
    """编辑订单 - 验证失败"""
    customer = create_customer(code='ES_CUS01', name='验证客户')
    warehouse = create_warehouse(code='ES_WH01', name='验证仓库')
    product = create_product(code='ES_PROD01', name='验证商品')

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 100}],
    )
    db.session.commit()

    # 缺少必填字段
    resp = authenticated_client.post(f'/sales/orders/{order.id}/edit', data={
        'customer_id': '',
        'warehouse_id': str(warehouse.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_edit_order_completed(app, authenticated_client, db_session):
    """编辑已完成订单"""
    customer = create_customer(code='ES_CUS02', name='完成客户')
    warehouse = create_warehouse(code='ES_WH02', name='完成仓库')

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[],
        status='completed',
    )
    db.session.commit()

    resp = authenticated_client.get(f'/sales/orders/{order.id}/edit', follow_redirects=True)
    assert resp.status_code == 200


def test_stock_out_edit_items_post(app, authenticated_client, db_session):
    """编辑出库明细 POST"""
    warehouse = create_warehouse(code='ES_WH03', name='出库编辑仓库')
    product = create_product(code='ES_PROD03', name='出库编辑商品')

    stock_out = StockOut(
        delivery_number='ES_SO001',
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

    resp = authenticated_client.post(f'/sales/stock-outs/{stock_out.id}/items', data={
        'product_id[]': [str(product.id)],
        'quantity[]': ['20'],
        'unit_price[]': ['110'],
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_new_stock_out_post(app, authenticated_client, db_session):
    """创建出库单 POST"""
    warehouse = create_warehouse(code='ES_WH04', name='新出库仓库')
    product = create_product(code='ES_PROD04', name='新出库商品', stock_quantity=100)

    resp = authenticated_client.post('/sales/stock-outs/new', data={
        'warehouse_id': str(warehouse.id),
        'delivery_date': date.today().strftime('%Y-%m-%d'),
        'product_id[]': [str(product.id)],
        'quantity[]': ['15'],
        'unit_price[]': ['95'],
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_order_filter_date_range(app, authenticated_client, db_session):
    """订单日期范围筛选"""
    get_page(authenticated_client, '/sales/?start_date=2026-01-01&end_date=2026-12-31')


def test_stock_out_filter_warehouse(app, authenticated_client, db_session):
    """出库单按仓库筛选"""
    warehouse = create_warehouse(code='ES_WH05', name='筛选仓库')
    get_page(authenticated_client, f'/sales/?tab=stockouts&warehouse_id={warehouse.id}')


def test_returns_filter(authenticated_client):
    """退货单筛选"""
    get_page(authenticated_client, '/sales/?tab=returns')
