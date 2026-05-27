from datetime import datetime
from app import db


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
