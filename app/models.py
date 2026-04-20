from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, user
    is_active = db.Column(db.Boolean, default=True)  # 用户是否激活
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)
    
    @property
    def is_authenticated(self):
        return True
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 自关联关系
    parent = db.relationship('Category', remote_side=[id], backref='children')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    specification = db.Column(db.String(200))  # 规格
    unit = db.Column(db.String(20), nullable=False, default='个')  # 计量单位
    purchase_price = db.Column(db.Numeric(10, 2), default=0)  # 采购价
    sale_price = db.Column(db.Numeric(10, 2), default=0)  # 销售价
    stock_quantity = db.Column(db.Numeric(10, 2), default=0)  # 当前库存
    safety_stock = db.Column(db.Numeric(10, 2), default=0)  # 安全库存
    image_path = db.Column(db.String(500))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    category = db.relationship('Category', backref='products')
    
    def __repr__(self):
        return f'<Product {self.code} - {self.name}>'

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    email = db.Column(db.String(120))
    payable_balance = db.Column(db.Numeric(12, 2), default=0)  # 应付余额
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Supplier {self.code} - {self.name}>'

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    email = db.Column(db.String(120))
    receivable_balance = db.Column(db.Numeric(12, 2), default=0)  # 应收余额
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Customer {self.code} - {self.name}>'

class Warehouse(db.Model):
    __tablename__ = 'warehouses'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    manager = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Warehouse {self.code} - {self.name}>'

class PurchaseOrder(db.Model):
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

class SalesOrder(db.Model):
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

class StockLog(db.Model):
    __tablename__ = 'stock_logs'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    change_type = db.Column(db.String(20), nullable=False)  # in, out, adjust_in, adjust_out, check_in, check_out
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    before_quantity = db.Column(db.Numeric(10, 2), nullable=False)
    after_quantity = db.Column(db.Numeric(10, 2), nullable=False)
    reference_id = db.Column(db.Integer)  # 关联单据ID
    reference_type = db.Column(db.String(50))  # 单据类型
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    
    product = db.relationship('Product', backref='stock_logs')
    warehouse = db.relationship('Warehouse', backref='stock_logs')
    creator = db.relationship('User', backref='created_stock_logs')
    
    # 动态关联关系 - 使用字符串引用避免循环导入
    @property
    def stock_in(self):
        if self.reference_type == 'stock_in' and self.reference_id:
            from app.models import StockIn
            return StockIn.query.get(self.reference_id)
        return None
    
    @property
    def stock_out(self):
        if self.reference_type == 'stock_out' and self.reference_id:
            from app.models import StockOut
            return StockOut.query.get(self.reference_id)
        return None
    
    @property
    def reference_number(self):
        """获取关联单号"""
        if not self.reference_id or not self.reference_type:
            return ''
        
        if self.reference_type == 'stock_in':
            stock_in = StockIn.query.get(self.reference_id)
            return stock_in.receipt_number if stock_in else ''
        elif self.reference_type == 'stock_out':
            stock_out = StockOut.query.get(self.reference_id)
            return stock_out.delivery_number if stock_out else ''
        elif self.reference_type == 'purchase_order':
            po = PurchaseOrder.query.get(self.reference_id)
            return po.order_number if po else ''
        elif self.reference_type == 'sales_order':
            so = SalesOrder.query.get(self.reference_id)
            return so.order_number if so else ''
        return ''
    
    def __repr__(self):
        return f'<StockLog {self.id} - {self.change_type}>'

class Receipt(db.Model):
    __tablename__ = 'receipts'
    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    receipt_date = db.Column(db.Date, nullable=False, default=datetime.now)
    payment_method = db.Column(db.String(50), default='cash')  # cash, bank_transfer, wechat, alipay
    reference_type = db.Column(db.String(50))  # sales_order, other
    reference_id = db.Column(db.String(500), nullable=True, index=True)  # 改为String支持多订单，以逗号分隔存储
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)

    customer = db.relationship('Customer', backref='receipts')
    creator = db.relationship('User', backref='created_receipts')
    
    def __repr__(self):
        return f'<Receipt {self.receipt_number}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    payment_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=datetime.now)
    payment_method = db.Column(db.String(50), default='cash')  # cash, bank_transfer, wechat, alipay
    reference_type = db.Column(db.String(50))  # purchase_order, other
    reference_id = db.Column(db.String(500), nullable=True, index=True)  # 改为String支持多订单，以逗号分隔存储
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)

    supplier = db.relationship('Supplier', backref='payments')
    creator = db.relationship('User', backref='created_payments')
    
    def __repr__(self):
        return f'<Payment {self.payment_number}>'

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    expense_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False)  # 费用类别
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False, default=datetime.now)
    payee = db.Column(db.String(200))  # 收款方
    payment_method = db.Column(db.String(50), default='cash')
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    creator = db.relationship('User', backref='created_expenses')
    
    def __repr__(self):
        return f'<Expense {self.expense_number}>'

class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    
    user = db.relationship('User', backref='logs')
    
    def __repr__(self):
        return f'<Log {self.id} - {self.action}>'

class SystemSetting(db.Model):
    """系统设置模型"""
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column('key', db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    @classmethod
    def get_value(cls, key, default=None):
        """获取设置值"""
        setting = cls.query.filter_by(setting_key=key).first()
        return setting.value if setting else default
    
    @classmethod
    def set_value(cls, key, value):
        """设置值"""
        setting = cls.query.filter_by(setting_key=key).first()
        if setting:
            setting.value = value if value else ''
        else:
            setting = cls(setting_key=key, value=value if value else '')
            db.session.add(setting)
        db.session.commit()
    
    def __repr__(self):
        return f'<SystemSetting {self.setting_key}>'
