"""
财务模块深度覆盖测试
"""
import pytest
from datetime import date
from decimal import Decimal
from tests.helpers import get_page, post_page
from tests.factories import create_customer, create_supplier
from app import db
from app.models import Receipt, Payment, Expense


def test_finance_index(authenticated_client):
    """财务首页"""
    get_page(authenticated_client, '/finance/')


def test_receipts_list(authenticated_client):
    """收款列表"""
    get_page(authenticated_client, '/finance/receipts')


def test_add_receipt_get(authenticated_client):
    """添加收款页面"""
    get_page(authenticated_client, '/finance/receipt/add')


def test_add_receipt_post(app, authenticated_client, db_session):
    """添加收款"""
    customer = create_customer(code='FC_CUS01', name='财务客户')
    post_page(authenticated_client, '/finance/receipt/add', {
        'customer_id': str(customer.id),
        'amount': '1000.00',
        'receipt_date': date.today().strftime('%Y-%m-%d'),
        'payment_method': 'cash',
        'reference_type': 'other',
    })


def test_view_receipt(app, authenticated_client, db_session):
    """查看收款"""
    customer = create_customer(code='FC_CUS02', name='查看收款客户')
    receipt = Receipt(
        receipt_number='FC_RC001',
        customer_id=customer.id,
        amount=Decimal('500.00'),
        receipt_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(receipt)
    db.session.commit()
    get_page(authenticated_client, f'/finance/receipt/{receipt.id}')


def test_edit_receipt_get(app, authenticated_client, db_session):
    """编辑收款页面"""
    customer = create_customer(code='FC_CUS03', name='编辑收款客户')
    receipt = Receipt(
        receipt_number='FC_RC002',
        customer_id=customer.id,
        amount=Decimal('500.00'),
        receipt_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(receipt)
    db.session.commit()
    get_page(authenticated_client, f'/finance/receipt/{receipt.id}/edit')


def test_delete_receipt(app, authenticated_client, db_session):
    """删除收款"""
    customer = create_customer(code='FC_CUS04', name='删除收款客户')
    receipt = Receipt(
        receipt_number='FC_RC003',
        customer_id=customer.id,
        amount=Decimal('300.00'),
        receipt_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(receipt)
    db.session.commit()
    resp = authenticated_client.post(
        f'/finance/receipt/{receipt.id}/delete', follow_redirects=True
    )
    assert resp.status_code == 200


def test_payments_list(authenticated_client):
    """付款列表"""
    get_page(authenticated_client, '/finance/payments')


def test_add_payment_get(authenticated_client):
    """添加付款页面"""
    get_page(authenticated_client, '/finance/payment/add')


def test_add_payment_post(app, authenticated_client, db_session):
    """添加付款"""
    supplier = create_supplier(code='FC_SUP01', name='财务供应商')
    post_page(authenticated_client, '/finance/payment/add', {
        'supplier_id': str(supplier.id),
        'amount': '2000.00',
        'payment_date': date.today().strftime('%Y-%m-%d'),
        'payment_method': 'bank_transfer',
        'reference_type': 'other',
    })


def test_view_payment(app, authenticated_client, db_session):
    """查看付款"""
    supplier = create_supplier(code='FC_SUP02', name='查看付款供应商')
    payment = Payment(
        payment_number='FC_PY001',
        supplier_id=supplier.id,
        amount=Decimal('800.00'),
        payment_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(payment)
    db.session.commit()
    get_page(authenticated_client, f'/finance/payment/{payment.id}')


def test_delete_payment(app, authenticated_client, db_session):
    """删除付款"""
    supplier = create_supplier(code='FC_SUP03', name='删除付款供应商')
    payment = Payment(
        payment_number='FC_PY002',
        supplier_id=supplier.id,
        amount=Decimal('400.00'),
        payment_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(payment)
    db.session.commit()
    resp = authenticated_client.post(
        f'/finance/payment/{payment.id}/delete', follow_redirects=True
    )
    assert resp.status_code == 200


def test_expenses_list(authenticated_client):
    """费用列表"""
    get_page(authenticated_client, '/finance/expenses')


def test_add_expense_get(authenticated_client):
    """添加费用页面"""
    get_page(authenticated_client, '/finance/expense/add')


def test_add_expense_post(app, authenticated_client, db_session):
    """添加费用"""
    post_page(authenticated_client, '/finance/expense/add', {
        'category': '办公费',
        'amount': '150.00',
        'expense_date': date.today().strftime('%Y-%m-%d'),
        'payee': '办公用品店',
        'payment_method': 'cash',
    })


def test_delete_expense(app, authenticated_client, db_session):
    """删除费用"""
    expense = Expense(
        expense_number='FC_EX001',
        category='测试费用',
        amount=Decimal('100.00'),
        expense_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(expense)
    db.session.commit()
    resp = authenticated_client.post(
        f'/finance/expense/{expense.id}/delete', follow_redirects=True
    )
    assert resp.status_code == 200


def test_profit_analysis(authenticated_client):
    """利润分析"""
    get_page(authenticated_client, '/finance/profit-analysis')


def test_ar_ap_search(authenticated_client):
    """应收应付"""
    get_page(authenticated_client, '/finance/ar-ap-search')


def test_export_receipts(authenticated_client):
    """导出收款"""
    get_page(authenticated_client, '/finance/export-receipts')


def test_export_payments(authenticated_client):
    """导出付款"""
    get_page(authenticated_client, '/finance/export-payments')


def test_export_expenses(authenticated_client):
    """导出费用"""
    get_page(authenticated_client, '/finance/export-expenses')


def test_export_profit(authenticated_client):
    """导出利润分析"""
    get_page(authenticated_client, '/finance/export-profit-analysis')


def test_financial_summary_api(authenticated_client):
    """财务汇总 API"""
    get_page(authenticated_client, '/finance/api/financial-summary')


def test_unauthenticated(client):
    """未登录重定向"""
    resp = client.get('/finance/', follow_redirects=False)
    assert resp.status_code == 302
