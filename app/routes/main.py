"""
main - 首页路由
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from decimal import Decimal
from app import db
from app.models import (
    Product, PurchaseOrder, SalesOrder,
    StockIn, StockOut, Supplier, Customer, Warehouse
)

bp = Blueprint('main', __name__)


@bp.route('/api/sales-trend')
@login_required
def api_sales_trend():
    """近 30 天销售趋势数据"""
    today = datetime.now().date()
    start_date = today - timedelta(days=29)

    # 查询每日销售金额
    results = db.session.query(
        db.func.date(SalesOrder.order_date).label('date'),
        db.func.coalesce(db.func.sum(SalesOrder.total_amount), 0).label('amount')
    ).filter(
        SalesOrder.order_date >= start_date,
        SalesOrder.order_date <= today,
        SalesOrder.status.in_(['confirmed', 'completed'])
    ).group_by(
        db.func.date(SalesOrder.order_date)
    ).order_by('date').all()

    # 填充缺失日期
    date_map = {str(r.date): float(r.amount) for r in results}
    dates = []
    amounts = []
    current = start_date
    while current <= today:
        date_str = current.strftime('%Y-%m-%d')
        dates.append(date_str)
        amounts.append(date_map.get(date_str, 0))
        current += timedelta(days=1)

    return jsonify({'dates': dates, 'amounts': amounts})


@bp.route('/api/stock-overview')
@login_required
def api_stock_overview():
    """各仓库库存分布"""
    warehouses = Warehouse.query.all()
    data = []
    for wh in warehouses:
        # 计算该仓库的库存总量（通过 StockLog 计算）
        from app.models import StockLog
        stock_in = db.session.query(
            db.func.coalesce(db.func.sum(StockLog.quantity), 0)
        ).filter(
            StockLog.warehouse_id == wh.id,
            StockLog.change_type.in_(['in', 'adjust_in', 'check_in', 'return_in'])
        ).scalar()

        stock_out = db.session.query(
            db.func.coalesce(db.func.sum(StockLog.quantity), 0)
        ).filter(
            StockLog.warehouse_id == wh.id,
            StockLog.change_type.in_(['out', 'adjust_out', 'check_out', 'return_out', 'stock_transfer'])
        ).scalar()

        total = float(stock_in) - float(stock_out)
        data.append({'warehouse': wh.name, 'stock': max(0, total)})

    return jsonify(data)


@bp.route('/api/finance-summary')
@login_required
def api_finance_summary():
    """近 7 天收支数据"""
    from app.models import Receipt, Payment, Expense

    today = datetime.now().date()
    start_date = today - timedelta(days=6)

    # 每日收款
    receipts = db.session.query(
        db.func.date(Receipt.receipt_date).label('date'),
        db.func.coalesce(db.func.sum(Receipt.amount), 0).label('amount')
    ).filter(
        Receipt.receipt_date >= start_date
    ).group_by(db.func.date(Receipt.receipt_date)).all()

    # 每日付款
    payments = db.session.query(
        db.func.date(Payment.payment_date).label('date'),
        db.func.coalesce(db.func.sum(Payment.amount), 0).label('amount')
    ).filter(
        Payment.payment_date >= start_date
    ).group_by(db.func.date(Payment.payment_date)).all()

    # 构建数据
    receipt_map = {str(r.date): float(r.amount) for r in receipts}
    payment_map = {str(p.date): float(p.amount) for p in payments}

    dates = []
    income = []
    expense = []
    current = start_date
    while current <= today:
        date_str = current.strftime('%Y-%m-%d')
        dates.append(date_str)
        income.append(receipt_map.get(date_str, 0))
        expense.append(payment_map.get(date_str, 0))
        current += timedelta(days=1)

    return jsonify({'dates': dates, 'income': income, 'expense': expense})


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
