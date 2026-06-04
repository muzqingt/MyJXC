"""
销售模块深度覆盖测试
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


# ==================== 订单编辑 POST ====================

def test_edit_order_post(app, authenticated_client, db_session):
    """POST 编辑销售订单"""
    customer = create_customer(code='SEO_CUS01', name='编辑客户')
    warehouse = create_warehouse(code='SEO_WH01', name='编辑仓库')
    product = create_product(code='SEO_PROD01', name='编辑商品')

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 100}],
    )
    db.session.commit()

    resp = authenticated_client.post(f'/sales/orders/{order.id}/edit', data={
        'customer_id': str(customer.id),
        'warehouse_id': str(warehouse.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '更新备注',
        'action': 'save',
        'product_id[]': [str(product.id)],
        'quantity[]': ['15'],
        'unit_price[]': ['120'],
    }, follow_redirects=True)

    assert resp.status_code == 200


def test_edit_order_completed_redirect(app, authenticated_client, db_session):
    """编辑已完成订单重定向"""
    customer = create_customer(code='SEO_CUS02', name='完成客户')
    warehouse = create_warehouse(code='SEO_WH02', name='完成仓库')

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[],
        status='completed',
    )
    db.session.commit()

    resp = authenticated_client.get(f'/sales/orders/{order.id}/edit', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 出库单编辑 ====================

def test_edit_stock_out_items_post(app, authenticated_client, db_session):
    """POST 编辑出库明细"""
    warehouse = create_warehouse(code='ESO_WH01', name='出库编辑仓库')
    product = create_product(code='ESO_PROD01', name='出库编辑商品')

    stock_out = StockOut(
        delivery_number='ESO_TEST001',
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
        'quantity[]': ['15'],
        'unit_price[]': ['110'],
    }, follow_redirects=True)

    assert resp.status_code == 200


# ==================== 出库单创建 ====================

def test_new_stock_out_post(app, authenticated_client, db_session):
    """POST 创建出库单"""
    warehouse = create_warehouse(code='NSO_WH01', name='新出库仓库')
    product = create_product(code='NSO_PROD01', name='新出库商品', stock_quantity=100)

    resp = authenticated_client.post('/sales/stock-outs/new', data={
        'warehouse_id': str(warehouse.id),
        'delivery_date': date.today().strftime('%Y-%m-%d'),
        'notes': '测试出库单',
        'product_id[]': [str(product.id)],
        'quantity[]': ['10'],
        'unit_price[]': ['100'],
    }, follow_redirects=True)

    assert resp.status_code == 200


# ==================== 订单删除 ====================

def test_delete_order(app, authenticated_client, db_session):
    """删除销售订单"""
    customer = create_customer(code='DSO_CUS01', name='删除客户')
    warehouse = create_warehouse(code='DSO_WH01', name='删除仓库')

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[],
    )
    db.session.commit()

    resp = authenticated_client.post(f'/sales/orders/{order.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 出库单删除 ====================

def test_delete_stock_out(app, authenticated_client, db_session):
    """删除出库单"""
    warehouse = create_warehouse(code='DSO_WH02', name='删除出库仓库')

    stock_out = StockOut(
        delivery_number='DSO_TEST001',
        warehouse_id=warehouse.id,
        delivery_date=date.today(),
        status='pending',
    )
    db.session.add(stock_out)
    db.session.commit()

    resp = authenticated_client.post(f'/sales/stock-outs/{stock_out.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 退货删除 ====================

def test_delete_return(app, authenticated_client, db_session):
    """删除退货单"""
    from app.models import SalesReturn

    warehouse = create_warehouse(code='DSR_WH01', name='退货删除仓库')

    ret = SalesReturn(
        return_number='DSR_TEST001',
        warehouse_id=warehouse.id,
        return_date=date.today(),
        status='pending',
    )
    db.session.add(ret)
    db.session.commit()

    resp = authenticated_client.post(f'/sales/returns/{ret.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 筛选组合测试 ====================

def test_order_filter_combined(app, authenticated_client, db_session):
    """组合筛选"""
    customer = create_customer(code='SFC_CUS01', name='组合筛选客户')
    warehouse = create_warehouse(code='SFC_WH01', name='组合筛选仓库')

    create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[],
        status='confirmed',
    )
    db.session.commit()

    get_page(authenticated_client, f'/sales/?status=confirmed&customer_id={customer.id}')


def test_stock_out_filter_by_warehouse(app, authenticated_client, db_session):
    """按仓库筛选出库单"""
    warehouse = create_warehouse(code='SOF_WH01', name='筛选出库仓库')

    get_page(authenticated_client, f'/sales/?tab=stockouts&warehouse_id={warehouse.id}')
