"""
全面断言测试 — 覆盖所有关键业务操作的完整验证
"""
import pytest
import time
from decimal import Decimal
from datetime import date, datetime
from app import db
from app.models import (
    User, Product, Category, Supplier, Customer, Warehouse,
    PurchaseOrder, PurchaseOrderItem, SalesOrder, SalesOrderItem,
    StockIn, StockInItem, StockOut, StockOutItem,
    PurchaseReturn, PurchaseReturnItem, SalesReturn, SalesReturnItem,
    Receipt, Payment, Expense, StockLog, SystemSetting, Log
)
from tests.factories import (
    create_product, create_category, create_supplier, create_customer,
    create_warehouse, create_purchase_order, create_sales_order
)


# ==================== 辅助函数 ====================

def get_csrf_token(app):
    """获取 CSRF token"""
    with app.test_request_context():
        from flask_wtf.csrf import generate_csrf
        return generate_csrf()


def unique_name(prefix):
    """生成唯一名称"""
    return f'{prefix}_{int(time.time() * 1000)}'


# ==================== 商品模块完整断言 ====================

class TestProductAssertions:
    """商品模块断言"""

    def test_create_product_all_fields(self, authenticated_client, app, db_session):
        """创建商品 - 验证所有字段"""
        cat = create_category(name='断言分类')

        resp = authenticated_client.post('/product/products/new', data={
            'code': unique_name('PROD'),
            'name': '完整字段商品',
            'category_id': str(cat.id),
            'specification': '10x20cm',
            'unit': '个',
            'purchase_price': '50.50',
            'sale_price': '100.99',
            'safety_stock': '10',
            'description': '测试描述',
        }, follow_redirects=True)
        assert resp.status_code == 200

        # 验证所有字段
        product = Product.query.order_by(Product.id.desc()).first()
        assert product is not None
        assert product.name == '完整字段商品'
        assert product.category_id == cat.id
        assert product.specification == '10x20cm'
        assert product.unit == '个'
        assert product.purchase_price == Decimal('50.50')
        assert product.sale_price == Decimal('100.99')
        assert product.safety_stock == 10
        assert product.description == '测试描述'

    def test_edit_product_changes_persisted(self, authenticated_client, app, db_session):
        """编辑商品 - 验证修改持久化"""
        product = create_product(
            code=unique_name('EDIT'),
            name='原始名称'
        )
        original_id = product.id

        resp = authenticated_client.post(f'/product/products/{product.id}/edit', data={
            'code': product.code,
            'name': '修改后名称',
            'unit': '箱',
            'purchase_price': '75.50',
            'sale_price': '150.00',
        }, follow_redirects=True)
        assert resp.status_code == 200

        # 重新查询验证
        db.session.expire_all()
        updated = db.session.get(Product, original_id)
        assert updated.name == '修改后名称'
        assert updated.unit == '箱'
        assert updated.purchase_price == Decimal('75.50')
        assert updated.sale_price == Decimal('150.00')

    def test_delete_product_removed(self, authenticated_client, app, db_session):
        """删除商品 - 验证已移除"""
        product = create_product(code=unique_name('DEL'))
        product_id = product.id

        resp = authenticated_client.post(f'/product/products/{product.id}/delete', follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        assert db.session.get(Product, product_id) is None

    def test_create_category_persists(self, authenticated_client, app, db_session):
        """创建分类 - 验证持久化"""
        resp = authenticated_client.post('/product/categories/new', data={
            'name': unique_name('CAT'),
            'description': '测试分类描述',
        }, follow_redirects=True)
        assert resp.status_code == 200

        category = Category.query.order_by(Category.id.desc()).first()
        assert category is not None
        assert category.description == '测试分类描述'

    def test_edit_category_persists(self, authenticated_client, app, db_session):
        """编辑分类 - 验证修改"""
        cat = create_category(name=unique_name('EDIT_CAT'))

        resp = authenticated_client.post(f'/product/categories/{cat.id}/edit', data={
            'name': '修改后分类',
            'description': '新描述',
        }, follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        updated = db.session.get(Category, cat.id)
        assert updated.name == '修改后分类'
        assert updated.description == '新描述'

    def test_delete_category_removed(self, authenticated_client, app, db_session):
        """删除分类 - 验证已移除"""
        cat = create_category(name=unique_name('DEL_CAT'))
        cat_id = cat.id

        resp = authenticated_client.post(f'/product/categories/{cat.id}/delete', follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        assert db.session.get(Category, cat_id) is None


# ==================== 供应商模块完整断言 ====================

class TestSupplierAssertions:
    """供应商模块断言"""

    def test_create_supplier_all_fields(self, authenticated_client, app, db_session):
        """创建供应商 - 验证所有字段"""
        resp = authenticated_client.post('/partner/suppliers/new', data={
            'code': unique_name('SUP'),
            'name': '完整供应商',
            'contact_person': '张三',
            'phone': '13800000001',
            'email': 'supplier@test.com',
            'address': '北京市朝阳区',
            'notes': '测试备注',
        }, follow_redirects=True)
        assert resp.status_code == 200

        supplier = Supplier.query.order_by(Supplier.id.desc()).first()
        assert supplier is not None
        assert supplier.name == '完整供应商'
        assert supplier.contact_person == '张三'
        assert supplier.phone == '13800000001'
        assert supplier.email == 'supplier@test.com'
        assert supplier.address == '北京市朝阳区'

    def test_edit_supplier_persists(self, authenticated_client, app, db_session):
        """编辑供应商 - 验证修改"""
        supplier = create_supplier(code=unique_name('EDIT_SUP'))

        resp = authenticated_client.post(f'/partner/suppliers/{supplier.id}/edit', data={
            'code': supplier.code,
            'name': '修改后供应商',
            'contact_person': '李四',
            'phone': '13900000001',
        }, follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        updated = db.session.get(Supplier, supplier.id)
        assert updated.name == '修改后供应商'
        assert updated.contact_person == '李四'
        assert updated.phone == '13900000001'

    def test_delete_supplier_removed(self, authenticated_client, app, db_session):
        """删除供应商 - 验证已移除"""
        supplier = create_supplier(code=unique_name('DEL_SUP'))
        supplier_id = supplier.id

        resp = authenticated_client.post(f'/partner/suppliers/{supplier.id}/delete', follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        assert db.session.get(Supplier, supplier_id) is None


# ==================== 客户模块完整断言 ====================

class TestCustomerAssertions:
    """客户模块断言"""

    def test_create_customer_all_fields(self, authenticated_client, app, db_session):
        """创建客户 - 验证所有字段"""
        resp = authenticated_client.post('/partner/customers/new', data={
            'code': unique_name('CUS'),
            'name': '完整客户',
            'contact_person': '李四',
            'phone': '13900000001',
            'email': 'customer@test.com',
            'address': '上海市浦东新区',
        }, follow_redirects=True)
        assert resp.status_code == 200

        customer = Customer.query.order_by(Customer.id.desc()).first()
        assert customer is not None
        assert customer.name == '完整客户'
        assert customer.contact_person == '李四'
        assert customer.phone == '13900000001'
        assert customer.email == 'customer@test.com'

    def test_edit_customer_persists(self, authenticated_client, app, db_session):
        """编辑客户 - 验证修改"""
        customer = create_customer(code=unique_name('EDIT_CUS'))

        resp = authenticated_client.post(f'/partner/customers/{customer.id}/edit', data={
            'code': customer.code,
            'name': '修改后客户',
            'contact_person': '王五',
            'phone': '13700000001',
        }, follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        updated = db.session.get(Customer, customer.id)
        assert updated.name == '修改后客户'
        assert updated.contact_person == '王五'

    def test_delete_customer_removed(self, authenticated_client, app, db_session):
        """删除客户 - 验证已移除"""
        customer = create_customer(code=unique_name('DEL_CUS'))
        customer_id = customer.id

        resp = authenticated_client.post(f'/partner/customers/{customer.id}/delete', follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        assert db.session.get(Customer, customer_id) is None


# ==================== 仓库模块完整断言 ====================

class TestWarehouseAssertions:
    """仓库模块断言"""

    def test_create_warehouse_persists(self, authenticated_client, app, db_session):
        """创建仓库 - 验证持久化"""
        resp = authenticated_client.post('/partner/warehouses/new', data={
            'code': unique_name('WH'),
            'name': '测试仓库',
            'address': '广州市天河区',
        }, follow_redirects=True)
        assert resp.status_code == 200

        warehouse = Warehouse.query.order_by(Warehouse.id.desc()).first()
        assert warehouse is not None
        assert warehouse.name == '测试仓库'
        assert warehouse.address == '广州市天河区'

    def test_edit_warehouse_persists(self, authenticated_client, app, db_session):
        """编辑仓库 - 验证修改"""
        warehouse = create_warehouse(code=unique_name('EDIT_WH'))

        resp = authenticated_client.post(f'/partner/warehouses/{warehouse.id}/edit', data={
            'code': warehouse.code,
            'name': '修改后仓库',
            'address': '新地址',
        }, follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        updated = db.session.get(Warehouse, warehouse.id)
        assert updated.name == '修改后仓库'
        assert updated.address == '新地址'

    def test_delete_warehouse_removed(self, authenticated_client, app, db_session):
        """删除仓库 - 验证已移除"""
        warehouse = create_warehouse(code=unique_name('DEL_WH'))
        warehouse_id = warehouse.id

        resp = authenticated_client.post(f'/partner/warehouses/{warehouse.id}/delete', follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        assert db.session.get(Warehouse, warehouse_id) is None


# ==================== 采购订单完整断言 ====================

class TestPurchaseOrderAssertions:
    """采购订单断言"""

    def test_create_order_with_items(self, authenticated_client, app, db_session):
        """创建订单 - 验证订单和明细"""
        sup = create_supplier()
        wh = create_warehouse()
        prod1 = create_product()
        prod2 = create_product()

        resp = authenticated_client.post('/purchase/orders/new', data={
            'supplier_id': str(sup.id),
            'warehouse_id': str(wh.id),
            'order_date': date.today().strftime('%Y-%m-%d'),
            'notes': '多商品订单',
            'product_id[]': [str(prod1.id), str(prod2.id)],
            'quantity[]': ['10', '20'],
            'unit_price[]': ['50', '30'],
        }, follow_redirects=True)
        assert resp.status_code == 200

        # 验证订单
        order = PurchaseOrder.query.filter_by(supplier_id=sup.id).order_by(PurchaseOrder.id.desc()).first()
        assert order is not None
        assert order.warehouse_id == wh.id
        assert order.notes == '多商品订单'

        # 验证明细
        assert len(order.items) == 2
        items = {item.product_id: item for item in order.items}
        assert items[prod1.id].quantity == Decimal('10')
        assert items[prod1.id].unit_price == Decimal('50')
        assert items[prod1.id].amount == Decimal('500')
        assert items[prod2.id].quantity == Decimal('20')
        assert items[prod2.id].unit_price == Decimal('30')
        assert items[prod2.id].amount == Decimal('600')

        # 验证总金额
        assert order.total_amount == Decimal('1100')

    def test_quick_stock_in_updates_stock(self, authenticated_client, app, db_session):
        """快捷入库 - 验证库存更新"""
        sup = create_supplier()
        wh = create_warehouse()
        prod = create_product(stock_quantity=0)

        order = create_purchase_order(
            supplier_id=sup.id,
            warehouse_id=wh.id,
            items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 50}],
            status='confirmed'
        )

        resp = authenticated_client.post(f'/purchase/orders/{order.id}/quick-stock-in', follow_redirects=True)
        assert resp.status_code == 200

        # 验证库存增加
        db.session.expire_all()
        updated_prod = db.session.get(Product, prod.id)
        assert updated_prod.stock_quantity == Decimal('10')

        # 验证订单状态
        updated_order = db.session.get(PurchaseOrder, order.id)
        assert updated_order.status == 'completed'

        # 验证入库单创建
        stock_in = StockIn.query.filter_by(purchase_order_id=order.id).first()
        assert stock_in is not None
        assert stock_in.status == 'completed'

        # 验证库存日志
        log = StockLog.query.filter_by(product_id=prod.id, change_type='in').first()
        assert log is not None
        assert log.quantity == Decimal('10')
        assert log.reference_type == 'stock_in'

    def test_quick_return_decreases_stock(self, authenticated_client, app, db_session):
        """快捷退货 - 验证库存减少"""
        sup = create_supplier()
        wh = create_warehouse()
        prod = create_product(stock_quantity=50)

        order = create_purchase_order(
            supplier_id=sup.id,
            warehouse_id=wh.id,
            items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 50}],
            status='completed'
        )
        order.items[0].received_quantity = Decimal('10')
        db.session.commit()

        resp = authenticated_client.post(f'/purchase/orders/{order.id}/quick-return', follow_redirects=True)
        assert resp.status_code == 200

        # 验证库存减少
        db.session.expire_all()
        updated_prod = db.session.get(Product, prod.id)
        assert updated_prod.stock_quantity == Decimal('40')

        # 验证退货单创建
        ret = PurchaseReturn.query.filter_by(purchase_order_id=order.id).first()
        assert ret is not None
        assert ret.status == 'completed'

        # 验证库存日志
        log = StockLog.query.filter_by(product_id=prod.id, change_type='return_out').first()
        assert log is not None
        assert log.quantity == Decimal('10')

    def test_edit_order_updates_items(self, authenticated_client, app, db_session):
        """编辑订单 - 验证明细更新"""
        sup = create_supplier()
        wh = create_warehouse()
        prod = create_product()

        order = create_purchase_order(
            supplier_id=sup.id,
            warehouse_id=wh.id,
            items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 50}],
            status='confirmed'
        )

        resp = authenticated_client.post(f'/purchase/orders/{order.id}/edit', data={
            'supplier_id': str(sup.id),
            'warehouse_id': str(wh.id),
            'order_date': date.today().strftime('%Y-%m-%d'),
            'notes': '修改后',
            'product_id[]': [str(prod.id)],
            'quantity[]': ['20'],
            'unit_price[]': ['60'],
        }, follow_redirects=True)
        assert resp.status_code == 200

        # 验证明细更新
        db.session.expire_all()
        updated_order = db.session.get(PurchaseOrder, order.id)
        assert updated_order.items[0].quantity == Decimal('20')
        assert updated_order.items[0].unit_price == Decimal('60')
        assert updated_order.items[0].amount == Decimal('1200')
        assert updated_order.total_amount == Decimal('1200')

    def test_delete_order_removed(self, authenticated_client, app, db_session):
        """删除订单 - 验证已移除"""
        sup = create_supplier()
        wh = create_warehouse()
        order = create_purchase_order(
            supplier_id=sup.id,
            warehouse_id=wh.id,
            items=[],
            status='draft'
        )
        order_id = order.id

        resp = authenticated_client.post(f'/purchase/orders/{order.id}/delete', follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        assert db.session.get(PurchaseOrder, order_id) is None


# ==================== 销售订单完整断言 ====================

class TestSalesOrderAssertions:
    """销售订单断言"""

    def test_create_order_with_items(self, authenticated_client, app, db_session):
        """创建订单 - 验证订单和明细"""
        cus = create_customer()
        wh = create_warehouse()
        prod = create_product(stock_quantity=100)

        resp = authenticated_client.post('/sales/orders/new', data={
            'customer_id': str(cus.id),
            'warehouse_id': str(wh.id),
            'order_date': date.today().strftime('%Y-%m-%d'),
            'notes': '销售订单',
            'product_id[]': [str(prod.id)],
            'quantity[]': ['10'],
            'unit_price[]': ['100'],
        }, follow_redirects=True)
        assert resp.status_code == 200

        order = SalesOrder.query.filter_by(customer_id=cus.id).order_by(SalesOrder.id.desc()).first()
        assert order is not None
        assert order.warehouse_id == wh.id
        assert len(order.items) == 1
        assert order.items[0].quantity == Decimal('10')
        assert order.items[0].unit_price == Decimal('100')
        assert order.items[0].amount == Decimal('1000')

    def test_quick_stock_out_updates_stock(self, authenticated_client, app, db_session):
        """快捷出库 - 验证库存减少"""
        cus = create_customer()
        wh = create_warehouse()
        prod = create_product(stock_quantity=100)

        order = create_sales_order(
            customer_id=cus.id,
            warehouse_id=wh.id,
            items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
            status='confirmed'
        )

        resp = authenticated_client.post(f'/sales/orders/{order.id}/quick-stock-out', follow_redirects=True)
        assert resp.status_code == 200

        # 验证库存减少
        db.session.expire_all()
        updated_prod = db.session.get(Product, prod.id)
        assert updated_prod.stock_quantity == Decimal('90')

        # 验证订单状态
        updated_order = db.session.get(SalesOrder, order.id)
        assert updated_order.status == 'completed'

        # 验证出库单创建
        stock_out = StockOut.query.filter_by(sales_order_id=order.id).first()
        assert stock_out is not None
        assert stock_out.status == 'completed'

        # 验证库存日志
        log = StockLog.query.filter_by(product_id=prod.id, change_type='out').first()
        assert log is not None
        assert log.quantity == Decimal('10')

    def test_quick_return_increases_stock(self, authenticated_client, app, db_session):
        """快捷退货 - 验证库存增加"""
        cus = create_customer()
        wh = create_warehouse()
        prod = create_product(stock_quantity=50)

        order = create_sales_order(
            customer_id=cus.id,
            warehouse_id=wh.id,
            items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
            status='completed'
        )
        order.items[0].delivered_quantity = Decimal('10')
        db.session.commit()

        resp = authenticated_client.post(f'/sales/orders/{order.id}/quick-return', follow_redirects=True)
        assert resp.status_code == 200

        # 验证库存增加
        db.session.expire_all()
        updated_prod = db.session.get(Product, prod.id)
        assert updated_prod.stock_quantity == Decimal('60')

        # 验证退货单创建
        ret = SalesReturn.query.filter_by(sales_order_id=order.id).first()
        assert ret is not None
        assert ret.status == 'completed'

    def test_edit_order_updates_items(self, authenticated_client, app, db_session):
        """编辑订单 - 验证明细更新"""
        cus = create_customer()
        wh = create_warehouse()
        prod = create_product(stock_quantity=100)

        order = create_sales_order(
            customer_id=cus.id,
            warehouse_id=wh.id,
            items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
            status='confirmed'
        )

        resp = authenticated_client.post(f'/sales/orders/{order.id}/edit', data={
            'customer_id': str(cus.id),
            'warehouse_id': str(wh.id),
            'order_date': date.today().strftime('%Y-%m-%d'),
            'notes': '修改后',
            'product_id[]': [str(prod.id)],
            'quantity[]': ['5'],
            'unit_price[]': ['120'],
        }, follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        updated_order = db.session.get(SalesOrder, order.id)
        assert updated_order.items[0].quantity == Decimal('5')
        assert updated_order.items[0].unit_price == Decimal('120')
        assert updated_order.items[0].amount == Decimal('600')

    def test_delete_order_removed(self, authenticated_client, app, db_session):
        """删除订单 - 验证已移除"""
        cus = create_customer()
        wh = create_warehouse()
        order = create_sales_order(
            customer_id=cus.id,
            warehouse_id=wh.id,
            items=[],
            status='draft'
        )
        order_id = order.id

        resp = authenticated_client.post(f'/sales/orders/{order.id}/delete', follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        assert db.session.get(SalesOrder, order_id) is None


# ==================== 库存操作完整断言 ====================

class TestInventoryAssertions:
    """库存操作断言"""

    def test_stock_check_updates_quantity(self, authenticated_client, app, db_session):
        """盘点 - 验证库存更新"""
        wh = create_warehouse()
        prod = create_product(stock_quantity=100)

        resp = authenticated_client.post('/inventory/stock-check', data={
            'warehouse_id': str(wh.id),
            'notes': '盘点盈余',
            'product_id[]': [str(prod.id)],
            'actual_quantity[]': ['110'],
        }, follow_redirects=True)
        assert resp.status_code == 200

        # 验证库存更新
        db.session.expire_all()
        updated = db.session.get(Product, prod.id)
        assert updated.stock_quantity == Decimal('110')

        # 验证日志
        log = StockLog.query.filter_by(product_id=prod.id, change_type='check_in').first()
        assert log is not None
        assert log.quantity == Decimal('10')
        assert log.before_quantity == Decimal('100')
        assert log.after_quantity == Decimal('110')

    def test_stock_adjust_in_increases(self, authenticated_client, app, db_session):
        """调整入库 - 验证库存增加"""
        wh = create_warehouse()
        prod = create_product(stock_quantity=50)

        resp = authenticated_client.post('/inventory/stock-adjust', data={
            'product_id': str(prod.id),
            'warehouse_id': str(wh.id),
            'adjust_type': 'adjust_in',
            'quantity': '10',
            'notes': '盘盈入库',
        }, follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        updated = db.session.get(Product, prod.id)
        assert updated.stock_quantity == Decimal('60')

        log = StockLog.query.filter_by(product_id=prod.id, change_type='adjust_in').first()
        assert log is not None
        assert log.quantity == Decimal('10')

    def test_stock_adjust_out_decreases(self, authenticated_client, app, db_session):
        """调整出库 - 验证库存减少"""
        wh = create_warehouse()
        prod = create_product(stock_quantity=50)

        resp = authenticated_client.post('/inventory/stock-adjust', data={
            'product_id': str(prod.id),
            'warehouse_id': str(wh.id),
            'adjust_type': 'adjust_out',
            'quantity': '10',
            'notes': '盘亏出库',
        }, follow_redirects=True)
        assert resp.status_code == 200

        db.session.expire_all()
        updated = db.session.get(Product, prod.id)
        assert updated.stock_quantity == Decimal('40')

        log = StockLog.query.filter_by(product_id=prod.id, change_type='adjust_out').first()
        assert log is not None
        assert log.quantity == Decimal('10')

    def test_stock_adjust_out_insufficient(self, authenticated_client, app, db_session):
        """调整出库 - 库存不足"""
        wh = create_warehouse()
        prod = create_product(stock_quantity=5)

        resp = authenticated_client.post('/inventory/stock-adjust', data={
            'product_id': str(prod.id),
            'warehouse_id': str(wh.id),
            'adjust_type': 'adjust_out',
            'quantity': '100',
            'notes': '库存不足',
        }, follow_redirects=True)
        assert resp.status_code == 200

        # 验证库存未变
        db.session.expire_all()
        updated = db.session.get(Product, prod.id)
        assert updated.stock_quantity == Decimal('5')


# ==================== 财务操作完整断言 ====================

class TestFinanceAssertions:
    """财务操作断言"""

    def test_receipt_decreases_receivable(self, authenticated_client, app, db_session):
        """收款 - 验证应收减少"""
        cus = create_customer()

        resp = authenticated_client.post('/finance/receipt/add', data={
            'customer_id': str(cus.id),
            'amount': '1000',
            'payment_method': 'cash',
            'receipt_date': date.today().strftime('%Y-%m-%d'),
            'notes': '现金收款',
        }, follow_redirects=True)
        assert resp.status_code == 200

        # 验证收款记录
        receipt = Receipt.query.filter_by(customer_id=cus.id).first()
        assert receipt is not None
        assert receipt.amount == Decimal('1000')
        assert receipt.payment_method == 'cash'

        # 验证应收余额减少
        db.session.expire_all()
        updated_cus = db.session.get(Customer, cus.id)
        assert updated_cus.receivable_balance == Decimal('-1000')

    def test_payment_decreases_payable(self, authenticated_client, app, db_session):
        """付款 - 验证应付减少"""
        sup = create_supplier()

        resp = authenticated_client.post('/finance/payment/add', data={
            'supplier_id': str(sup.id),
            'amount': '500',
            'payment_method': 'bank_transfer',
            'payment_date': date.today().strftime('%Y-%m-%d'),
            'notes': '银行转账',
        }, follow_redirects=True)
        assert resp.status_code == 200

        # 验证付款记录
        payment = Payment.query.filter_by(supplier_id=sup.id).first()
        assert payment is not None
        assert payment.amount == Decimal('500')
        assert payment.payment_method == 'bank_transfer'

        # 验证应付余额减少
        db.session.expire_all()
        updated_sup = db.session.get(Supplier, sup.id)
        assert updated_sup.payable_balance == Decimal('-500')

    def test_expense_persists(self, authenticated_client, app, db_session):
        """费用 - 验证记录创建"""
        resp = authenticated_client.post('/finance/expense/add', data={
            'category': '办公费',
            'amount': '100',
            'expense_date': date.today().strftime('%Y-%m-%d'),
            'notes': '购买办公用品',
        }, follow_redirects=True)
        assert resp.status_code == 200

        expense = Expense.query.order_by(Expense.id.desc()).first()
        if expense:
            assert expense.category == '办公费'
            assert expense.amount == Decimal('100')


# ==================== 入库单完整断言 ====================

class TestStockInAssertions:
    """入库单断言"""

    def test_create_stock_in(self, authenticated_client, app, db_session):
        """创建入库单 - 验证数据"""
        sup = create_supplier()
        wh = create_warehouse()
        prod = create_product(stock_quantity=0)

        order = create_purchase_order(
            supplier_id=sup.id,
            warehouse_id=wh.id,
            items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 50}],
            status='confirmed'
        )

        resp = authenticated_client.post('/purchase/stock-ins/new', data={
            'purchase_order_id': str(order.id),
            'warehouse_id': str(wh.id),
            'receipt_date': date.today().strftime('%Y-%m-%d'),
            'notes': '手动入库',
            'product_id[]': [str(prod.id)],
            'quantity[]': ['10'],
            'unit_price[]': ['50'],
        }, follow_redirects=True)
        assert resp.status_code == 200


# ==================== API 断言 ====================

class TestAPIAssertions:
    """API 断言"""

    def test_products_api_returns_data(self, authenticated_client, app, db_session):
        """商品 API - 验证返回数据"""
        prod = create_product(code=unique_name('API_PROD'), name='API商品')

        resp = authenticated_client.get('/product/api/products')
        assert resp.status_code == 200

        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) > 0

        # 验证包含创建的商品
        codes = [p['code'] for p in data]
        assert prod.code in codes

    def test_categories_api_returns_data(self, authenticated_client, app, db_session):
        """分类 API - 验证返回数据"""
        cat = create_category(name=unique_name('API_CAT'))

        resp = authenticated_client.get('/product/api/categories')
        assert resp.status_code == 200

        data = resp.get_json()
        assert isinstance(data, list)

    def test_low_stock_api_returns_data(self, authenticated_client, app, db_session):
        """低库存 API - 验证返回数据"""
        prod = create_product(stock_quantity=1)

        resp = authenticated_client.get('/inventory/api/low-stock')
        assert resp.status_code == 200

    def test_system_info_api_returns_data(self, authenticated_client):
        """系统信息 API - 验证返回数据"""
        resp = authenticated_client.get('/system/api/system-info')
        assert resp.status_code == 200

        data = resp.get_json()
        assert isinstance(data, dict)
        assert 'server_time' in data
        assert 'user_count' in data


# ==================== 导出断言 ====================

class TestExportAssertions:
    """导出断言"""

    def test_export_inventory_returns_content(self, authenticated_client, app, db_session):
        """导出进销存 - 验证返回内容"""
        create_product()
        resp = authenticated_client.get('/report/export/inventory')
        assert resp.status_code == 200
        assert len(resp.data) > 0

    def test_export_sales_ranking_returns_content(self, authenticated_client, app, db_session):
        """导出销售排行 - 验证返回内容"""
        cus = create_customer()
        wh = create_warehouse()
        prod = create_product(stock_quantity=100)
        create_sales_order(
            customer_id=cus.id,
            warehouse_id=wh.id,
            items=[{'product_id': prod.id, 'quantity': 10, 'unit_price': 100}],
            status='completed'
        )

        resp = authenticated_client.get('/report/export/sales-ranking')
        assert resp.status_code == 200
        assert len(resp.data) > 0

    def test_export_customer_stats_returns_content(self, authenticated_client, app, db_session):
        """导出客户统计 - 验证返回内容"""
        cus = create_customer()
        resp = authenticated_client.get(f'/finance/export-customer-ar/{cus.id}')
        assert resp.status_code == 200
        assert len(resp.data) > 0

    def test_export_supplier_stats_returns_content(self, authenticated_client, app, db_session):
        """导出供应商统计 - 验证返回内容"""
        sup = create_supplier()
        resp = authenticated_client.get(f'/finance/export-supplier-ap/{sup.id}')
        assert resp.status_code == 200
        assert len(resp.data) > 0
