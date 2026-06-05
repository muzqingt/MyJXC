"""
深度覆盖测试 — 覆盖 purchase、sales、finance 的未测试路径
"""
from app import db
from app.models import (
    Product, Category, Supplier, Customer, Warehouse,
    PurchaseOrder, PurchaseOrderItem, SalesOrder, SalesOrderItem,
    StockIn, StockInItem, StockOut, StockOutItem,
    PurchaseReturn, PurchaseReturnItem, SalesReturn, SalesReturnItem,
    Receipt, Payment, Expense
)
from tests.factories import (
    create_product, create_category, create_supplier, create_customer,
    create_warehouse, create_purchase_order, create_sales_order
)
from datetime import date, datetime
from decimal import Decimal


# ==================== Purchase 深度测试 ====================

def test_purchase_order_edit(app, authenticated_client, db_session):
    """编辑采购订单"""
    supplier = create_supplier()
    warehouse = create_warehouse()
    product = create_product(stock_quantity=100)

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 50}],
        status='confirmed'
    )

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/edit', data={
        'supplier_id': str(supplier.id),
        'warehouse_id': str(warehouse.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '修改备注',
        'product_id[]': [str(product.id)],
        'quantity[]': ['20'],
        'unit_price[]': ['60'],
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_purchase_order_delete(app, authenticated_client, db_session):
    """删除采购订单"""
    supplier = create_supplier()
    warehouse = create_warehouse()
    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[],
        status='draft'
    )

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_purchase_stock_in(app, authenticated_client, db_session):
    """采购入库"""
    supplier = create_supplier()
    warehouse = create_warehouse()
    product = create_product(stock_quantity=0)

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 50}],
        status='confirmed'
    )

    # 使用快捷入库
    resp = authenticated_client.post(f'/purchase/orders/{order.id}/quick-stock-in', follow_redirects=True)
    assert resp.status_code == 200


def test_purchase_return(app, authenticated_client, db_session):
    """采购退货"""
    supplier = create_supplier()
    warehouse = create_warehouse()
    product = create_product(stock_quantity=50)

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 50}],
        status='completed'
    )
    order.items[0].received_quantity = Decimal('10')
    db.session.commit()

    resp = authenticated_client.post(f'/purchase/orders/{order.id}/quick-return', follow_redirects=True)
    assert resp.status_code == 200


def test_purchase_returns_list(authenticated_client):
    """采购退货列表"""
    resp = authenticated_client.get('/purchase/returns')
    assert resp.status_code == 200


def test_purchase_stock_in_list(authenticated_client):
    """入库单列表"""
    resp = authenticated_client.get('/purchase/stock-ins/new')
    assert resp.status_code == 200


# ==================== Sales 深度测试 ====================

def test_sales_order_edit(app, authenticated_client, db_session):
    """编辑销售订单"""
    customer = create_customer()
    warehouse = create_warehouse()
    product = create_product(stock_quantity=100)

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 100}],
        status='confirmed'
    )

    resp = authenticated_client.post(f'/sales/orders/{order.id}/edit', data={
        'customer_id': str(customer.id),
        'warehouse_id': str(warehouse.id),
        'order_date': date.today().strftime('%Y-%m-%d'),
        'notes': '修改备注',
        'product_id[]': [str(product.id)],
        'quantity[]': ['5'],
        'unit_price[]': ['120'],
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_sales_order_delete(app, authenticated_client, db_session):
    """删除销售订单"""
    customer = create_customer()
    warehouse = create_warehouse()
    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[],
        status='draft'
    )

    resp = authenticated_client.post(f'/sales/orders/{order.id}/delete', follow_redirects=True)
    assert resp.status_code == 200


def test_sales_stock_out(app, authenticated_client, db_session):
    """销售出库"""
    customer = create_customer()
    warehouse = create_warehouse()
    product = create_product(stock_quantity=100)

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 100}],
        status='confirmed'
    )

    # 使用快捷出库
    resp = authenticated_client.post(f'/sales/orders/{order.id}/quick-stock-out', follow_redirects=True)
    assert resp.status_code == 200


def test_sales_return(app, authenticated_client, db_session):
    """销售退货"""
    customer = create_customer()
    warehouse = create_warehouse()
    product = create_product(stock_quantity=50)

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 100}],
        status='completed'
    )
    order.items[0].delivered_quantity = Decimal('10')
    db.session.commit()

    resp = authenticated_client.post(f'/sales/orders/{order.id}/quick-return', follow_redirects=True)
    assert resp.status_code == 200


def test_sales_returns_list(authenticated_client):
    """销售退货列表"""
    resp = authenticated_client.get('/sales/returns')
    assert resp.status_code == 200


def test_sales_stock_out_list(authenticated_client):
    """出库单列表"""
    resp = authenticated_client.get('/sales/stock-outs/new')
    assert resp.status_code == 200


# ==================== Finance 深度测试 ====================

def test_add_receipt(app, authenticated_client, db_session):
    """添加收款记录"""
    customer = create_customer()

    resp = authenticated_client.post('/finance/receipt/add', data={
        'customer_id': str(customer.id),
        'amount': '1000',
        'payment_method': 'cash',
        'receipt_date': date.today().strftime('%Y-%m-%d'),
        'notes': '测试收款',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_add_payment(app, authenticated_client, db_session):
    """添加付款记录"""
    supplier = create_supplier()

    resp = authenticated_client.post('/finance/payment/add', data={
        'supplier_id': str(supplier.id),
        'amount': '500',
        'payment_method': 'bank_transfer',
        'payment_date': date.today().strftime('%Y-%m-%d'),
        'notes': '测试付款',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_add_expense(authenticated_client):
    """添加费用记录"""
    resp = authenticated_client.post('/finance/expense/add', data={
        'category': '办公费',
        'amount': '100',
        'expense_date': date.today().strftime('%Y-%m-%d'),
        'notes': '测试费用',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_receipts_list(authenticated_client):
    """收款列表"""
    resp = authenticated_client.get('/finance/receipts')
    assert resp.status_code == 200


def test_payments_list(authenticated_client):
    """付款列表"""
    resp = authenticated_client.get('/finance/payments')
    assert resp.status_code == 200


def test_expenses_list(authenticated_client):
    """费用列表"""
    resp = authenticated_client.get('/finance/expenses')
    assert resp.status_code == 200


def test_profit_analysis(authenticated_client):
    """利润分析"""
    resp = authenticated_client.get('/finance/profit-analysis')
    assert resp.status_code == 200


def test_ar_ap_search(authenticated_client):
    """应收应付查询"""
    resp = authenticated_client.get('/finance/ar-ap-search')
    assert resp.status_code == 200


# ==================== Inventory 深度测试 ====================

def test_stock_check_page(authenticated_client):
    """库存盘点页面"""
    resp = authenticated_client.get('/inventory/stock-check')
    assert resp.status_code == 200


def test_stock_transfer_page(authenticated_client):
    """库存调拨页面"""
    resp = authenticated_client.get('/inventory/stock-transfer')
    assert resp.status_code == 200


def test_stock_adjust_page(authenticated_client):
    """库存调整页面"""
    resp = authenticated_client.get('/inventory/stock-adjust')
    assert resp.status_code == 200


def test_stock_logs(authenticated_client):
    """库存日志"""
    resp = authenticated_client.get('/inventory/logs')
    assert resp.status_code == 200


def test_low_stock_api(authenticated_client):
    """低库存API"""
    resp = authenticated_client.get('/inventory/api/low-stock')
    assert resp.status_code == 200


# ==================== Report 深度测试 ====================

def test_inventory_report(authenticated_client):
    """进销存报表"""
    resp = authenticated_client.get('/report/inventory-report')
    assert resp.status_code == 200


def test_sales_ranking(authenticated_client):
    """销售排行"""
    resp = authenticated_client.get('/report/sales-ranking')
    assert resp.status_code == 200


def test_customer_stats(authenticated_client):
    """客户统计"""
    resp = authenticated_client.get('/report/customer-statistics')
    assert resp.status_code == 200


def test_supplier_stats(authenticated_client):
    """供应商统计"""
    resp = authenticated_client.get('/report/supplier-statistics')
    assert resp.status_code == 200


def test_daily_report(authenticated_client):
    """日报"""
    resp = authenticated_client.get('/report/daily-report')
    assert resp.status_code == 200
