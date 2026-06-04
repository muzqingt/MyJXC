"""
采购模块深度覆盖测试
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


# ==================== 订单编辑 POST ====================

def test_edit_order_post(app, authenticated_client, db_session):
    """POST 编辑采购订单"""
    supplier = create_supplier(code='EO_SUP01', name='编辑供应商')
    warehouse = create_warehouse(code='EO_WH01', name='编辑仓库')
    product = create_product(code='EO_PROD01', name='编辑商品')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 50}],
    )
    db.session.commit()

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/edit', data={
        'supplier_id': str(supplier.id),
        'warehouse_id': str(warehouse.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '更新备注',
        'action': 'save',
        'product_id[]': [str(product.id)],
        'quantity[]': ['20'],
        'unit_price[]': ['60'],
    }, follow_redirects=True)

    assert resp.status_code == 200


def test_edit_order_completed_redirect(app, authenticated_client, db_session):
    """编辑已完成订单重定向"""
    supplier = create_supplier(code='EO_SUP02', name='完成供应商')
    warehouse = create_warehouse(code='EO_WH02', name='完成仓库')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[],
        status='completed',
    )
    db.session.commit()

    resp = authenticated_client.get(f'/purchase/orders/{order.id}/edit', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 入库单编辑 ====================

def test_edit_stock_in_items_post(app, authenticated_client, db_session):
    """POST 编辑入库明细"""
    warehouse = create_warehouse(code='ESI_WH01', name='入库编辑仓库')
    product = create_product(code='ESI_PROD01', name='入库编辑商品')

    stock_in = StockIn(
        receipt_number='ESI_TEST001',
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
        'quantity[]': ['15'],
        'unit_price[]': ['55'],
    }, follow_redirects=True)

    assert resp.status_code == 200


# ==================== 入库单创建 ====================

def test_new_stock_in_post(app, authenticated_client, db_session):
    """POST 创建入库单"""
    warehouse = create_warehouse(code='NSI_WH01', name='新入库仓库')
    product = create_product(code='NSI_PROD01', name='新入库商品')

    resp = authenticated_client.post('/purchase/stock-ins/new', data={
        'warehouse_id': str(warehouse.id),
        'receipt_date': date.today().strftime('%Y-%m-%d'),
        'notes': '测试入库单',
        'product_id[]': [str(product.id)],
        'quantity[]': ['10'],
        'unit_price[]': ['50'],
    }, follow_redirects=True)

    assert resp.status_code == 200


# ==================== 退货删除 ====================

def test_delete_return(app, authenticated_client, db_session):
    """删除退货单"""
    from app.models import PurchaseReturn

    supplier = create_supplier(name='退货删除供应商')
    warehouse = create_warehouse(name='退货删除仓库')

    ret = PurchaseReturn(
        return_number='DR_TEST001',
        warehouse_id=warehouse.id,
        return_date=date.today(),
        status='pending',
    )
    db.session.add(ret)
    db.session.commit()
    ret_id = ret.id

    resp = authenticated_client.post(f'/purchase/returns/{ret.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 订单删除 ====================

def test_delete_order(app, authenticated_client, db_session):
    """删除采购订单"""
    supplier = create_supplier(code='DO_SUP01', name='删除供应商')
    warehouse = create_warehouse(code='DO_WH01', name='删除仓库')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[],
    )
    db.session.commit()
    order_id = order.id

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 入库单删除 ====================

def test_delete_stock_in(app, authenticated_client, db_session):
    """删除入库单"""
    warehouse = create_warehouse(code='DSI_WH01', name='删除入库仓库')

    stock_in = StockIn(
        receipt_number='DSI_TEST001',
        warehouse_id=warehouse.id,
        receipt_date=date.today(),
        status='pending',
    )
    db.session.add(stock_in)
    db.session.commit()
    stock_in_id = stock_in.id

    resp = authenticated_client.post(f'/purchase/stock-ins/{stock_in.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 筛选组合测试 ====================

def test_order_filter_combined(app, authenticated_client, db_session):
    """组合筛选"""
    supplier = create_supplier(name='组合筛选供应商')
    warehouse = create_warehouse(name='组合筛选仓库')

    create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[],
        status='confirmed',
    )
    db.session.commit()

    get_page(authenticated_client, f'/purchase/?status=confirmed&supplier_id={supplier.id}')


def test_stock_in_filter_by_warehouse(app, authenticated_client, db_session):
    """按仓库筛选入库单"""
    warehouse = create_warehouse(code='SIF_WH01', name='筛选入库仓库')

    get_page(authenticated_client, f'/purchase/?tab=stockins&warehouse_id={warehouse.id}')
