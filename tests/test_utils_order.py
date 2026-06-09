"""
订单工具函数测试
"""
import pytest
from decimal import Decimal

from app import db
from app.models import StockLog, Product
from app.utils_order import (
    parse_reference_ids, create_stock_log,
    rebuild_items_on_error,
)
from tests.factories import create_product, create_warehouse


# ==================== parse_reference_ids ====================

def test_parse_reference_ids_normal():
    """正常解析逗号分隔的 ID"""
    result = parse_reference_ids("1,2,3")
    assert result == [1, 2, 3]


def test_parse_reference_ids_with_spaces():
    """解析带空格的 ID"""
    result = parse_reference_ids("1, 2, 3")
    assert result == [1, 2, 3]


def test_parse_reference_ids_empty():
    """空字符串返回空列表"""
    result = parse_reference_ids("")
    assert result == []


def test_parse_reference_ids_none():
    """None 返回空列表"""
    result = parse_reference_ids(None)
    assert result == []


def test_parse_reference_ids_invalid():
    """无效格式返回空列表"""
    result = parse_reference_ids("abc,def")
    assert result == []


def test_parse_reference_ids_single():
    """单个 ID"""
    result = parse_reference_ids("42")
    assert result == [42]


# ==================== create_stock_log ====================

def test_create_stock_log_in(app, db_session):
    """创建入库日志"""
    product = create_product(code='CSL_PROD01', name='日志商品', stock_quantity=50)
    warehouse = create_warehouse(code='CSL_WH01', name='日志仓库')

    log = create_stock_log(
        product=product,
        warehouse_id=warehouse.id,
        change_type='in',
        quantity=Decimal('20'),
        reference_id=1,
        reference_type='test',
        notes='测试入库',
        user_id=1,
    )
    db.session.commit()

    assert log.id is not None
    assert log.before_quantity == Decimal('50')
    assert log.after_quantity == Decimal('70')
    assert product.stock_quantity == Decimal('70')


def test_create_stock_log_out(app, db_session):
    """创建出库日志"""
    product = create_product(code='CSL_PROD02', name='出库商品', stock_quantity=100)
    warehouse = create_warehouse(code='CSL_WH02', name='出库仓库')

    log = create_stock_log(
        product=product,
        warehouse_id=warehouse.id,
        change_type='out',
        quantity=Decimal('30'),
        reference_id=2,
        reference_type='test',
        notes='测试出库',
        user_id=1,
    )
    db.session.commit()

    assert log.before_quantity == Decimal('100')
    assert log.after_quantity == Decimal('70')
    assert product.stock_quantity == Decimal('70')


def test_create_stock_log_adjust_in(app, db_session):
    """创建调整入库日志"""
    product = create_product(code='CSL_PROD03', name='调整商品', stock_quantity=50)
    warehouse = create_warehouse(code='CSL_WH03', name='调整仓库')

    log = create_stock_log(
        product=product,
        warehouse_id=warehouse.id,
        change_type='adjust_in',
        quantity=Decimal('10'),
        reference_id=3,
        reference_type='test',
    )
    db.session.commit()

    assert log.after_quantity == Decimal('60')
    assert product.stock_quantity == Decimal('60')


# ==================== rebuild_items_on_error ====================

def test_rebuild_items_on_error(app, db_session):
    """重建商品明细数据"""
    product = create_product(code='RIO_PROD01', name='重建商品')

    items = rebuild_items_on_error(
        product_ids=[str(product.id)],
        quantities=['10'],
        unit_prices=['50'],
    )

    assert len(items) == 1
    assert items[0]['product_id'] == product.id
    assert items[0]['quantity'] == '10'


def test_rebuild_items_on_error_invalid_id(app, db_session):
    """无效 ID 跳过"""
    items = rebuild_items_on_error(
        product_ids=['abc'],
        quantities=['10'],
        unit_prices=['50'],
    )

    assert len(items) == 0


def test_rebuild_items_on_error_empty(app, db_session):
    """空列表返回空"""
    items = rebuild_items_on_error(
        product_ids=[],
        quantities=[],
        unit_prices=[],
    )

    assert len(items) == 0
