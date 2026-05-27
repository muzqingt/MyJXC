"""
main - 首页路由
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal
from app import db
from app.models import (
    Product, PurchaseOrder, SalesOrder,
    StockIn, StockOut, Supplier, Customer
)

bp = Blueprint('main', __name__)


@bp.route('/')
@login_required
def index():
    """业务概览仪表板"""
    today = datetime.now().date()

    # 今日采购订单
    today_purchase_orders = PurchaseOrder.query.filter(
        db.func.date(PurchaseOrder.created_at) == today
    ).count()
    
    # 今日销售订单
    today_sales_orders = SalesOrder.query.filter(
        db.func.date(SalesOrder.created_at) == today
    ).count()
    
    # 待入库采购单
    pending_stock_in = PurchaseOrder.query.filter(
        PurchaseOrder.status == 'confirmed'
    ).count()
    
    # 待出库销售单
    pending_stock_out = SalesOrder.query.filter(
        SalesOrder.status == 'confirmed'
    ).count()
    
    # 未完成入库单
    pending_stock_in_docs = StockIn.query.filter(
        StockIn.status == 'pending'
    ).count()
    
    # 未完成出库单
    pending_stock_out_docs = StockOut.query.filter(
        StockOut.status == 'pending'
    ).count()
    
    # 低库存商品（库存 < 安全库存）
    low_stock_products = Product.query.filter(
        Product.stock_quantity < Product.safety_stock,
        Product.safety_stock > 0
    ).count()
    
    # 零库存商品
    zero_stock_products = Product.query.filter(
        Product.stock_quantity <= 0
    ).count()
    
    # 总商品数
    total_products = Product.query.count()
    
    # 总供应商数
    total_suppliers = Supplier.query.count()
    
    # 总客户数
    total_customers = Customer.query.count()
    
    # 今日采购金额
    today_purchase_amount = db.session.query(
        db.func.sum(PurchaseOrder.total_amount)
    ).filter(
        db.func.date(PurchaseOrder.created_at) == today
    ).scalar() or Decimal('0')

    # 今日销售金额
    today_sales_amount = db.session.query(
        db.func.sum(SalesOrder.total_amount)
    ).filter(
        db.func.date(SalesOrder.created_at) == today
    ).scalar() or Decimal('0')

    # 最近采购订单
    recent_purchase_orders = PurchaseOrder.query.order_by(
        PurchaseOrder.created_at.desc()
    ).limit(5).all()
    
    # 最近销售订单
    recent_sales_orders = SalesOrder.query.order_by(
        SalesOrder.created_at.desc()
    ).limit(5).all()
    
    # 最近入库单
    recent_stock_ins = StockIn.query.order_by(
        StockIn.created_at.desc()
    ).limit(5).all()
    
    # 最近出库单
    recent_stock_outs = StockOut.query.order_by(
        StockOut.created_at.desc()
    ).limit(5).all()
    
    return render_template('main/dashboard.html',
                         title='业务概览',
                         # 统计数据
                         today_purchase_orders=today_purchase_orders,
                         today_sales_orders=today_sales_orders,
                         pending_stock_in=pending_stock_in,
                         pending_stock_out=pending_stock_out,
                         pending_stock_in_docs=pending_stock_in_docs,
                         pending_stock_out_docs=pending_stock_out_docs,
                         low_stock_products=low_stock_products,
                         zero_stock_products=zero_stock_products,
                         total_products=total_products,
                         total_suppliers=total_suppliers,
                         total_customers=total_customers,
                         today_purchase_amount=today_purchase_amount,
                         today_sales_amount=today_sales_amount,
                         # 最近记录
                         recent_purchase_orders=recent_purchase_orders,
                         recent_sales_orders=recent_sales_orders,
                         recent_stock_ins=recent_stock_ins,
                         recent_stock_outs=recent_stock_outs,
                         # 当前用户
                         current_user=current_user)
