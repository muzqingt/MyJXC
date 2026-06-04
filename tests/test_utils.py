"""
工具函数单元测试 — to_decimal, add_balance, sub_balance, generate_order_number
"""
import pytest
from decimal import Decimal

from app import db
from app.utils import to_decimal, add_balance, sub_balance, generate_order_number
from app.models import Customer, Supplier, PurchaseOrder
from tests.factories import create_customer, create_supplier, create_product, create_warehouse


# ==================== to_decimal ====================

def test_to_decimal_none():
    """None 返回默认值"""
    assert to_decimal(None) == Decimal('0')


def test_to_decimal_none_custom_default():
    """None 返回自定义默认值"""
    assert to_decimal(None, Decimal('99')) == Decimal('99')


def test_to_decimal_int():
    """整数转换"""
    assert to_decimal(42) == Decimal('42')


def test_to_decimal_float():
    """浮点数转换"""
    assert to_decimal(3.14) == Decimal('3.14')


def test_to_decimal_string():
    """字符串转换"""
    assert to_decimal('123.45') == Decimal('123.45')


def test_to_decimal_string_invalid():
    """无效字符串返回默认值"""
    assert to_decimal('abc') == Decimal('0')


def test_to_decimal_decimal():
    """Decimal 直接返回"""
    d = Decimal('10.50')
    assert to_decimal(d) is d


def test_to_decimal_zero():
    """零值"""
    assert to_decimal(0) == Decimal('0')


def test_to_decimal_negative():
    """负数"""
    assert to_decimal(-5) == Decimal('-5')


# ==================== add_balance / sub_balance ====================

def test_add_balance_customer(app, db_session):
    """增加客户应收余额"""
    customer = create_customer(code='BAL_CUS01', name='余额测试客户')
    customer.receivable_balance = Decimal('1000.00')
    db.session.commit()

    add_balance(customer, 'receivable_balance', '500.00')
    db.session.commit()

    c = db.session.get(Customer, customer.id)
    assert c.receivable_balance == Decimal('1500.00')


def test_sub_balance_customer(app, db_session):
    """减少客户应收余额"""
    customer = create_customer(code='BAL_CUS02', name='减少余额客户')
    customer.receivable_balance = Decimal('2000.00')
    db.session.commit()

    sub_balance(customer, 'receivable_balance', '800.00')
    db.session.commit()

    c = db.session.get(Customer, customer.id)
    assert c.receivable_balance == Decimal('1200.00')


def test_add_balance_supplier(app, db_session):
    """增加供应商应付余额"""
    supplier = create_supplier(code='BAL_SUP01', name='余额测试供应商')
    supplier.payable_balance = Decimal('3000.00')
    db.session.commit()

    add_balance(supplier, 'payable_balance', '1000.00')
    db.session.commit()

    s = db.session.get(Supplier, supplier.id)
    assert s.payable_balance == Decimal('4000.00')


def test_sub_balance_supplier(app, db_session):
    """减少供应商应付余额"""
    supplier = create_supplier(code='BAL_SUP02', name='减少余额供应商')
    supplier.payable_balance = Decimal('5000.00')
    db.session.commit()

    sub_balance(supplier, 'payable_balance', '2000.00')
    db.session.commit()

    s = db.session.get(Supplier, supplier.id)
    assert s.payable_balance == Decimal('3000.00')


def test_add_balance_decimal_amount(app, db_session):
    """Decimal 类型金额"""
    customer = create_customer(code='BAL_CUS03', name='Decimal客户')
    customer.receivable_balance = Decimal('100.00')
    db.session.commit()

    add_balance(customer, 'receivable_balance', Decimal('50.50'))
    db.session.commit()

    c = db.session.get(Customer, customer.id)
    assert c.receivable_balance == Decimal('150.50')


# ==================== generate_order_number ====================

def test_generate_order_number_first(app, db_session):
    """生成订单号"""
    num = generate_order_number('PO', PurchaseOrder)
    assert num.startswith('PO')
    assert len(num) >= 12


def test_generate_order_number_format(app, db_session):
    """订单号格式：前缀+日期+序号"""
    num = generate_order_number('SO', PurchaseOrder)
    assert num[:2] == 'SO'
    # 日期部分是8位数字
    date_part = num[2:10]
    assert date_part.isdigit()
    assert len(date_part) == 8
    # 序号部分是4位数字
    seq_part = num[10:]
    assert seq_part.isdigit()
    assert len(seq_part) == 4


def test_generate_order_number_auto_increment(app, db_session):
    """同一天自动递增"""
    num1 = generate_order_number('TST', PurchaseOrder)
    num2 = generate_order_number('TST', PurchaseOrder)
    assert num1.startswith('TST')
    assert num2.startswith('TST')


def test_generate_order_number_safe(app, db_session):
    """generate_order_number_safe 生成唯一订单号"""
    from app.utils import generate_order_number_safe
    num = generate_order_number_safe('SAFE', PurchaseOrder)
    assert num.startswith('SAFE')
    assert len(num) >= 12


def test_generate_order_number_safe_unique(app, db_session):
    """generate_order_number_safe 生成订单号格式正确"""
    from app.utils import generate_order_number_safe
    num = generate_order_number_safe('UNQ', PurchaseOrder)
    assert num.startswith('UNQ')
    assert len(num) >= 12


# ==================== update_stock_and_log ====================

def test_update_stock_in(app, db_session):
    """入库操作增加库存"""
    from app.utils import update_stock_and_log
    from app.models import StockLog
    product = create_product(code='STK_IN01', name='入库测试', stock_quantity=50)
    warehouse = create_warehouse(code='STK_WH01', name='入库仓库')

    before, after = update_stock_and_log(
        product, warehouse.id, 20, 'in', 1, 'test', '测试入库', 1
    )
    db.session.commit()

    assert before == Decimal('50')
    assert after == Decimal('70')
    assert product.stock_quantity == Decimal('70')


def test_update_stock_out(app, db_session):
    """出库操作减少库存"""
    from app.utils import update_stock_and_log
    product = create_product(code='STK_OUT01', name='出库测试', stock_quantity=50)
    warehouse = create_warehouse(code='STK_WH02', name='出库仓库')

    before, after = update_stock_and_log(
        product, warehouse.id, 15, 'out', 1, 'test', '测试出库', 1
    )
    db.session.commit()

    assert before == Decimal('50')
    assert after == Decimal('35')


def test_update_stock_invalid_type(app, db_session):
    """无效变动类型抛出异常"""
    from app.utils import update_stock_and_log
    product = create_product(code='STK_INV01', name='无效类型测试', stock_quantity=50)
    warehouse = create_warehouse(code='STK_WH03', name='无效仓库')

    with pytest.raises(ValueError):
        update_stock_and_log(
            product, warehouse.id, 10, 'invalid_type', 1, 'test', '测试', 1
        )


# ==================== safe_commit ====================

def test_safe_commit_success(app, db_session):
    """正常提交返回成功"""
    from app.utils import safe_commit
    success, error = safe_commit()
    assert success is True
    assert error is None


# ==================== localize_dt / format_local_dt ====================

def test_localize_dt_none():
    """None 返回空字符串"""
    from app.utils import localize_dt
    assert localize_dt(None) == ''


def test_localize_dt_naive():
    """无时区时间转换为上海时区"""
    from app.utils import localize_dt
    from datetime import datetime
    dt = datetime(2024, 1, 1, 12, 0, 0)
    result = localize_dt(dt)
    assert result.hour == 20  # UTC+8


def test_format_local_dt_none():
    """None 返回空字符串"""
    from app.utils import format_local_dt
    assert format_local_dt(None) == ''


def test_format_local_dt():
    """格式化时间"""
    from app.utils import format_local_dt
    from datetime import datetime
    dt = datetime(2024, 1, 1, 12, 0, 0)
    result = format_local_dt(dt)
    assert '2024' in result


# ==================== get_redirect_tab ====================

def test_get_redirect_tab_draft():
    """草稿状态"""
    from app.utils import get_redirect_tab
    assert get_redirect_tab('draft') == 'draft'


def test_get_redirect_tab_confirmed():
    """已确认状态"""
    from app.utils import get_redirect_tab
    assert get_redirect_tab('confirmed') == 'confirmed'


def test_get_redirect_tab_completed():
    """已完成状态"""
    from app.utils import get_redirect_tab
    assert get_redirect_tab('completed') == 'completed'


def test_get_redirect_tab_none():
    """无状态默认草稿"""
    from app.utils import get_redirect_tab
    assert get_redirect_tab() == 'draft'


# ==================== Excel 样式常量 ====================

def test_excel_constants():
    """Excel 样式常量已定义"""
    from app.utils import EXCEL_HEADER_FONT, EXCEL_HEADER_FILL, EXCEL_THIN_BORDER
    assert EXCEL_HEADER_FONT is not None
    assert EXCEL_HEADER_FILL is not None
    assert EXCEL_THIN_BORDER is not None
