"""
财务模块测试 — 收款、付款、费用、利润分析
"""
import pytest
from datetime import date
from decimal import Decimal

from app import db
from app.models import Receipt, Payment, Expense, Customer, Supplier
from tests.factories import create_customer, create_supplier


# ==================== 财务首页 ====================

def test_finance_index(authenticated_client):
    """GET /finance/ 返回 200"""
    resp = authenticated_client.get('/finance/', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 收款管理 ====================

def test_receipts_list(authenticated_client):
    """GET /finance/receipts 返回 200"""
    resp = authenticated_client.get('/finance/receipts', follow_redirects=True)
    assert resp.status_code == 200


def test_add_receipt_get(authenticated_client):
    """GET /finance/receipt/add 返回 200"""
    resp = authenticated_client.get('/finance/receipt/add', follow_redirects=True)
    assert resp.status_code == 200


def test_add_receipt_post(app, authenticated_client, db_session):
    """POST 添加收款记录"""
    customer = create_customer(code='FIN_CUS01', name='收款测试客户')

    resp = authenticated_client.post('/finance/receipt/add', data={
        'customer_id': str(customer.id),
        'amount': '1000.00',
        'receipt_date': date.today().strftime('%Y-%m-%d'),
        'payment_method': 'cash',
        'reference_type': 'other',
        'notes': '测试收款',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        receipt = Receipt.query.filter_by(customer_id=customer.id).first()
        assert receipt is not None
        assert receipt.amount == Decimal('1000.00')


def test_view_receipt(app, authenticated_client, db_session):
    """查看收款详情"""
    customer = create_customer(code='FIN_CUS02', name='查看收款客户')

    receipt = Receipt(
        receipt_number='RC_TEST001',
        customer_id=customer.id,
        amount=Decimal('500.00'),
        receipt_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(receipt)
    db.session.commit()

    resp = authenticated_client.get(f'/finance/receipt/{receipt.id}', follow_redirects=True)
    assert resp.status_code == 200


def test_delete_receipt(app, authenticated_client, db_session):
    """删除收款记录"""
    customer = create_customer(code='FIN_CUS03', name='删除收款客户')

    receipt = Receipt(
        receipt_number='RC_TEST002',
        customer_id=customer.id,
        amount=Decimal('300.00'),
        receipt_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(receipt)
    db.session.commit()
    receipt_id = receipt.id

    resp = authenticated_client.post(f'/finance/receipt/{receipt.id}/delete', follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        deleted = db.session.get(Receipt, receipt_id)
        assert deleted is None


def test_receipt_updates_customer_balance(app, authenticated_client, db_session):
    """收款后客户应收余额减少"""
    customer = create_customer(code='FIN_CUS04', name='余额测试客户')
    customer.receivable_balance = Decimal('5000.00')
    db.session.commit()

    authenticated_client.post('/finance/receipt/add', data={
        'customer_id': str(customer.id),
        'amount': '1000.00',
        'receipt_date': date.today().strftime('%Y-%m-%d'),
        'payment_method': 'bank_transfer',
        'reference_type': 'other',
    }, follow_redirects=True)

    with app.app_context():
        c = db.session.get(Customer, customer.id)
        assert c.receivable_balance == Decimal('4000.00')


# ==================== 付款管理 ====================

def test_payments_list(authenticated_client):
    """GET /finance/payments 返回 200"""
    resp = authenticated_client.get('/finance/payments', follow_redirects=True)
    assert resp.status_code == 200


def test_add_payment_get(authenticated_client):
    """GET /finance/payment/add 返回 200"""
    resp = authenticated_client.get('/finance/payment/add', follow_redirects=True)
    assert resp.status_code == 200


def test_add_payment_post(app, authenticated_client, db_session):
    """POST 添加付款记录"""
    supplier = create_supplier(code='FIN_SUP01', name='付款测试供应商')

    resp = authenticated_client.post('/finance/payment/add', data={
        'supplier_id': str(supplier.id),
        'amount': '2000.00',
        'payment_date': date.today().strftime('%Y-%m-%d'),
        'payment_method': 'bank_transfer',
        'reference_type': 'other',
        'notes': '测试付款',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        payment = Payment.query.filter_by(supplier_id=supplier.id).first()
        assert payment is not None
        assert payment.amount == Decimal('2000.00')


def test_view_payment(app, authenticated_client, db_session):
    """查看付款详情"""
    supplier = create_supplier(code='FIN_SUP02', name='查看付款供应商')

    payment = Payment(
        payment_number='PY_TEST001',
        supplier_id=supplier.id,
        amount=Decimal('800.00'),
        payment_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(payment)
    db.session.commit()

    resp = authenticated_client.get(f'/finance/payment/{payment.id}', follow_redirects=True)
    assert resp.status_code == 200


def test_delete_payment(app, authenticated_client, db_session):
    """删除付款记录"""
    supplier = create_supplier(code='FIN_SUP03', name='删除付款供应商')

    payment = Payment(
        payment_number='PY_TEST002',
        supplier_id=supplier.id,
        amount=Decimal('400.00'),
        payment_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(payment)
    db.session.commit()
    payment_id = payment.id

    resp = authenticated_client.post(f'/finance/payment/{payment.id}/delete', follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        deleted = db.session.get(Payment, payment_id)
        assert deleted is None


# ==================== 费用管理 ====================

def test_expenses_list(authenticated_client):
    """GET /finance/expenses 返回 200"""
    resp = authenticated_client.get('/finance/expenses', follow_redirects=True)
    assert resp.status_code == 200


def test_add_expense_get(authenticated_client):
    """GET /finance/expense/add 返回 200"""
    resp = authenticated_client.get('/finance/expense/add', follow_redirects=True)
    assert resp.status_code == 200


def test_add_expense_post(app, authenticated_client, db_session):
    """POST 添加费用记录"""
    resp = authenticated_client.post('/finance/expense/add', data={
        'category': '办公费',
        'amount': '150.00',
        'expense_date': date.today().strftime('%Y-%m-%d'),
        'payee': '办公用品店',
        'payment_method': 'cash',
        'notes': '购买办公用品',
    }, follow_redirects=True)

    assert resp.status_code == 200

    with app.app_context():
        expense = Expense.query.filter_by(category='办公费').first()
        assert expense is not None
        assert expense.amount == Decimal('150.00')


def test_delete_expense(app, authenticated_client, db_session):
    """删除费用记录"""
    expense = Expense(
        expense_number='EX_TEST001',
        category='测试费用',
        amount=Decimal('100.00'),
        expense_date=date.today(),
        payment_method='cash',
        created_by=1,
    )
    db.session.add(expense)
    db.session.commit()
    expense_id = expense.id

    resp = authenticated_client.post(f'/finance/expense/{expense.id}/delete', follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        deleted = db.session.get(Expense, expense_id)
        assert deleted is None


# ==================== 利润分析 ====================

def test_profit_analysis(authenticated_client):
    """GET /finance/profit-analysis 返回 200"""
    resp = authenticated_client.get('/finance/profit-analysis', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 应收应付 ====================

def test_ar_ap_search(authenticated_client):
    """GET /finance/ar-ap-search 返回 200"""
    resp = authenticated_client.get('/finance/ar-ap-search', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 边界情况 ====================

def test_receipt_not_found_404(authenticated_client):
    """访问不存在的收款记录返回 404"""
    resp = authenticated_client.get('/finance/receipt/99999', follow_redirects=False)
    assert resp.status_code == 404


def test_payment_not_found_404(authenticated_client):
    """访问不存在的付款记录返回 404"""
    resp = authenticated_client.get('/finance/payment/99999', follow_redirects=False)
    assert resp.status_code == 404


def test_unauthenticated_redirect(client):
    """未登录访问财务首页重定向"""
    resp = client.get('/finance/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers.get('Location', '')


def test_financial_summary_api(authenticated_client):
    """GET /finance/api/financial-summary 返回 JSON"""
    resp = authenticated_client.get('/finance/api/financial-summary')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)


def test_export_receipts(authenticated_client):
    """GET /finance/export-receipts 导出收款"""
    resp = authenticated_client.get('/finance/export-receipts')
    assert resp.status_code == 200


def test_export_payments(authenticated_client):
    """GET /finance/export-payments 导出付款"""
    resp = authenticated_client.get('/finance/export-payments')
    assert resp.status_code == 200


def test_export_expenses(authenticated_client):
    """GET /finance/export-expenses 导出费用"""
    resp = authenticated_client.get('/finance/export-expenses')
    assert resp.status_code == 200
