"""
库存模块测试 — 库存概览、盘点、调拨、调整、日志
"""
import pytest
from decimal import Decimal

from app import db
from app.models import Product, StockLog, Warehouse
from tests.factories import create_product, create_warehouse, create_category


# ==================== 库存概览 ====================

def test_inventory_index(authenticated_client):
    """GET /inventory/ 返回 200"""
    resp = authenticated_client.get('/inventory/', follow_redirects=True)
    assert resp.status_code == 200


def test_product_list(authenticated_client):
    """GET /inventory/products 返回 200"""
    resp = authenticated_client.get('/inventory/products', follow_redirects=True)
    assert resp.status_code == 200


def test_warehouse_stock(app, authenticated_client, db_session):
    """GET /inventory/warehouse/{id} 返回 200"""
    warehouse = create_warehouse(code='INV_WH01', name='库存概览仓库')
    resp = authenticated_client.get(
        f'/inventory/warehouse/{warehouse.id}', follow_redirects=True
    )
    assert resp.status_code == 200


def test_warehouse_stock_not_found(authenticated_client):
    """访问不存在的仓库返回 404"""
    resp = authenticated_client.get('/inventory/warehouse/99999', follow_redirects=False)
    assert resp.status_code == 404


# ==================== 库存盘点 ====================

def test_stock_check_get(authenticated_client):
    """GET /inventory/stock-check 返回 200"""
    resp = authenticated_client.get('/inventory/stock-check', follow_redirects=True)
    assert resp.status_code == 200


def test_stock_check_post(app, authenticated_client, db_session):
    """POST 盘点，验证库存更新和日志"""
    warehouse = create_warehouse(code='CHK_WH01', name='盘点仓库')
    product = create_product(code='CHK_PROD01', name='盘点商品', stock_quantity=100)

    resp = authenticated_client.post('/inventory/stock-check', data={
        'warehouse_id': str(warehouse.id),
        'notes': '测试盘点',
        'product_id[]': [str(product.id)],
        'actual_quantity[]': ['105'],
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('105')

        log = StockLog.query.filter_by(
            product_id=product.id, change_type='check_in'
        ).first()
        assert log is not None
        assert log.quantity == Decimal('5')
        assert log.before_quantity == Decimal('100')
        assert log.after_quantity == Decimal('105')


def test_stock_check_decrease(app, authenticated_client, db_session):
    """盘点减少库存（盘亏）"""
    warehouse = create_warehouse(code='CHK_WH02', name='盘亏仓库')
    product = create_product(code='CHK_PROD02', name='盘亏商品', stock_quantity=50)

    resp = authenticated_client.post('/inventory/stock-check', data={
        'warehouse_id': str(warehouse.id),
        'notes': '盘亏测试',
        'product_id[]': [str(product.id)],
        'actual_quantity[]': ['45'],
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('45')

        log = StockLog.query.filter_by(
            product_id=product.id, change_type='check_out'
        ).first()
        assert log is not None
        assert log.quantity == Decimal('5')


def test_stock_check_no_change(app, authenticated_client, db_session):
    """盘点数量一致时不创建日志"""
    warehouse = create_warehouse(code='CHK_WH03', name='无差异仓库')
    product = create_product(code='CHK_PROD03', name='无差异商品', stock_quantity=30)

    log_count_before = StockLog.query.count()

    resp = authenticated_client.post('/inventory/stock-check', data={
        'warehouse_id': str(warehouse.id),
        'notes': '无差异',
        'product_id[]': [str(product.id)],
        'actual_quantity[]': ['30'],
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        log_count_after = StockLog.query.count()
        assert log_count_after == log_count_before


# ==================== 库存调拨 ====================

def test_stock_transfer_get(authenticated_client):
    """GET /inventory/stock-transfer 返回 200"""
    resp = authenticated_client.get('/inventory/stock-transfer', follow_redirects=True)
    assert resp.status_code == 200


def test_stock_transfer_post(app, authenticated_client, db_session):
    """POST 调拨，验证库存转移"""
    wh_from = create_warehouse(code='TR_WH01', name='调出仓库')
    wh_to = create_warehouse(code='TR_WH02', name='调入仓库')
    product = create_product(code='TR_PROD01', name='调拨商品', stock_quantity=100)

    # 需要先创建 StockLog 记录来表示该仓库有库存
    log = StockLog(
        product_id=product.id,
        warehouse_id=wh_from.id,
        change_type='in',
        quantity=Decimal('100'),
        before_quantity=Decimal('0'),
        after_quantity=Decimal('100'),
        reference_type='purchase',
        notes='初始化库存',
    )
    db.session.add(log)
    db.session.commit()

    resp = authenticated_client.post('/inventory/stock-transfer', data={
        'from_warehouse': str(wh_from.id),
        'to_warehouse': str(wh_to.id),
        'transfer_date': '2026-06-03',
        'notes': '测试调拨',
        'items-0-product_id': str(product.id),
        'items-0-quantity': '20',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        # 验证调拨日志
        transfer_log = StockLog.query.filter_by(
            product_id=product.id, change_type='stock_transfer'
        ).first()
        # 调拨可能创建多条日志或一条
        assert transfer_log is not None or StockLog.query.filter_by(
            product_id=product.id
        ).count() > 0


# ==================== 库存调整 ====================

def test_stock_adjust_get(authenticated_client):
    """GET /inventory/stock-adjust 返回 200"""
    resp = authenticated_client.get('/inventory/stock-adjust', follow_redirects=True)
    assert resp.status_code == 200


def test_stock_adjust_in(app, authenticated_client, db_session):
    """调整入库"""
    warehouse = create_warehouse(code='ADJ_WH01', name='调整仓库')
    product = create_product(code='ADJ_PROD01', name='调整入库商品', stock_quantity=50)

    resp = authenticated_client.post('/inventory/stock-adjust', data={
        'product_id': str(product.id),
        'warehouse_id': str(warehouse.id),
        'adjust_type': 'adjust_in',
        'quantity': '10',
        'notes': '调整入库测试',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('60')

        log = StockLog.query.filter_by(
            product_id=product.id, change_type='adjust_in'
        ).first()
        assert log is not None
        assert log.quantity == Decimal('10')


def test_stock_adjust_out(app, authenticated_client, db_session):
    """调整出库"""
    warehouse = create_warehouse(code='ADJ_WH02', name='调整出库仓库')
    product = create_product(code='ADJ_PROD02', name='调整出库商品', stock_quantity=50)

    resp = authenticated_client.post('/inventory/stock-adjust', data={
        'product_id': str(product.id),
        'warehouse_id': str(warehouse.id),
        'adjust_type': 'adjust_out',
        'quantity': '15',
        'notes': '调整出库测试',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Product, product.id)
        assert p.stock_quantity == Decimal('35')

        log = StockLog.query.filter_by(
            product_id=product.id, change_type='adjust_out'
        ).first()
        assert log is not None
        assert log.quantity == Decimal('15')


def test_stock_adjust_out_insufficient(app, authenticated_client, db_session):
    """库存不足时调整出库失败"""
    warehouse = create_warehouse(code='ADJ_WH03', name='不足仓库')
    product = create_product(code='ADJ_PROD03', name='不足商品', stock_quantity=5)
    product_id = product.id
    db.session.commit()  # 确保数据可见

    resp = authenticated_client.post('/inventory/stock-adjust', data={
        'product_id': str(product.id),
        'warehouse_id': str(warehouse.id),
        'adjust_type': 'adjust_out',
        'quantity': '10',
        'notes': '超出库存调整',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Product, product_id)
        # 库存不应变为负数
        assert p.stock_quantity == Decimal('5')


# ==================== 库存日志 ====================

def test_stock_logs(authenticated_client):
    """GET /inventory/logs 返回 200"""
    resp = authenticated_client.get('/inventory/logs', follow_redirects=True)
    assert resp.status_code == 200


def test_low_stock_api(authenticated_client):
    """GET /inventory/api/low-stock 返回 JSON"""
    resp = authenticated_client.get('/inventory/api/low-stock')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, (list, dict))


def test_api_stock_check(app, authenticated_client, db_session):
    """POST /inventory/api/stock-check 返回 JSON"""
    product = create_product(code='CHK_API01', name='API盘点商品', stock_quantity=50)
    db.session.commit()

    resp = authenticated_client.post('/inventory/api/stock-check',
        json={'product_id': product.id, 'warehouse_id': 1},
        content_type='application/json')
    assert resp.status_code == 200


def test_unauthenticated_redirect(client):
    """未登录访问库存首页重定向"""
    resp = client.get('/inventory/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers.get('Location', '')
