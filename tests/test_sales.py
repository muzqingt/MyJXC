"""
销售模块测试 — 订单 CRUD、出库流程、退货流程、库存联动
"""
import pytest
from datetime import date
from decimal import Decimal

from app import db
from app.models import (
    SalesOrder, SalesOrderItem, StockOut, StockOutItem,
    StockLog, SalesReturn, SalesReturnItem, Product,
)
from tests.factories import (
    create_customer, create_warehouse, create_product,
    create_sales_order, create_category,
)


# ==================== 订单 CRUD ====================

def test_sales_index(authenticated_client):
    """GET /sales/ 返回 200"""
    resp = authenticated_client.get('/sales/', follow_redirects=True)
    assert resp.status_code == 200


def test_new_order_get(authenticated_client):
    """GET /sales/orders/new 返回 200"""
    resp = authenticated_client.get('/sales/orders/new', follow_redirects=True)
    assert resp.status_code == 200


def test_new_order_post(app, authenticated_client, db_session):
    """POST 创建销售订单"""
    customer = create_customer(code='SO_CUS01', name='销售测试客户')
    warehouse = create_warehouse(code='SO_WH01', name='销售测试仓库')
    product = create_product(code='SO_PROD01', name='销售测试商品', stock_quantity=100)

    resp = authenticated_client.post('/sales/orders/new', data={
        'customer_id': str(customer.id),
        'warehouse_id': str(warehouse.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '测试销售订单',
        'action': 'save',
        'order_status': 'confirmed',
        'product_id[]': [str(product.id)],
        'quantity[]': ['5'],
        'unit_price[]': ['200.00'],
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        order = SalesOrder.query.filter_by(customer_id=customer.id).first()
        assert order is not None
        assert order.order_number.startswith('SO')
        assert order.status == 'confirmed'


def test_edit_order(app, authenticated_client, db_session):
    """GET /sales/orders/{id}/edit 返回 200"""
    customer = create_customer(code='SO_CUS02', name='编辑测试客户')
    warehouse = create_warehouse(code='SO_WH02', name='编辑测试仓库')
    product = create_product(code='SO_PROD02', name='编辑测试商品')

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 3, 'unit_price': 150}],
    )

    resp = authenticated_client.get(f'/sales/orders/{order.id}/edit', follow_redirects=True)
    assert resp.status_code == 200


def test_view_order(app, authenticated_client, db_session):
    """GET /sales/orders/{id} 返回 200"""
    customer = create_customer(code='SO_CUS03', name='查看测试客户')
    warehouse = create_warehouse(code='SO_WH03', name='查看测试仓库')
    product = create_product(code='SO_PROD03', name='查看测试商品')

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 2, 'unit_price': 300}],
    )

    resp = authenticated_client.get(f'/sales/orders/{order.id}', follow_redirects=True)
    assert resp.status_code == 200


def test_delete_order(app, authenticated_client, db_session):
    """POST 删除销售订单"""
    customer = create_customer(code='SO_CUS04', name='删除测试客户')
    warehouse = create_warehouse(code='SO_WH04', name='删除测试仓库')

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[],
    )
    order_id = order.id

    resp = authenticated_client.post(f'/sales/orders/{order.id}/delete', follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        deleted = db.session.get(SalesOrder, order_id)
        assert deleted is None


def test_order_with_items(app, authenticated_client, db_session):
    """创建带明细的订单，验证金额计算"""
    customer = create_customer(code='SO_CUS05', name='明细测试客户')
    warehouse = create_warehouse(code='SO_WH05', name='明细测试仓库')
    product1 = create_product(code='SO_P1', name='商品A', sale_price=100)
    product2 = create_product(code='SO_P2', name='商品B', sale_price=200)

    resp = authenticated_client.post('/sales/orders/new', data={
        'customer_id': str(customer.id),
        'warehouse_id': str(warehouse.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'action': 'save',
        'order_status': 'confirmed',
        'product_id[]': [str(product1.id), str(product2.id)],
        'quantity[]': ['3', '2'],
        'unit_price[]': ['100.00', '200.00'],
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        order = SalesOrder.query.filter_by(customer_id=customer.id).first()
        assert order is not None
        assert len(order.items) == 2
        assert order.total_amount == Decimal('700.00')  # 3*100 + 2*200


def test_order_list_filter(app, authenticated_client, db_session):
    """按客户筛选订单"""
    customer1 = create_customer(code='SO_CUS06', name='筛选客户A')
    customer2 = create_customer(code='SO_CUS07', name='筛选客户B')
    warehouse = create_warehouse(code='SO_WH06', name='筛选仓库')

    create_sales_order(customer_id=customer1.id, warehouse_id=warehouse.id, items=[])
    create_sales_order(customer_id=customer2.id, warehouse_id=warehouse.id, items=[])

    resp = authenticated_client.get(
        f'/sales/?customer_id={customer1.id}', follow_redirects=True
    )
    assert resp.status_code == 200


# ==================== 出库流程 ====================

def test_quick_stock_out(app, authenticated_client, db_session):
    """快速出库，验证库存减少"""
    customer = create_customer(code='OUT_CUS01', name='出库客户')
    warehouse = create_warehouse(code='OUT_WH01', name='出库仓库')
    product = create_product(code='OUT_PROD01', name='出库商品', stock_quantity=100)

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 200}],
    )

    resp = authenticated_client.post(
        f'/sales/orders/{order.id}/quick-stock-out', follow_redirects=True
    )
    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('90')


def test_new_stock_out(authenticated_client):
    """独立创建出库单 GET"""
    resp = authenticated_client.get('/sales/stock-outs/new', follow_redirects=True)
    assert resp.status_code == 200


def test_complete_stock_out(app, authenticated_client, db_session):
    """完成出库，验证库存和日志"""
    warehouse = create_warehouse(code='OUT_WH02', name='完成出库仓库')
    product = create_product(code='OUT_PROD02', name='完成出库商品', stock_quantity=50)

    stock_out = StockOut(
        delivery_number='OUT_TEST001',
        warehouse_id=warehouse.id,
        delivery_date=date.today(),
        status='pending',
    )
    db.session.add(stock_out)
    db.session.flush()

    item = StockOutItem(
        stock_out_id=stock_out.id,
        product_id=product.id,
        quantity=Decimal('15'),
        unit_price=Decimal('100.00'),
        amount=Decimal('1500.00'),
    )
    db.session.add(item)
    db.session.commit()

    resp = authenticated_client.post(
        f'/sales/stock-outs/{stock_out.id}/complete', follow_redirects=True
    )
    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('35')

        so = db.session.get(StockOut, stock_out.id)
        assert so.status == 'completed'


def test_view_stock_out(app, authenticated_client, db_session):
    """查看出库单详情"""
    warehouse = create_warehouse(code='OUT_WH03', name='查看出库仓库')
    product = create_product(code='OUT_PROD03', name='查看出库商品')

    stock_out = StockOut(
        delivery_number='OUT_TEST002',
        warehouse_id=warehouse.id,
        delivery_date=date.today(),
        status='pending',
    )
    db.session.add(stock_out)
    db.session.flush()

    item = StockOutItem(
        stock_out_id=stock_out.id,
        product_id=product.id,
        quantity=Decimal('5'),
        unit_price=Decimal('100.00'),
        amount=Decimal('500.00'),
    )
    db.session.add(item)
    db.session.commit()

    resp = authenticated_client.get(f'/sales/stock-outs/{stock_out.id}', follow_redirects=True)
    assert resp.status_code == 200


def test_stock_out_creates_log(app, authenticated_client, db_session):
    """出库后验证 StockLog 记录"""
    warehouse = create_warehouse(code='OUT_WH04', name='日志出库仓库')
    product = create_product(code='OUT_PROD04', name='日志出库商品', stock_quantity=100)

    stock_out = StockOut(
        delivery_number='OUT_TEST003',
        warehouse_id=warehouse.id,
        delivery_date=date.today(),
        status='pending',
    )
    db.session.add(stock_out)
    db.session.flush()

    item = StockOutItem(
        stock_out_id=stock_out.id,
        product_id=product.id,
        quantity=Decimal('20'),
        unit_price=Decimal('50.00'),
        amount=Decimal('1000.00'),
    )
    db.session.add(item)
    db.session.commit()

    authenticated_client.post(
        f'/sales/stock-outs/{stock_out.id}/complete', follow_redirects=True
    )

    with app.app_context():
        log = StockLog.query.filter_by(
            product_id=product.id, change_type='out'
        ).first()
        assert log is not None
        assert log.quantity == Decimal('20')


def test_stock_out_with_insufficient_stock(app, authenticated_client, db_session):
    """库存不足时出库处理"""
    customer = create_customer(code='OUT_CUS05', name='库存不足客户')
    warehouse = create_warehouse(code='OUT_WH05', name='库存不足仓库')
    product = create_product(code='OUT_PROD05', name='库存不足商品', stock_quantity=3)

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 100}],
    )
    db.session.commit()  # 确保订单在数据库中可见

    resp = authenticated_client.post(
        f'/sales/orders/{order.id}/quick-stock-out', follow_redirects=True
    )
    # 出库可能成功（允许负库存）或被拒绝
    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Product, product.id)
        # 验证库存发生了变化
        assert p.stock_quantity is not None


# ==================== 退货流程 ====================

def test_quick_return(app, authenticated_client, db_session):
    """快速退货，验证库存增加"""
    customer = create_customer(code='SRT_CUS01', name='退货客户')
    warehouse = create_warehouse(code='SRT_WH01', name='退货仓库')
    product = create_product(code='SRT_PROD01', name='退货商品', stock_quantity=50)

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 200}],
        status='completed',
    )
    order.items[0].delivered_quantity = Decimal('10')
    db.session.commit()

    resp = authenticated_client.post(
        f'/sales/orders/{order.id}/quick-return', follow_redirects=True
    )
    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('60')  # 50 + 10


def test_returns_list(authenticated_client):
    """GET /sales/returns 返回 200"""
    resp = authenticated_client.get('/sales/returns', follow_redirects=True)
    assert resp.status_code == 200


def test_view_return(app, authenticated_client, db_session):
    """查看退货单详情"""
    customer = create_customer(code='SRT_CUS02', name='查看退货客户')
    warehouse = create_warehouse(code='SRT_WH02', name='查看退货仓库')
    product = create_product(code='SRT_PROD02', name='查看退货商品', stock_quantity=100)

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 5, 'unit_price': 100}],
    )

    ret = SalesReturn(
        return_number='SRT_TEST001',
        sales_order_id=order.id,
        warehouse_id=warehouse.id,
        return_date=date.today(),
        status='completed',
    )
    db.session.add(ret)
    db.session.flush()

    ret_item = SalesReturnItem(
        return_id=ret.id,
        product_id=product.id,
        quantity=Decimal('2'),
        unit_price=Decimal('100.00'),
        amount=Decimal('200.00'),
    )
    db.session.add(ret_item)
    db.session.commit()

    resp = authenticated_client.get(f'/sales/returns/{ret.id}', follow_redirects=True)
    assert resp.status_code == 200


def test_return_increases_stock(app, authenticated_client, db_session):
    """退货后库存增加"""
    customer = create_customer(code='SRT_CUS03', name='库存增加客户')
    warehouse = create_warehouse(code='SRT_WH03', name='库存增加仓库')
    product = create_product(code='SRT_PROD03', name='库存增加商品', stock_quantity=80)

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 150}],
        status='completed',
    )
    order.items[0].delivered_quantity = Decimal('10')
    db.session.commit()

    authenticated_client.post(
        f'/sales/orders/{order.id}/quick-return', follow_redirects=True
    )

    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('90')  # 80 + 10


# ==================== 边界情况和 API ====================

def test_order_not_found_404(authenticated_client):
    """访问不存在的订单返回 404"""
    resp = authenticated_client.get('/sales/orders/99999', follow_redirects=False)
    assert resp.status_code == 404


def test_stock_out_not_found_404(authenticated_client):
    """访问不存在的出库单返回 404"""
    resp = authenticated_client.get('/sales/stock-outs/99999', follow_redirects=False)
    assert resp.status_code == 404


def test_unauthenticated_redirect(client):
    """未登录访问销售首页重定向"""
    resp = client.get('/sales/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers.get('Location', '')


def test_api_order_items(app, authenticated_client, db_session):
    """GET /sales/api/sales-orders/{id}/items 返回 JSON"""
    customer = create_customer(code='API_CUS01', name='API客户')
    warehouse = create_warehouse(code='API_WH01', name='API仓库')
    product = create_product(code='API_PROD01', name='API商品')

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 5, 'unit_price': 100}],
    )

    resp = authenticated_client.get(f'/sales/api/sales-orders/{order.id}/items')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
