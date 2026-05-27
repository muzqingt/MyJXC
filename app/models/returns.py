from datetime import datetime
from app import db


class PurchaseReturn(db.Model):
    """采购退货单 - 退货给供应商"""
    __tablename__ = 'purchase_returns'
    id = db.Column(db.Integer, primary_key=True)
    return_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    return_date = db.Column(db.Date, nullable=False, default=datetime.now)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default='pending')  # pending, completed
    handler = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    purchase_order = db.relationship('PurchaseOrder', backref='purchase_returns')
    warehouse = db.relationship('Warehouse', backref='purchase_returns')
    creator = db.relationship('User', backref='created_purchase_returns')
    items = db.relationship('PurchaseReturnItem', backref='purchase_return', cascade='all, delete-orphan')


class PurchaseReturnItem(db.Model):
    __tablename__ = 'purchase_return_items'
    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(db.Integer, db.ForeignKey('purchase_returns.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)

    product = db.relationship('Product', backref='purchase_return_items')


class SalesReturn(db.Model):
    """销售退货单 - 客户退货"""
    __tablename__ = 'sales_returns'
    id = db.Column(db.Integer, primary_key=True)
    return_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    return_date = db.Column(db.Date, nullable=False, default=datetime.now)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default='pending')  # pending, completed
    handler = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    sales_order = db.relationship('SalesOrder', backref='sales_returns')
    warehouse = db.relationship('Warehouse', backref='sales_returns')
    creator = db.relationship('User', backref='created_sales_returns')
    items = db.relationship('SalesReturnItem', backref='sales_return', cascade='all, delete-orphan')


class SalesReturnItem(db.Model):
    __tablename__ = 'sales_return_items'
    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(db.Integer, db.ForeignKey('sales_returns.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)

    product = db.relationship('Product', backref='sales_return_items')
