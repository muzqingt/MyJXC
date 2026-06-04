"""
Dashboard 测试 — 图表 API 和页面
"""
import pytest
from tests.helpers import get_page, get_json


# ==================== Dashboard 页面 ====================

def test_dashboard_page(authenticated_client):
    """Dashboard 页面可访问"""
    get_page(authenticated_client, '/')


def test_dashboard_has_charts(authenticated_client):
    """Dashboard 包含图表容器"""
    resp = authenticated_client.get('/', follow_redirects=True)
    content = resp.data.decode('utf-8', errors='replace')
    assert 'salesTrendChart' in content
    assert 'stockOverviewChart' in content
    assert 'financeSummaryChart' in content


# ==================== 图表 API ====================

def test_api_sales_trend(authenticated_client):
    """销售趋势 API 返回 JSON"""
    data = get_json(authenticated_client, '/api/sales-trend')
    assert 'dates' in data
    assert 'amounts' in data
    assert isinstance(data['dates'], list)
    assert isinstance(data['amounts'], list)


def test_api_stock_overview(authenticated_client):
    """库存分布 API 返回 JSON"""
    data = get_json(authenticated_client, '/api/stock-overview')
    assert isinstance(data, list)


def test_api_finance_summary(authenticated_client):
    """财务摘要 API 返回 JSON"""
    data = get_json(authenticated_client, '/api/finance-summary')
    assert 'dates' in data
    assert 'income' in data
    assert 'expense' in data
    assert isinstance(data['dates'], list)
    assert isinstance(data['income'], list)
    assert isinstance(data['expense'], list)


def test_api_sales_trend_unauthenticated(client):
    """未登录访问销售趋势 API 重定向"""
    resp = client.get('/api/sales-trend', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers.get('Location', '')
