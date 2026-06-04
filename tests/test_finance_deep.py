"""
财务模块深度测试 — 编辑、导出、筛选
"""
import pytest
from datetime import date
from decimal import Decimal

from app import db
from app.models import Receipt, Payment, Expense
from tests.factories import create_customer, create_supplier
from tests.helpers import get_page, post_page


# ==================== 收款编辑 ====================

def test_edit_receipt_get(app, authenticated_client, db_session):
    """GET 编辑收款页面"""
    customer = create_customer(code='FED_CUS01', name='编辑收款客户')

    receipt = Receipt(
        receipt_number='RC_ED001',
        customer_id=customer.id,
        amount=Decimal('1000.00'),
        receipt_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(receipt)
    db.session.commit()

    get_page(authenticated_client, f'/finance/receipt/{receipt.id}/edit')


def test_edit_receipt_post(app, authenticated_client, db_session):
    """POST 更新收款记录"""
    customer = create_customer(code='FED_CUS02', name='更新收款客户')

    receipt = Receipt(
        receipt_number='RC_ED002',
        customer_id=customer.id,
        amount=Decimal('500.00'),
        receipt_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(receipt)
    db.session.commit()

    post_page(authenticated_client, f'/finance/receipt/{receipt.id}/edit', {
        'customer_id': str(customer.id),
        'amount': '600.00',
        'receipt_date': date.today().strftime('%Y-%m-%d'),
        'payment_method': 'bank_transfer',
    })


# ==================== 付款编辑 ====================

def test_edit_payment_get(app, authenticated_client, db_session):
    """GET 编辑付款页面"""
    supplier = create_supplier(code='FED_SUP01', name='编辑付款供应商')

    payment = Payment(
        payment_number='PY_ED001',
        supplier_id=supplier.id,
        amount=Decimal('2000.00'),
        payment_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(payment)
    db.session.commit()

    get_page(authenticated_client, f'/finance/payment/{payment.id}/edit')


def test_edit_payment_post(app, authenticated_client, db_session):
    """POST 更新付款记录"""
    supplier = create_supplier(code='FED_SUP02', name='更新付款供应商')

    payment = Payment(
        payment_number='PY_ED002',
        supplier_id=supplier.id,
        amount=Decimal('800.00'),
        payment_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(payment)
    db.session.commit()

    post_page(authenticated_client, f'/finance/payment/{payment.id}/edit', {
        'supplier_id': str(supplier.id),
        'amount': '900.00',
        'payment_date': date.today().strftime('%Y-%m-%d'),
        'payment_method': 'bank_transfer',
    })


# ==================== 导出 ====================

def test_export_profit_analysis(authenticated_client):
    """导出利润分析"""
    get_page(authenticated_client, '/finance/export-profit-analysis')
