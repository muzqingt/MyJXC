"""
最终覆盖率提升 — 补充低覆盖率模块测试
"""
import pytest
from datetime import date
from decimal import Decimal

from app import db
from app.models import (
    PurchaseOrder, SalesOrder, Product, StockIn, StockOut,
    Supplier, Customer, Warehouse, Category,
)
from tests.factories import (
    create_product, create_warehouse, create_supplier, create_customer,
    create_purchase_order, create_sales_order, create_category,
)
from tests.helpers import get_page, post_page


# ==================== 采购模块补充 ====================

def test_purchase_order_view(app, authenticated_client, db_session):
    """查看采购订单详情"""
    supplier = create_supplier(code='CV_SUP01', name='查看供应商')
    warehouse = create_warehouse(code='CV_WH01', name='查看仓库')
    product = create_product(code='CV_PROD01', name='查看商品')

    order = create_purchase_order(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 10, 'unit_price': 50}],
    )
    db.session.commit()

    get_page(authenticated_client, f'/purchase/orders/{order.id}')


def test_purchase_stock_in_new_get(authenticated_client):
    """GET 新建入库单"""
    get_page(authenticated_client, '/purchase/stock-ins/new')


def test_purchase_returns_list(authenticated_client):
    """退货单列表"""
    get_page(authenticated_client, '/purchase/returns')


# ==================== 销售模块补充 ====================

def test_sales_order_view(app, authenticated_client, db_session):
    """查看销售订单详情"""
    customer = create_customer(code='CV_CUS01', name='查看客户')
    warehouse = create_warehouse(code='CV_WH02', name='查看仓库2')
    product = create_product(code='CV_PROD02', name='查看商品2')

    order = create_sales_order(
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        items=[{'product_id': product.id, 'quantity': 5, 'unit_price': 100}],
    )
    db.session.commit()

    get_page(authenticated_client, f'/sales/orders/{order.id}')


def test_sales_stock_out_new_get(authenticated_client):
    """GET 新建出库单"""
    get_page(authenticated_client, '/sales/stock-outs/new')


def test_sales_returns_list(authenticated_client):
    """退货单列表"""
    get_page(authenticated_client, '/sales/returns')


# ==================== 商品模块补充 ====================

def test_product_view(app, authenticated_client, db_session):
    """查看商品详情"""
    product = create_product(code='PV_PROD01', name='查看商品')
    get_page(authenticated_client, f'/product/products/{product.id}')


def test_product_edit_post(app, authenticated_client, db_session):
    """POST 编辑商品"""
    product = create_product(code='PE_PROD01', name='编辑商品')
    category = create_category(name='编辑分类')

    post_page(authenticated_client, f'/product/products/{product.id}/edit', {
        'code': 'PE_PROD01',
        'name': '新名称',
        'category_id': str(category.id),
        'unit': '个',
        'sale_price': '200.00',
        'purchase_price': '100.00',
    })


def test_category_edit_post(app, authenticated_client, db_session):
    """POST 编辑分类"""
    category = create_category(name='编辑测试分类')

    post_page(authenticated_client, f'/product/categories/{category.id}/edit', {
        'name': '新分类名',
        'description': '新描述',
    })


# ==================== 合作方模块补充 ====================

def test_supplier_view(app, authenticated_client, db_session):
    """查看供应商详情"""
    supplier = create_supplier(code='SV_SUP01', name='查看供应商')
    get_page(authenticated_client, f'/partner/suppliers/{supplier.id}/edit')


def test_customer_view(app, authenticated_client, db_session):
    """查看客户详情"""
    customer = create_customer(code='SV_CUS01', name='查看客户')
    get_page(authenticated_client, f'/partner/customers/{customer.id}/edit')


def test_warehouse_view(app, authenticated_client, db_session):
    """查看仓库详情"""
    warehouse = create_warehouse(code='SV_WH01', name='查看仓库')
    get_page(authenticated_client, f'/partner/warehouses/{warehouse.id}/edit')


# ==================== 系统模块补充 ====================

def test_system_user_edit_get(app, authenticated_client, db_session):
    """GET 编辑用户页面"""
    from tests.factories import create_user
    user = create_user(username='sue_user', password='pass123')
    db.session.commit()

    get_page(authenticated_client, f'/system/user/edit/{user.id}')


def test_system_settings_get(authenticated_client):
    """GET 系统设置页面"""
    get_page(authenticated_client, '/system/settings')


def test_system_logs_get(authenticated_client):
    """GET 系统日志页面"""
    get_page(authenticated_client, '/system/logs')


# ==================== 财务模块补充 ====================

def test_finance_index(authenticated_client):
    """GET 财务首页"""
    get_page(authenticated_client, '/finance/')


def test_finance_receipts(authenticated_client):
    """GET 收款列表"""
    get_page(authenticated_client, '/finance/receipts')


def test_finance_payments(authenticated_client):
    """GET 付款列表"""
    get_page(authenticated_client, '/finance/payments')


def test_finance_expenses(authenticated_client):
    """GET 费用列表"""
    get_page(authenticated_client, '/finance/expenses')


def test_finance_profit_analysis(authenticated_client):
    """GET 利润分析"""
    get_page(authenticated_client, '/finance/profit-analysis')


def test_finance_ar_ap(authenticated_client):
    """GET 应收应付"""
    get_page(authenticated_client, '/finance/ar-ap-search')


# ==================== 报表模块补充 ====================

def test_report_sales_ranking(authenticated_client):
    """GET 销售排行"""
    get_page(authenticated_client, '/report/sales-ranking')


def test_report_customer_statistics(authenticated_client):
    """GET 客户统计"""
    get_page(authenticated_client, '/report/customer-statistics')


def test_report_supplier_statistics(authenticated_client):
    """GET 供应商统计"""
    get_page(authenticated_client, '/report/supplier-statistics')


def test_report_daily(authenticated_client):
    """GET 日报"""
    get_page(authenticated_client, '/report/daily-report')
