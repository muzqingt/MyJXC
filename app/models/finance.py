from datetime import datetime
from app import db


class Receipt(db.Model):
    """收款单"""
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
    """付款单"""
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
    """费用单"""
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
