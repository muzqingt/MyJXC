from datetime import datetime
from app import db


class StockLog(db.Model):
    """库存变动流水"""
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

    @property
    def reference_number(self) -> str:
        """获取关联单号"""
        if not self.reference_id or not self.reference_type:
            return ''

        if self.reference_type == 'stock_in':
            from app.models import StockIn
            stock_in = StockIn.query.get(self.reference_id)
            return stock_in.receipt_number if stock_in else ''
        elif self.reference_type == 'stock_out':
            from app.models import StockOut
            stock_out = StockOut.query.get(self.reference_id)
            return stock_out.delivery_number if stock_out else ''
        elif self.reference_type == 'purchase_order':
            from app.models import PurchaseOrder
            po = PurchaseOrder.query.get(self.reference_id)
            return po.order_number if po else ''
        elif self.reference_type == 'sales_order':
            from app.models import SalesOrder
            so = SalesOrder.query.get(self.reference_id)
            return so.order_number if so else ''
        elif self.reference_type == 'purchase_return':
            from app.models import PurchaseReturn
            pr = PurchaseReturn.query.get(self.reference_id)
            return pr.return_number if pr else ''
        elif self.reference_type == 'sales_return':
            from app.models import SalesReturn
            sr = SalesReturn.query.get(self.reference_id)
            return sr.return_number if sr else ''
        return ''

    def __repr__(self):
        return f'<StockLog {self.id} - {self.change_type}>'
