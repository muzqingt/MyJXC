"""
报表模块测试 — 各类报表页面和导出
"""
import pytest
from tests.helpers import get_page, get_json, assert_redirects_to_login


# ==================== 报表页面 ====================

def test_report_index(authenticated_client):
    """GET /report/ 返回 200"""
    get_page(authenticated_client, '/report/')


def test_inventory_report(authenticated_client):
    """GET /report/inventory-report 返回 200"""
    get_page(authenticated_client, '/report/inventory-report')


def test_sales_ranking(authenticated_client):
    """GET /report/sales-ranking 返回 200"""
    get_page(authenticated_client, '/report/sales-ranking')


def test_customer_statistics(authenticated_client):
    """GET /report/customer-statistics 返回 200"""
    get_page(authenticated_client, '/report/customer-statistics')


def test_supplier_statistics(authenticated_client):
    """GET /report/supplier-statistics 返回 200"""
    get_page(authenticated_client, '/report/supplier-statistics')


def test_daily_report(authenticated_client):
    """GET /report/daily-report 返回 200"""
    get_page(authenticated_client, '/report/daily-report')


# ==================== API ====================

def test_sales_trend_api(authenticated_client):
    """GET /report/api/sales-trend 返回 JSON"""
    data = get_json(authenticated_client, '/report/api/sales-trend')
    assert isinstance(data, (list, dict))


# ==================== 导出 ====================

def test_export_inventory(authenticated_client):
    """GET /report/export/inventory 导出库存报表"""
    get_page(authenticated_client, '/report/export/inventory')


def test_export_sales_ranking(authenticated_client):
    """GET /report/export/sales-ranking 导出销售排行"""
    get_page(authenticated_client, '/report/export/sales-ranking')


def test_export_customer(authenticated_client):
    """GET /report/export/customer 导出客户统计"""
    get_page(authenticated_client, '/report/export/customer')


def test_export_supplier(authenticated_client):
    """GET /report/export/supplier 导出供应商统计"""
    get_page(authenticated_client, '/report/export/supplier')


def test_export_products(authenticated_client):
    """GET /report/export-products 导出商品报表"""
    get_page(authenticated_client, '/report/export-products')


def test_export_daily(authenticated_client):
    """GET /report/export/daily 导出日报"""
    get_page(authenticated_client, '/report/export/daily')


# ==================== 边界 ====================

def test_unauthenticated_redirect(client):
    """未登录访问报表首页重定向"""
    assert_redirects_to_login(client, '/report/')
