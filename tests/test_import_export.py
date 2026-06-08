"""
导入/导出验证测试
"""
import pytest
import io
from decimal import Decimal
from datetime import date
from app import db
from app.models import (
    Product, Category, Supplier, Customer, Warehouse,
    PurchaseOrder, SalesOrder, StockLog
)
from tests.factories import (
    create_product, create_category, create_supplier, create_customer,
    create_warehouse, create_purchase_order, create_sales_order
)


# ==================== 商品导入验证 ====================

def test_product_import_valid(authenticated_client, app, db_session):
    """商品导入 - 有效数据"""
    from werkzeug.datastructures import FileStorage

    csv_content = "code,name,unit,purchase_price,sale_price\nIMP_VALID_001,有效商品1,个,50,100\nIMP_VALID_002,有效商品2,个,30,60"
    csv_file = FileStorage(
        stream=io.BytesIO(csv_content.encode()),
        filename='products.csv',
        content_type='text/csv'
    )

    resp = authenticated_client.post('/product/import', data={
        'file': csv_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_product_import_empty_file(authenticated_client, app, db_session):
    """商品导入 - 空文件"""
    from werkzeug.datastructures import FileStorage

    csv_content = "code,name,unit,purchase_price,sale_price\n"
    csv_file = FileStorage(
        stream=io.BytesIO(csv_content.encode()),
        filename='products.csv',
        content_type='text/csv'
    )

    resp = authenticated_client.post('/product/import', data={
        'file': csv_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_product_import_missing_columns(authenticated_client, app, db_session):
    """商品导入 - 缺少列"""
    from werkzeug.datastructures import FileStorage

    csv_content = "code,name\nIMP_MISSING_001,缺少列商品"
    csv_file = FileStorage(
        stream=io.BytesIO(csv_content.encode()),
        filename='products.csv',
        content_type='text/csv'
    )

    resp = authenticated_client.post('/product/import', data={
        'file': csv_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_product_import_duplicate_code(authenticated_client, app, db_session):
    """商品导入 - 重复编码"""
    create_product(code='IMP_DUP_001')

    from werkzeug.datastructures import FileStorage

    csv_content = "code,name,unit,purchase_price,sale_price\nIMP_DUP_001,重复编码商品,个,50,100"
    csv_file = FileStorage(
        stream=io.BytesIO(csv_content.encode()),
        filename='products.csv',
        content_type='text/csv'
    )

    resp = authenticated_client.post('/product/import', data={
        'file': csv_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_product_import_invalid_price(authenticated_client, app, db_session):
    """商品导入 - 无效价格"""
    from werkzeug.datastructures import FileStorage

    csv_content = "code,name,unit,purchase_price,sale_price\nIMP_PRICE_001,无效价格商品,个,abc,100"
    csv_file = FileStorage(
        stream=io.BytesIO(csv_content.encode()),
        filename='products.csv',
        content_type='text/csv'
    )

    resp = authenticated_client.post('/product/import', data={
        'file': csv_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_product_import_negative_price(authenticated_client, app, db_session):
    """商品导入 - 负数价格"""
    from werkzeug.datastructures import FileStorage

    csv_content = "code,name,unit,purchase_price,sale_price\nIMP_NEG_001,负数价格商品,个,-50,100"
    csv_file = FileStorage(
        stream=io.BytesIO(csv_content.encode()),
        filename='products.csv',
        content_type='text/csv'
    )

    resp = authenticated_client.post('/product/import', data={
        'file': csv_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_product_import_no_file(authenticated_client, app, db_session):
    """商品导入 - 无文件"""
    resp = authenticated_client.post('/product/import', data={}, follow_redirects=True)
    assert resp.status_code == 200


def test_product_import_invalid_file_type(authenticated_client, app, db_session):
    """商品导入 - 无效文件类型"""
    from werkzeug.datastructures import FileStorage

    txt_file = FileStorage(
        stream=io.BytesIO(b'this is not a csv file'),
        filename='products.txt',
        content_type='text/plain'
    )

    resp = authenticated_client.post('/product/import', data={
        'file': txt_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_product_import_template(authenticated_client):
    """商品导入模板下载"""
    resp = authenticated_client.get('/product/import/template')
    assert resp.status_code == 200
    assert len(resp.data) > 0


# ==================== 供应商导入验证 ====================

def test_supplier_import_valid(authenticated_client, app, db_session):
    """供应商导入 - 有效数据"""
    from werkzeug.datastructures import FileStorage

    csv_content = "code,name,contact_person,phone\nIMP_SUP_VALID_001,有效供应商1,张三,13800000001"
    csv_file = FileStorage(
        stream=io.BytesIO(csv_content.encode()),
        filename='suppliers.csv',
        content_type='text/csv'
    )

    resp = authenticated_client.post('/partner/suppliers/import', data={
        'file': csv_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_supplier_import_empty_file(authenticated_client, app, db_session):
    """供应商导入 - 空文件"""
    from werkzeug.datastructures import FileStorage

    csv_content = "code,name,contact_person,phone\n"
    csv_file = FileStorage(
        stream=io.BytesIO(csv_content.encode()),
        filename='suppliers.csv',
        content_type='text/csv'
    )

    resp = authenticated_client.post('/partner/suppliers/import', data={
        'file': csv_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_supplier_import_duplicate_code(authenticated_client, app, db_session):
    """供应商导入 - 重复编码"""
    create_supplier(code='IMP_SUP_DUP_001')

    from werkzeug.datastructures import FileStorage

    csv_content = "code,name,contact_person,phone\nIMP_SUP_DUP_001,重复编码供应商,张三,13800000001"
    csv_file = FileStorage(
        stream=io.BytesIO(csv_content.encode()),
        filename='suppliers.csv',
        content_type='text/csv'
    )

    resp = authenticated_client.post('/partner/suppliers/import', data={
        'file': csv_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_supplier_import_missing_columns(authenticated_client, app, db_session):
    """供应商导入 - 缺少列"""
    from werkzeug.datastructures import FileStorage

    csv_content = "code,name\nIMP_SUP_MISSING_001,缺少列供应商"
    csv_file = FileStorage(
        stream=io.BytesIO(csv_content.encode()),
        filename='suppliers.csv',
        content_type='text/csv'
    )

    resp = authenticated_client.post('/partner/suppliers/import', data={
        'file': csv_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_supplier_import_template(authenticated_client):
    """供应商导入模板下载"""
    resp = authenticated_client.get('/partner/suppliers/import/template')
    assert resp.status_code == 200
    assert len(resp.data) > 0


# ==================== 客户导入验证 ====================

def test_customer_import_valid(authenticated_client, app, db_session):
    """客户导入 - 有效数据"""
    from werkzeug.datastructures import FileStorage

    csv_content = "code,name,contact_person,phone\nIMP_CUS_VALID_001,有效客户1,李四,13900000001"
    csv_file = FileStorage(
        stream=io.BytesIO(csv_content.encode()),
        filename='customers.csv',
        content_type='text/csv'
    )

    resp = authenticated_client.post('/partner/customers/import', data={
        'file': csv_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_customer_import_empty_file(authenticated_client, app, db_session):
    """客户导入 - 空文件"""
    from werkzeug.datastructures import FileStorage

    csv_content = "code,name,contact_person,phone\n"
    csv_file = FileStorage(
        stream=io.BytesIO(csv_content.encode()),
        filename='customers.csv',
        content_type='text/csv'
    )

    resp = authenticated_client.post('/partner/customers/import', data={
        'file': csv_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_customer_import_duplicate_code(authenticated_client, app, db_session):
    """客户导入 - 重复编码"""
    create_customer(code='IMP_CUS_DUP_001')

    from werkzeug.datastructures import FileStorage

    csv_content = "code,name,contact_person,phone\nIMP_CUS_DUP_001,重复编码客户,李四,13900000001"
    csv_file = FileStorage(
        stream=io.BytesIO(csv_content.encode()),
        filename='customers.csv',
        content_type='text/csv'
    )

    resp = authenticated_client.post('/partner/customers/import', data={
        'file': csv_file,
    }, follow_redirects=True, content_type='multipart/form-data')
    assert resp.status_code == 200


def test_customer_import_template(authenticated_client):
    """客户导入模板下载"""
    resp = authenticated_client.get('/partner/customers/import/template')
    assert resp.status_code == 200
    assert len(resp.data) > 0


# ==================== 导出验证 ====================

def test_export_inventory(authenticated_client, app, db_session):
    """导出进销存报表"""
    create_product()
    resp = authenticated_client.get('/report/export/inventory')
    assert resp.status_code == 200
    assert len(resp.data) > 0


def test_export_sales_ranking(authenticated_client, app, db_session):
    """导出销售排行"""
    cus = create_customer()
    wh = create_warehouse()
    prod = create_product(stock_quantity=100)
    create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
        status='completed'
    )
    resp = authenticated_client.get('/report/export/sales-ranking')
    assert resp.status_code == 200


def test_export_customer_stats(authenticated_client, app, db_session):
    """导出客户统计"""
    cus = create_customer()
    wh = create_warehouse()
    prod = create_product(stock_quantity=100)
    create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
        status='completed'
    )
    resp = authenticated_client.get('/report/export/customer')
    assert resp.status_code == 200


def test_export_supplier_stats(authenticated_client, app, db_session):
    """导出供应商统计"""
    sup = create_supplier()
    wh = create_warehouse()
    prod = create_product()
    create_purchase_order(
        supplier_id=sup.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 50}],
        status='completed'
    )
    resp = authenticated_client.get('/report/export/supplier')
    assert resp.status_code == 200


def test_export_daily_report(authenticated_client, app, db_session):
    """导出日报"""
    cus = create_customer()
    wh = create_warehouse()
    prod = create_product(stock_quantity=100)
    create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
        status='completed'
    )
    resp = authenticated_client.get('/report/export/daily')
    assert resp.status_code == 200


def test_export_products(authenticated_client, app, db_session):
    """导出商品列表"""
    create_product()
    resp = authenticated_client.get('/report/export-products')
    assert resp.status_code == 200


def test_export_receipts(authenticated_client, app, db_session):
    """导出收款记录"""
    cus = create_customer()
    from app.models import Receipt
    receipt = Receipt(
        receipt_number='REC_EXPORT_001',
        customer_id=cus.id,
        amount=Decimal('1000'),
        receipt_date=date.today(),
        payment_method='cash'
    )
    db.session.add(receipt)
    db.session.commit()

    resp = authenticated_client.get('/finance/export-receipts')
    assert resp.status_code == 200


def test_export_payments(authenticated_client, app, db_session):
    """导出付款记录"""
    sup = create_supplier()
    from app.models import Payment
    payment = Payment(
        payment_number='PAY_EXPORT_001',
        supplier_id=sup.id,
        amount=Decimal('500'),
        payment_date=date.today(),
        payment_method='bank_transfer'
    )
    db.session.add(payment)
    db.session.commit()

    resp = authenticated_client.get('/finance/export-payments')
    assert resp.status_code == 200


def test_export_expenses(authenticated_client, app, db_session):
    """导出费用记录"""
    from app.models import Expense
    expense = Expense(
        expense_number='EXP_EXPORT_001',
        category='办公费',
        amount=Decimal('100'),
        expense_date=date.today()
    )
    db.session.add(expense)
    db.session.commit()

    resp = authenticated_client.get('/finance/export-expenses')
    assert resp.status_code == 200


def test_export_profit(authenticated_client, app, db_session):
    """导出利润分析"""
    cus = create_customer()
    wh = create_warehouse()
    prod = create_product(stock_quantity=100)
    create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
        status='completed'
    )
    resp = authenticated_client.get('/finance/export-profit-analysis')
    assert resp.status_code == 200


def test_export_customer_ar(authenticated_client, app, db_session):
    """导出客户应收"""
    cus = create_customer()
    resp = authenticated_client.get(f'/finance/export-customer-ar/{cus.id}')
    assert resp.status_code == 200


def test_export_supplier_ap(authenticated_client, app, db_session):
    """导出供应商应付"""
    sup = create_supplier()
    resp = authenticated_client.get(f'/finance/export-supplier-ap/{sup.id}')
    assert resp.status_code == 200


# ==================== API 验证 ====================

def test_api_products(authenticated_client, app, db_session):
    """商品 API"""
    create_product()
    resp = authenticated_client.get('/product/api/products')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_api_categories(authenticated_client, app, db_session):
    """分类 API"""
    create_category()
    resp = authenticated_client.get('/product/api/categories')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_api_low_stock(authenticated_client, app, db_session):
    """低库存 API"""
    create_product(stock_quantity=1)
    resp = authenticated_client.get('/inventory/api/low-stock')
    assert resp.status_code == 200


def test_api_system_info(authenticated_client):
    """系统信息 API"""
    resp = authenticated_client.get('/system/api/system-info')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert len(data) > 0


def test_api_recent_logs(authenticated_client):
    """最近日志 API"""
    resp = authenticated_client.get('/system/api/system/recent-logs')
    assert resp.status_code == 200


def test_api_sales_trend(authenticated_client):
    """销售趋势 API"""
    resp = authenticated_client.get('/api/sales-trend')
    assert resp.status_code == 200


def test_api_stock_overview(authenticated_client):
    """库存概览 API"""
    resp = authenticated_client.get('/api/stock-overview')
    assert resp.status_code == 200


def test_api_finance_summary(authenticated_client):
    """财务汇总 API"""
    resp = authenticated_client.get('/api/finance-summary')
    assert resp.status_code == 200


def test_api_financial_summary(authenticated_client):
    """财务汇总 API (finance)"""
    resp = authenticated_client.get('/finance/api/financial-summary')
    assert resp.status_code == 200


def test_api_customer_ar(authenticated_client, app, db_session):
    """客户应收 API"""
    cus = create_customer()
    resp = authenticated_client.get(f'/finance/api/customer-ar/{cus.id}')
    assert resp.status_code == 200


def test_api_supplier_ap(authenticated_client, app, db_session):
    """供应商应付 API"""
    sup = create_supplier()
    resp = authenticated_client.get(f'/finance/api/supplier-ap/{sup.id}')
    assert resp.status_code == 200


def test_api_purchase_order_items(authenticated_client, app, db_session):
    """采购订单明细 API"""
    sup = create_supplier()
    wh = create_warehouse()
    prod = create_product()
    order = create_purchase_order(
        supplier_id=sup.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 50}],
        status='confirmed'
    )
    resp = authenticated_client.get(f'/purchase/api/purchase-orders/{order.id}/items')
    assert resp.status_code == 200


def test_api_sales_order_items(authenticated_client, app, db_session):
    """销售订单明细 API"""
    cus = create_customer()
    wh = create_warehouse()
    prod = create_product()
    order = create_sales_order(
        customer_id=cus.id,
        warehouse_id=wh.id,
        items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
        status='confirmed'
    )
    resp = authenticated_client.get(f'/sales/api/sales-orders/{order.id}/items')
    assert resp.status_code == 200
