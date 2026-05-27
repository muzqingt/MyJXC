from datetime import datetime
from app import db


class SalesOrder(db.Model):
    """销售订单"""
    __tablename__ = 'sales_orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False, default=datetime.now)
    delivery_date = db.Column(db.Date)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default='confirmed')  # confirmed, partial, completed
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    customer = db.relationship('Customer', backref='sales_orders')
    warehouse = db.relationship('Warehouse', backref='sales_orders')
    creator = db.relationship('User', backref='created_sales_orders')
    items = db.relationship('SalesOrderItem', backref='order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<SalesOrder {self.order_number}>'


class SalesOrderItem(db.Model):
    """销售订单明细"""
    __tablename__ = 'sales_order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    delivered_quantity = db.Column(db.Numeric(10, 2), default=0)  # 已出库数量

    product = db.relationship('Product', backref='sales_order_items')

    def __repr__(self):
        return f'<SalesOrderItem {self.id}>'


class StockOut(db.Model):
    """出库单"""
    __tablename__ = 'stock_outs'
    id = db.Column(db.Integer, primary_key=True)
    delivery_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    delivery_date = db.Column(db.Date, nullable=False, default=datetime.now)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default='pending')  # pending, completed
    handler = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    sales_order = db.relationship('SalesOrder', backref='stock_outs')
    warehouse = db.relationship('Warehouse', backref='stock_outs')
    creator = db.relationship('User', backref='created_stock_outs')
    items = db.relationship('StockOutItem', backref='stock_out', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<StockOut {self.delivery_number}>'


class StockOutItem(db.Model):
    """出库单明细"""
    __tablename__ = 'stock_out_items'
    id = db.Column(db.Integer, primary_key=True)
    stock_out_id = db.Column(db.Integer, db.ForeignKey('stock_outs.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)

    product = db.relationship('Product', backref='stock_out_items')

    def __repr__(self):
        return f'<StockOutItem {self.id}>'
