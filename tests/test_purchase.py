"""
采购模块测试 — 订单 CRUD、入库流程、退货流程、边界情况
"""
import pytest
from datetime import date
from decimal import Decimal

from app import db
from app.models import (
    PurchaseOrder, PurchaseOrderItem, StockIn, StockInItem,
    StockLog, PurchaseReturn, PurchaseReturnItem, Product,
)
from tests.factories import (
    create_supplier, create_warehouse, create_product,
    create_purchase_order, create_category,
)


# ==================== 采购订单 CRUD ====================

def test_purchase_index(authenticated_client):
    """GET /purchase/ 返回 200"""
    resp = authenticated_client.get('/purchase/', follow_redirects=True)
    assert resp.status_code == 200


def test_new_order_get(authenticated_client):
    """GET /purchase/orders/new 返回 200"""
    resp = authenticated_client.get('/purchase/orders/new', follow_redirects=True)
    assert resp.status_code == 200


def test_new_order_post(app, authenticated_client, db_session):
    """POST 创建采购订单，验证订单号生成"""
    supplier = create_supplier(code='PO_SUP01', name='采购测试供应商')
    warehouse = create_warehouse(code='PO_WH01', name='采购测试仓库')
    product = create_product(code='PO_PROD01', name='采购测试商品')

    resp = authenticated_client.post('/purchase/orders/new', data={
        'supplier_id': str(supplier.id),
        'warehouse_id': str(warehouse.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '测试订单',
        'action': 'save',
        'order_status': 'confirmed',
        'product_id[]': [str(product.id)],
        'quantity[]': ['10'],
        'unit_price[]': ['50.00'],
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        order = PurchaseOrder.query.filter_by(supplier_id=supplier.id).first()
        assert order is not None
        assert order.order_number.startswith('PO')
        assert order.status == 'confirmed'


def test_edit_order(app, authenticated_client, db_session):
    """GET /purchase/orders/{id}/edit 返回 200"""
    supplier = create_supplier(code='PO_SUP02', name='编辑测试供应商')
    warehouse = create_warehouse(code='PO_WH02', name='编辑测试仓库')
    product = create_product(code='PO_PROD02', name='编辑测试商品')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 5, 'unit_price': 100}],
    )

    resp = authenticated_client.get(f'/purchase/orders/{order.id}/edit', follow_redirects=True)
    assert resp.status_code == 200


def test_view_order(app, authenticated_client, db_session):
    """GET /purchase/orders/{id} 返回 200"""
    supplier = create_supplier(code='PO_SUP03', name='查看测试供应商')
    warehouse = create_warehouse(code='PO_WH03', name='查看测试仓库')
    product = create_product(code='PO_PROD03', name='查看测试商品')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 3, 'unit_price': 80}],
    )

    resp = authenticated_client.get(f'/purchase/orders/{order.id}', follow_redirects=True)
    assert resp.status_code == 200


def test_delete_order(app, authenticated_client, db_session):
    """POST 删除采购订单，验证已删除"""
    supplier = create_supplier(code='PO_SUP04', name='删除测试供应商')
    warehouse = create_warehouse(code='PO_WH04', name='删除测试仓库')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[],
    )
    order_id = order.id

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/delete', follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        deleted = db.session.get(PurchaseOrder, order_id)
        assert deleted is None


def test_order_with_items(app, authenticated_client, db_session):
    """创建带明细的订单，验证金额计算"""
    supplier = create_supplier(code='PO_SUP05', name='明细测试供应商')
    warehouse = create_warehouse(code='PO_WH05', name='明细测试仓库')
    product1 = create_product(code='PO_P1', name='商品1', cost_price=10)
    product2 = create_product(code='PO_P2', name='商品2', cost_price=20)

    resp = authenticated_client.post('/purchase/orders/new', data={
        'supplier_id': str(supplier.id),
        'warehouse_id': str(warehouse.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'action': 'save',
        'order_status': 'confirmed',
        'product_id[]': [str(product1.id), str(product2.id)],
        'quantity[]': ['10', '5'],
        'unit_price[]': ['10.00', '20.00'],
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        order = PurchaseOrder.query.filter_by(supplier_id=supplier.id).first()
        assert order is not None
        assert len(order.items) == 2
        assert order.total_amount == Decimal('200.00')  # 10*10 + 5*20


def test_order_list_filter(app, authenticated_client, db_session):
    """按供应商筛选订单"""
    supplier1 = create_supplier(code='PO_SUP06', name='筛选供应商A')
    supplier2 = create_supplier(code='PO_SUP07', name='筛选供应商B')
    warehouse = create_warehouse(code='PO_WH06', name='筛选仓库')

    create_purchase_order(supplier_id=supplier1.id, warehouse_id=warehouse.id, items=[])
    create_purchase_order(supplier_id=supplier2.id, warehouse_id=warehouse.id, items=[])

    resp = authenticated_client.get(
        f'/purchase/?supplier_id={supplier1.id}', follow_redirects=True
    )
    assert resp.status_code == 200


# ==================== 入库流程 ====================

def test_quick_stock_in(app, authenticated_client, db_session):
    """快速入库，验证库存增加"""
    supplier = create_supplier(code='SI_SUP01', name='入库供应商')
    warehouse = create_warehouse(code='SI_WH01', name='入库仓库')
    product = create_product(code='SI_PROD01', name='入库商品', stock_quantity=0)

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 50}],
    )

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/quick-stock-in', follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('10')


def test_new_stock_in_from_order(app, authenticated_client, db_session):
    """从订单创建入库单"""
    supplier = create_supplier(code='SI_SUP02', name='从订单入库供应商')
    warehouse = create_warehouse(code='SI_WH02', name='从订单入库仓库')
    product = create_product(code='SI_PROD02', name='从订单入库商品')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 5, 'unit_price': 30}],
    )

    resp = authenticated_client.get(
        f'/purchase/orders/{order.id}/stock-in', follow_redirects=True
    )
    assert resp.status_code == 200


def test_new_stock_in(authenticated_client):
    """独立创建入库单 GET"""
    resp = authenticated_client.get('/purchase/stock-ins/new', follow_redirects=True)
    assert resp.status_code == 200


def test_complete_stock_in(app, authenticated_client, db_session):
    """完成入库，验证库存和日志"""
    warehouse = create_warehouse(code='SI_WH03', name='完成入库仓库')
    product = create_product(code='SI_PROD03', name='完成入库商品', stock_quantity=0)

    # 创建入库单
    stock_in = StockIn(
        receipt_number='SI_TEST001',
        warehouse_id=warehouse.id,
        receipt_date=date.today(),
        status='pending',
    )
    db.session.add(stock_in)
    db.session.flush()

    item = StockInItem(
        stock_in_id=stock_in.id,
        product_id=product.id,
        quantity=Decimal('20'),
        unit_price=Decimal('25.00'),
        amount=Decimal('500.00'),
    )
    db.session.add(item)
    db.session.commit()

    resp = authenticated_client.post(
        f'/purchase/stock-ins/{stock_in.id}/complete', follow_redirects=True
    )
    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('20')

        si = db.session.get(StockIn, stock_in.id)
        assert si.status == 'completed'


def test_view_stock_in(app, authenticated_client, db_session):
    """查看入库单详情"""
    warehouse = create_warehouse(code='SI_WH04', name='查看入库仓库')
    product = create_product(code='SI_PROD04', name='查看入库商品')

    stock_in = StockIn(
        receipt_number='SI_TEST002',
        warehouse_id=warehouse.id,
        receipt_date=date.today(),
        status='pending',
    )
    db.session.add(stock_in)
    db.session.flush()

    item = StockInItem(
        stock_in_id=stock_in.id,
        product_id=product.id,
        quantity=Decimal('5'),
        unit_price=Decimal('100.00'),
        amount=Decimal('500.00'),
    )
    db.session.add(item)
    db.session.commit()

    resp = authenticated_client.get(f'/purchase/stock-ins/{stock_in.id}', follow_redirects=True)
    assert resp.status_code == 200


def test_stock_in_creates_log(app, authenticated_client, db_session):
    """入库后验证 StockLog 记录"""
    warehouse = create_warehouse(code='SI_WH05', name='日志仓库')
    product = create_product(code='SI_PROD05', name='日志商品', stock_quantity=0)

    stock_in = StockIn(
        receipt_number='SI_TEST003',
        warehouse_id=warehouse.id,
        receipt_date=date.today(),
        status='pending',
    )
    db.session.add(stock_in)
    db.session.flush()

    item = StockInItem(
        stock_in_id=stock_in.id,
        product_id=product.id,
        quantity=Decimal('15'),
        unit_price=Decimal('20.00'),
        amount=Decimal('300.00'),
    )
    db.session.add(item)
    db.session.commit()

    authenticated_client.post(
        f'/purchase/stock-ins/{stock_in.id}/complete', follow_redirects=True
    )

    with app.app_context():
        log = StockLog.query.filter_by(
            product_id=product.id, change_type='in'
        ).first()
        assert log is not None
        assert log.quantity == Decimal('15')


# ==================== 退货流程 ====================

def test_quick_return(app, authenticated_client, db_session):
    """快速退货，验证库存减少"""
    supplier = create_supplier(code='RT_SUP01', name='退货供应商')
    warehouse = create_warehouse(code='RT_WH01', name='退货仓库')
    product = create_product(code='RT_PROD01', name='退货商品', stock_quantity=50)

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 50}],
        status='completed',
    )
    # 设置已入库数量
    order.items[0].received_quantity = Decimal('10')
    db.session.commit()

    resp = authenticated_client.post(
        f'/purchase/orders/{order.id}/quick-return', follow_redirects=True
    )
    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('40')  # 50 - 10


def test_returns_list(authenticated_client):
    """GET /purchase/returns 返回 200"""
    resp = authenticated_client.get('/purchase/returns', follow_redirects=True)
    assert resp.status_code == 200


def test_view_return(app, authenticated_client, db_session):
    """查看退货单详情"""
    supplier = create_supplier(code='RT_SUP02', name='查看退货供应商')
    warehouse = create_warehouse(code='RT_WH02', name='查看退货仓库')
    product = create_product(code='RT_PROD02', name='查看退货商品', stock_quantity=100)

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 50}],
    )

    # 创建退货单
    ret = PurchaseReturn(
        return_number='RT_TEST001',
        purchase_order_id=order.id,
        warehouse_id=warehouse.id,
        return_date=date.today(),
        status='completed',
    )
    db.session.add(ret)
    db.session.flush()

    ret_item = PurchaseReturnItem(
        return_id=ret.id,
        product_id=product.id,
        quantity=Decimal('2'),
        unit_price=Decimal('50.00'),
        amount=Decimal('100.00'),
    )
    db.session.add(ret_item)
    db.session.commit()

    resp = authenticated_client.get(f'/purchase/returns/{ret.id}', follow_redirects=True)
    assert resp.status_code == 200


def test_return_decreases_stock(app, authenticated_client, db_session):
    """退货后库存正确减少"""
    supplier = create_supplier(code='RT_SUP03', name='库存减少供应商')
    warehouse = create_warehouse(code='RT_WH03', name='库存减少仓库')
    product = create_product(code='RT_PROD03', name='库存减少商品', stock_quantity=100)

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 50}],
        status='completed',
    )
    order.items[0].received_quantity = Decimal('10')
    db.session.commit()

    authenticated_client.post(
        f'/purchase/orders/{order.id}/quick-return', follow_redirects=True
    )

    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('90')  # 100 - 10


def test_return_creates_log(app, authenticated_client, db_session):
    """退货后验证 StockLog 记录"""
    supplier = create_supplier(code='RT_SUP04', name='日志退货供应商')
    warehouse = create_warehouse(code='RT_WH04', name='日志退货仓库')
    product = create_product(code='RT_PROD04', name='日志退货商品', stock_quantity=80)

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 50}],
        status='completed',
    )
    order.items[0].received_quantity = Decimal('10')
    db.session.commit()

    authenticated_client.post(
        f'/purchase/orders/{order.id}/quick-return', follow_redirects=True
    )

    with app.app_context():
        log = StockLog.query.filter_by(
            product_id=product.id, change_type='return_out'
        ).first()
        assert log is not None
        assert log.quantity == Decimal('10')


# ==================== 边界情况和 API ====================

def test_order_not_found_404(authenticated_client):
    """访问不存在的订单返回 404"""
    resp = authenticated_client.get('/purchase/orders/99999', follow_redirects=False)
    assert resp.status_code == 404


def test_stock_in_not_found_404(authenticated_client):
    """访问不存在的入库单返回 404"""
    resp = authenticated_client.get('/purchase/stock-ins/99999', follow_redirects=False)
    assert resp.status_code == 404


def test_unauthenticated_redirect(client):
    """未登录访问采购首页重定向"""
    resp = client.get('/purchase/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers.get('Location', '')


def test_api_order_items(app, authenticated_client, db_session):
    """GET /purchase/api/purchase-orders/{id}/items 返回 JSON"""
    supplier = create_supplier(code='API_SUP01', name='API供应商')
    warehouse = create_warehouse(code='API_WH01', name='API仓库')
    product = create_product(code='API_PROD01', name='API商品')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 5, 'unit_price': 100}],
    )

    resp = authenticated_client.get(f'/purchase/api/purchase-orders/{order.id}/items')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 1


def test_order_delete_with_stock_in(app, authenticated_client, db_session):
    """有入库单的订单不能直接删除"""
    supplier = create_supplier(code='DEL_SUP01', name='删除关联供应商')
    warehouse = create_warehouse(code='DEL_WH01', name='删除关联仓库')
    product = create_product(code='DEL_PROD01', name='删除关联商品')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 5, 'unit_price': 100}],
    )

    # 创建入库单关联此订单
    stock_in = StockIn(
        receipt_number='DEL_SI001',
        purchase_order_id=order.id,
        warehouse_id=warehouse.id,
        receipt_date=date.today(),
        status='completed',
    )
    db.session.add(stock_in)
    db.session.commit()

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/delete', follow_redirects=True)
    # 应该失败（有关联入库单）
    with app.app_context():
        still_exists = db.session.get(PurchaseOrder, order.id)
        assert still_exists is not None
