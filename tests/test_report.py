"""
报表模块测试 — 各类报表页面和导出
"""
import pytest


# ==================== 报表页面 ====================

def test_report_index(authenticated_client):
    """GET /report/ 返回 200"""
    resp = authenticated_client.get('/report/', follow_redirects=True)
    assert resp.status_code == 200


def test_inventory_report(authenticated_client):
    """GET /report/inventory-report 返回 200"""
    resp = authenticated_client.get('/report/inventory-report', follow_redirects=True)
    assert resp.status_code == 200


def test_sales_ranking(authenticated_client):
    """GET /report/sales-ranking 返回 200"""
    resp = authenticated_client.get('/report/sales-ranking', follow_redirects=True)
    assert resp.status_code == 200


def test_customer_statistics(authenticated_client):
    """GET /report/customer-statistics 返回 200"""
    resp = authenticated_client.get('/report/customer-statistics', follow_redirects=True)
    assert resp.status_code == 200


def test_supplier_statistics(authenticated_client):
    """GET /report/supplier-statistics 返回 200"""
    resp = authenticated_client.get('/report/supplier-statistics', follow_redirects=True)
    assert resp.status_code == 200


def test_daily_report(authenticated_client):
    """GET /report/daily-report 返回 200"""
    resp = authenticated_client.get('/report/daily-report', follow_redirects=True)
    assert resp.status_code == 200


# ==================== API ====================

def test_sales_trend_api(authenticated_client):
    """GET /report/api/sales-trend 返回 JSON"""
    resp = authenticated_client.get('/report/api/sales-trend')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, (list, dict))


# ==================== 导出 ====================

def test_export_inventory(authenticated_client):
    """GET /report/export/inventory 导出库存报表"""
    resp = authenticated_client.get('/report/export/inventory')
    assert resp.status_code == 200


def test_export_sales_ranking(authenticated_client):
    """GET /report/export/sales-ranking 导出销售排行"""
    resp = authenticated_client.get('/report/export/sales-ranking')
    assert resp.status_code == 200


def test_export_customer(authenticated_client):
    """GET /report/export/customer 导出客户统计"""
    resp = authenticated_client.get('/report/export/customer')
    assert resp.status_code == 200


def test_export_supplier(authenticated_client):
    """GET /report/export/supplier 导出供应商统计"""
    resp = authenticated_client.get('/report/export/supplier')
    assert resp.status_code == 200


def test_export_products(authenticated_client):
    """GET /report/export-products 导出商品报表"""
    resp = authenticated_client.get('/report/export-products')
    assert resp.status_code == 200


def test_export_daily(authenticated_client):
    """GET /report/export/daily 导出日报"""
    resp = authenticated_client.get('/report/export/daily')
    assert resp.status_code == 200


# ==================== 边界 ====================

def test_unauthenticated_redirect(client):
    """未登录访问报表首页重定向"""
    resp = client.get('/report/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers.get('Location', '')
