"""
图表组件测试
"""
import pytest
from tests.helpers import get_page


def test_charts_js_exists(authenticated_client):
    """charts.js 文件可访问"""
    resp = authenticated_client.get('/static/js/charts.js')
    assert resp.status_code == 200


def test_charts_js_has_functions(authenticated_client):
    """charts.js 包含所有图表函数"""
    resp = authenticated_client.get('/static/js/charts.js')
    content = resp.data.decode('utf-8')

    # 检查所有图表函数
    assert 'renderSalesTrendChart' in content
    assert 'renderStockOverviewChart' in content
    assert 'renderFinanceSummaryChart' in content
    assert 'renderPieChart' in content
    assert 'renderDoughnutChart' in content
    assert 'createChart' in content


def test_chart_components_template(authenticated_client):
    """图表组件模板可渲染"""
    # 访问 Dashboard 页面，它使用了图表组件
    resp = authenticated_client.get('/', follow_redirects=True)
    assert resp.status_code == 200

    content = resp.data.decode('utf-8')
    assert 'chart.js' in content.lower() or 'Chart' in content


def test_dashboard_has_all_charts(authenticated_client):
    """Dashboard 包含所有图表"""
    resp = authenticated_client.get('/', follow_redirects=True)
    content = resp.data.decode('utf-8')

    assert 'salesTrendChart' in content
    assert 'stockOverviewChart' in content
    assert 'financeSummaryChart' in content
