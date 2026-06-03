"""
测试专用 fixtures — 预创建的测试数据
"""
import pytest
from tests.factories import (
    create_user, create_category, create_product,
    create_supplier, create_customer, create_warehouse,
)


@pytest.fixture
def sample_user(app, db_session):
    """预创建的普通用户"""
    return create_user(username='testuser', password='test123', role='user')


@pytest.fixture
def sample_category(app, db_session):
    """预创建的商品分类"""
    return create_category(name='电子产品')


@pytest.fixture
def sample_product(app, db_session, sample_category):
    """预创建的商品（含分类）"""
    return create_product(
        code='TEST001',
        name='测试商品A',
        category_id=sample_category.id,
        sale_price='100.00',
        cost_price='50.00',
    )


@pytest.fixture
def sample_supplier(app, db_session):
    """预创建的供应商"""
    return create_supplier(
        code='SUP001',
        name='测试供应商A',
        contact_person='张三',
        phone='13800000001',
    )


@pytest.fixture
def sample_customer(app, db_session):
    """预创建的客户"""
    return create_customer(
        code='CUS001',
        name='测试客户A',
        contact_person='李四',
        phone='13900000001',
    )


@pytest.fixture
def sample_warehouse(app, db_session):
    """预创建的仓库"""
    return create_warehouse(
        code='WH001',
        name='测试仓库A',
        address='测试地址1号',
    )
