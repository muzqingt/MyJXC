"""
导出与交互测试
"""
import pytest
from tests.helpers import get_page, get_json


def test_api_sales_trend_with_days(authenticated_client):
    """销售趋势 API 支持天数参数"""
    data = get_json(authenticated_client, '/api/sales-trend?days=7')
    assert 'dates' in data
    assert len(data['dates']) == 7


def test_api_finance_summary_with_days(authenticated_client):
    """财务摘要 API 支持天数参数"""
    data = get_json(authenticated_client, '/api/finance-summary?days=14')
    assert 'dates' in data
    assert len(data['dates']) == 14


def test_dashboard_has_time_selector(authenticated_client):
    """Dashboard 包含时间选择器"""
    resp = authenticated_client.get('/', follow_redirects=True)
    content = resp.data.decode('utf-8')
    assert 'timeRange' in content
    assert 'autoRefresh' in content


def test_dashboard_has_export_button(authenticated_client):
    """Dashboard 包含导出按钮"""
    resp = authenticated_client.get('/', follow_redirects=True)
    content = resp.data.decode('utf-8')
    assert 'exportChartAsPNG' in content


def test_dashboard_has_refresh_button(authenticated_client):
    """Dashboard 包含刷新按钮"""
    resp = authenticated_client.get('/', follow_redirects=True)
    content = resp.data.decode('utf-8')
    assert 'refreshBtn' in content


def test_charts_js_has_export_function(authenticated_client):
    """charts.js 包含导出函数"""
    resp = authenticated_client.get('/static/js/charts.js')
    content = resp.data.decode('utf-8')
    assert 'exportChartAsPNG' in content
    assert 'ChartManager' in content
