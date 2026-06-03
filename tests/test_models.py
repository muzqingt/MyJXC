"""
模型单元测试 — User, Product, Category, Supplier, Customer, Warehouse
"""
import pytest
from decimal import Decimal

from app import db
from app.models import User, Product, Category, Supplier, Customer, Warehouse
from app.constants import OrderStatus, ChangeType, PaymentMethod, UserRole
from tests.factories import (
    create_user, create_product, create_category,
    create_supplier, create_customer, create_warehouse,
)


# ==================== User 模型 ====================

def test_user_password_hash(app, db_session):
    """密码哈希和验证"""
    user = create_user(username='pwd_test', password='secret123')
    assert user.check_password('secret123') is True
    assert user.check_password('wrong') is False


def test_user_is_authenticated(app, db_session):
    """is_authenticated 属性"""
    user = create_user(username='auth_test')
    assert user.is_authenticated is True


def test_user_default_role(app, db_session):
    """默认角色为 user"""
    user = create_user(username='role_test')
    assert user.role == 'user'


def test_user_admin_role(app, db_session):
    """管理员角色"""
    user = create_user(username='admin_test', role='admin')
    assert user.role == 'admin'


def test_user_repr(app, db_session):
    """__repr__ 方法"""
    user = create_user(username='repr_test')
    assert 'repr_test' in repr(user)


# ==================== Product 模型 ====================

def test_product_creation(app, db_session):
    """创建商品"""
    category = create_category(name='测试分类')
    product = create_product(
        code='MDL_P01', name='模型测试商品',
        category_id=category.id, sale_price=100, cost_price=50,
    )
    assert product.id is not None
    assert product.code == 'MDL_P01'
    assert product.sale_price == Decimal('100')
    assert product.purchase_price == Decimal('50')


def test_product_stock_default(app, db_session):
    """默认库存为 0"""
    product = create_product(code='MDL_P02', name='库存测试')
    assert product.stock_quantity == Decimal('0')


def test_product_category_relationship(app, db_session):
    """商品-分类关系"""
    category = create_category(name='关系分类')
    product = create_product(code='MDL_P03', name='关系商品', category_id=category.id)
    assert product.category.name == '关系分类'


def test_product_repr(app, db_session):
    """__repr__ 方法"""
    product = create_product(code='MDL_P04', name='repr商品')
    assert 'MDL_P04' in repr(product)


# ==================== Category 模型 ====================

def test_category_creation(app, db_session):
    """创建分类"""
    category = create_category(name='电子产品')
    assert category.id is not None
    assert category.name == '电子产品'


def test_category_parent_child(app, db_session):
    """父子分类关系"""
    parent = create_category(name='父分类')
    child = create_category(name='子分类', parent_id=parent.id)
    assert child.parent.name == '父分类'
    assert child in parent.children


def test_category_repr(app, db_session):
    """__repr__ 方法"""
    category = create_category(name='repr分类')
    assert 'repr分类' in repr(category)


# ==================== Supplier 模型 ====================

def test_supplier_creation(app, db_session):
    """创建供应商"""
    supplier = create_supplier(code='MDL_S01', name='模型供应商')
    assert supplier.id is not None
    assert supplier.code == 'MDL_S01'


def test_supplier_balance_default(app, db_session):
    """默认应付余额为 0"""
    supplier = create_supplier(code='MDL_S02', name='余额供应商')
    assert supplier.payable_balance == Decimal('0')


def test_supplier_repr(app, db_session):
    """__repr__ 方法"""
    supplier = create_supplier(code='MDL_S03', name='repr供应商')
    assert 'MDL_S03' in repr(supplier)


# ==================== Customer 模型 ====================

def test_customer_creation(app, db_session):
    """创建客户"""
    customer = create_customer(code='MDL_C01', name='模型客户')
    assert customer.id is not None
    assert customer.code == 'MDL_C01'


def test_customer_balance_default(app, db_session):
    """默认应收余额为 0"""
    customer = create_customer(code='MDL_C02', name='余额客户')
    assert customer.receivable_balance == Decimal('0')


def test_customer_repr(app, db_session):
    """__repr__ 方法"""
    customer = create_customer(code='MDL_C03', name='repr客户')
    assert 'MDL_C03' in repr(customer)


# ==================== Warehouse 模型 ====================

def test_warehouse_creation(app, db_session):
    """创建仓库"""
    warehouse = create_warehouse(code='MDL_W01', name='模型仓库')
    assert warehouse.id is not None
    assert warehouse.code == 'MDL_W01'


def test_warehouse_repr(app, db_session):
    """__repr__ 方法"""
    warehouse = create_warehouse(code='MDL_W02', name='repr仓库')
    assert 'MDL_W02' in repr(warehouse)


# ==================== Constants 测试 ====================

def test_order_status_labels():
    """OrderStatus 中文标签"""
    assert OrderStatus.label('draft') == '草稿'
    assert OrderStatus.label('confirmed') == '已确认'
    assert OrderStatus.label('partial') == '部分完成'
    assert OrderStatus.label('completed') == '已完成'
    assert OrderStatus.label('unknown') == 'unknown'


def test_change_type_in_types():
    """入库类变动类型"""
    assert 'in' in ChangeType.IN_TYPES
    assert 'adjust_in' in ChangeType.IN_TYPES
    assert 'check_in' in ChangeType.IN_TYPES
    assert 'return_in' in ChangeType.IN_TYPES


def test_change_type_out_types():
    """出库类变动类型"""
    assert 'out' in ChangeType.OUT_TYPES
    assert 'adjust_out' in ChangeType.OUT_TYPES
    assert 'check_out' in ChangeType.OUT_TYPES
    assert 'return_out' in ChangeType.OUT_TYPES
    assert 'stock_transfer' in ChangeType.OUT_TYPES


def test_payment_method_labels():
    """PaymentMethod 中文标签"""
    assert PaymentMethod.label('cash') == '现金'
    assert PaymentMethod.label('bank_transfer') == '银行转账'
    assert PaymentMethod.label('wechat') == '微信'
    assert PaymentMethod.label('alipay') == '支付宝'
    assert PaymentMethod.label('unknown') == 'unknown'


def test_user_role_constants():
    """UserRole 常量"""
    assert UserRole.ADMIN == 'admin'
    assert UserRole.USER == 'user'
