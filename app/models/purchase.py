from datetime import datetime
from app import db


class PurchaseOrder(db.Model):
    """采购订单"""
    __tablename__ = 'purchase_orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False, default=datetime.now)
    expected_date = db.Column(db.Date)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default='confirmed')  # confirmed, partial, completed
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    supplier = db.relationship('Supplier', backref='purchase_orders')
    warehouse = db.relationship('Warehouse', backref='purchase_orders')
    creator = db.relationship('User', backref='created_purchase_orders')
    items = db.relationship('PurchaseOrderItem', backref='order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PurchaseOrder {self.order_number}>'


class PurchaseOrderItem(db.Model):
    """采购订单明细"""
    __tablename__ = 'purchase_order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    received_quantity = db.Column(db.Numeric(10, 2), default=0)  # 已入库数量

    product = db.relationship('Product', backref='purchase_order_items')

    def __repr__(self):
        return f'<PurchaseOrderItem {self.id}>'


class StockIn(db.Model):
    """入库单"""
    __tablename__ = 'stock_ins'
    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    receipt_date = db.Column(db.Date, nullable=False, default=datetime.now)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default='pending')  # pending, completed
    handler = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    purchase_order = db.relationship('PurchaseOrder', backref='stock_ins')
    warehouse = db.relationship('Warehouse', backref='stock_ins')
    creator = db.relationship('User', backref='created_stock_ins')
    items = db.relationship('StockInItem', backref='stock_in', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<StockIn {self.receipt_number}>'


class StockInItem(db.Model):
    """入库单明细"""
    __tablename__ = 'stock_in_items'
    id = db.Column(db.Integer, primary_key=True)
    stock_in_id = db.Column(db.Integer, db.ForeignKey('stock_ins.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)

    product = db.relationship('Product', backref='stock_in_items')

    def __repr__(self):
        return f'<StockInItem {self.id}>'
