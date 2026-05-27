from datetime import datetime
from app import db


class Supplier(db.Model):
    """供应商"""
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
    """客户"""
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
    """仓库"""
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
