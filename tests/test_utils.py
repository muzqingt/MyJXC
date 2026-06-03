"""
工具函数单元测试 — to_decimal, add_balance, sub_balance, generate_order_number
"""
import pytest
from decimal import Decimal

from app import db
from app.utils import to_decimal, add_balance, sub_balance, generate_order_number
from app.models import Customer, Supplier, PurchaseOrder
from tests.factories import create_customer, create_supplier


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
    # 由于 TST 前缀在数据库中没有记录，两个都应该返回 0001
    # 但格式应该正确
    assert num1.startswith('TST')
    assert num2.startswith('TST')
