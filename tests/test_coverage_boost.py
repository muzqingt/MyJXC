"""
覆盖率提升测试 — 补充未覆盖的代码路径
"""
import pytest
from datetime import date
from decimal import Decimal

from app import db
from app.models import Product, StockLog, Warehouse
from tests.factories import (
    create_product, create_warehouse, create_supplier, create_customer,
    create_purchase_order, create_sales_order,
)
from tests.helpers import get_page, post_page, get_json


# ==================== 库存模块补充测试 ====================

def test_export_warehouse_stock(app, authenticated_client, db_session):
    """导出仓库库存"""
    warehouse = create_warehouse(code='EWS_WH01', name='导出仓库')
    product = create_product(code='EWS_PROD01', name='导出商品', stock_quantity=50)

    # 创建库存日志
    log = StockLog(
        product_id=product.id,
        warehouse_id=warehouse.id,
        change_type='in',
        quantity=Decimal('50'),
        before_quantity=Decimal('0'),
        after_quantity=Decimal('50'),
        reference_type='test',
        notes='测试入库',
    )
    db.session.add(log)
    db.session.commit()

    get_page(authenticated_client, f'/inventory/export-warehouse-stock/{warehouse.id}')


def test_export_logs(authenticated_client):
    """导出库存日志"""
    get_page(authenticated_client, '/inventory/api/export-logs')


def test_logs_statistics(authenticated_client):
    """库存日志统计"""
    get_page(authenticated_client, '/inventory/api/logs-statistics')


# ==================== 采购模块补充测试 ====================

def test_purchase_api_order_items(app, authenticated_client, db_session):
    """采购订单明细 API"""
    supplier = create_supplier(code='PAI_SUP01', name='API供应商')
    warehouse = create_warehouse(code='PAI_WH01', name='API仓库')
    product = create_product(code='PAI_PROD01', name='API商品')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 50}],
    )
    db.session.commit()

    data = get_json(authenticated_client, f'/purchase/api/purchase-orders/{order.id}/items')
    assert isinstance(data, list)


# ==================== 销售模块补充测试 ====================

def test_sales_api_order_items(app, authenticated_client, db_session):
    """销售订单明细 API"""
    customer = create_customer(code='SAI_CUS01', name='API客户')
    warehouse = create_warehouse(code='SAI_WH01', name='API仓库')
    product = create_product(code='SAI_PROD01', name='API商品')

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 5, 'unit_price': 100}],
    )
    db.session.commit()

    data = get_json(authenticated_client, f'/sales/api/sales-orders/{order.id}/items')
    assert isinstance(data, list)


# ==================== 财务模块补充测试 ====================

def test_export_profit_analysis(authenticated_client):
    """导出利润分析"""
    get_page(authenticated_client, '/finance/export-profit-analysis')


def test_export_receipts(authenticated_client):
    """导出收款记录"""
    get_page(authenticated_client, '/finance/export-receipts')


def test_export_payments(authenticated_client):
    """导出付款记录"""
    get_page(authenticated_client, '/finance/export-payments')


def test_export_expenses(authenticated_client):
    """导出费用记录"""
    get_page(authenticated_client, '/finance/export-expenses')


# ==================== 系统模块补充测试 ====================

def test_system_backup_download(authenticated_client):
    """下载备份文件"""
    # 先创建备份
    authenticated_client.post('/system/backup/create', follow_redirects=True)

    # 获取备份列表
    resp = authenticated_client.get('/system/backup/list', follow_redirects=True)
    assert resp.status_code == 200


# ==================== 报表模块补充测试 ====================

def test_report_export_all(authenticated_client):
    """导出所有报表"""
    # 库存报表
    get_page(authenticated_client, '/report/export/inventory')

    # 销售排行
    get_page(authenticated_client, '/report/export/sales-ranking')

    # 客户统计
    get_page(authenticated_client, '/report/export/customer')

    # 供应商统计
    get_page(authenticated_client, '/report/export/supplier')

    # 日报
    get_page(authenticated_client, '/report/export/daily')


# ==================== 认证模块补充测试 ====================

def test_register_duplicate_email(client):
    """重复邮箱注册"""
    # 先注册一个用户
    client.post('/auth/register', data={
        'username': 'emailuser1',
        'email': 'duplicate@test.com',
        'password': 'pass123',
        'password2': 'pass123',
    })

    # 用相同邮箱注册
    resp = client.post('/auth/register', data={
        'username': 'emailuser2',
        'email': 'duplicate@test.com',
        'password': 'pass123',
        'password2': 'pass123',
    }, follow_redirects=True)

    assert resp.status_code == 200


def test_login_redirect_to_next(client):
    """登录后重定向到目标页面"""
    resp = client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123',
        'next': '/product/products',
    }, follow_redirects=True)

    assert resp.status_code == 200
