"""
测试工厂函数 — 快速创建测试数据
"""
import time
from decimal import Decimal
from datetime import datetime, date

from app import db
from app.utils import to_decimal


_ts_counter = 0


def _unique_suffix():
    """生成唯一后缀避免重复"""
    global _ts_counter
    _ts_counter += 1
    return f"{int(time.time())}{_ts_counter}"


def create_user(username=None, password='test123', role='user', email=None):
    """创建用户"""
    from app.models import User
    suffix = _unique_suffix()
    user = User(
        username=username or f'user_{suffix}',
        email=email or f'user_{suffix}@test.com',
        role=role,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


def create_category(name=None, parent_id=None, description=None):
    """创建商品分类"""
    from app.models import Category
    cat = Category(
        name=name or f'分类_{_unique_suffix()}',
        parent_id=parent_id,
        description=description,
    )
    db.session.add(cat)
    db.session.flush()
    return cat


def create_product(code=None, name=None, category_id=None, unit='个',
                   sale_price=Decimal('100.00'), cost_price=Decimal('50.00'),
                   stock_quantity=Decimal('0')):
    """创建商品"""
    from app.models import Product
    suffix = _unique_suffix()
    product = Product(
        code=code or f'SKU_{suffix}',
        name=name or f'测试商品_{suffix}',
        category_id=category_id,
        unit=unit,
        sale_price=to_decimal(sale_price),
        purchase_price=to_decimal(cost_price),
        stock_quantity=to_decimal(stock_quantity),
    )
    db.session.add(product)
    db.session.flush()
    return product


def create_supplier(code=None, name=None, contact_person=None, phone=None):
    """创建供应商"""
    from app.models import Supplier
    suffix = _unique_suffix()
    supplier = Supplier(
        code=code or f'SUP_{suffix}',
        name=name or f'供应商_{suffix}',
        contact_person=contact_person or '联系人',
        phone=phone or '13800000000',
    )
    db.session.add(supplier)
    db.session.flush()
    return supplier


def create_customer(code=None, name=None, contact_person=None, phone=None):
    """创建客户"""
    from app.models import Customer
    suffix = _unique_suffix()
    customer = Customer(
        code=code or f'CUS_{suffix}',
        name=name or f'客户_{suffix}',
        contact_person=contact_person or '联系人',
        phone=phone or '13900000000',
    )
    db.session.add(customer)
    db.session.flush()
    return customer


def create_warehouse(code=None, name=None, address=None):
    """创建仓库"""
    from app.models import Warehouse
    suffix = _unique_suffix()
    wh = Warehouse(
        code=code or f'WH_{suffix}',
        name=name or f'仓库_{suffix}',
        address=address or '测试地址',
    )
    db.session.add(wh)
    db.session.flush()
    return wh


def create_purchase_order(supplier_id, warehouse_id, created_by=None,
                          items=None, status='confirmed'):
    """创建采购订单

    items: list of dict，每个 dict 包含 product_id, quantity, unit_price
    """
    from app.models import PurchaseOrder, PurchaseOrderItem
    from app.utils import generate_order_number

    order = PurchaseOrder(
        order_number=generate_order_number('PO'),
        supplier_id=supplier_id,
        warehouse_id=warehouse_id,
        order_date=date.today(),
        status=status,
        created_by=created_by,
    )
    db.session.add(order)
    db.session.flush()

    total = Decimal('0')
    if items:
        for item_data in items:
            qty = to_decimal(item_data['quantity'])
            price = to_decimal(item_data['unit_price'])
            amount = qty * price
            item = PurchaseOrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                quantity=qty,
                unit_price=price,
                amount=amount,
            )
            db.session.add(item)
            total += amount

    order.total_amount = total
    db.session.flush()
    return order


def create_sales_order(customer_id, warehouse_id, created_by=None,
                       items=None, status='confirmed'):
    """创建销售订单

    items: list of dict，每个 dict 包含 product_id, quantity, unit_price
    """
    from app.models import SalesOrder, SalesOrderItem
    from app.utils import generate_order_number

    order = SalesOrder(
        order_number=generate_order_number('SO'),
        customer_id=customer_id,
        warehouse_id=warehouse_id,
        order_date=date.today(),
        status=status,
        created_by=created_by,
    )
    db.session.add(order)
    db.session.flush()

    total = Decimal('0')
    if items:
        for item_data in items:
            qty = to_decimal(item_data['quantity'])
            price = to_decimal(item_data['unit_price'])
            amount = qty * price
            item = SalesOrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                quantity=qty,
                unit_price=price,
                amount=amount,
            )
            db.session.add(item)
            total += amount

    order.total_amount = total
    db.session.flush()
    return order
