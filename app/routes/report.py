from flask import render_template, redirect, url_for, flash, request, jsonify, Blueprint, make_response
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import Product, SalesOrder, PurchaseOrder, Customer, Supplier, Receipt, PurchaseOrderItem, SalesOrderItem
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from io import BytesIO
from decimal import Decimal
from urllib.parse import quote

# 创建蓝图
bp = Blueprint('report', __name__, url_prefix='/report')

# 样式定义
header_font = Font(bold=True, color='FFFFFF')
header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
header_alignment = Alignment(horizontal='center', vertical='center')
cell_alignment = Alignment(horizontal='center', vertical='center')
thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

def set_header_style(cell):
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = header_alignment
    cell.border = thin_border

def set_cell_style(cell):
    cell.alignment = cell_alignment
    cell.border = thin_border

@bp.route('/')
@login_required
def index():
    """报表分析首页"""
    return render_template('report/index.html', title='报表分析')

@bp.route('/inventory-report')
@login_required
def inventory_report():
    """进销存报表"""
    # 获取时间范围参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 如果没有提供日期，默认最近30天
    if not start_date or not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('日期格式无效，请使用YYYY-MM-DD格式', 'error')
            return redirect(url_for('report.index'))

    # 查询采购数据
    purchase_data = db.session.query(
        Product.id,
        Product.code,
        Product.name,
        db.func.sum(PurchaseOrderItem.quantity).label('purchase_quantity'),
        db.func.sum(PurchaseOrderItem.amount).label('purchase_amount')
    ).join(PurchaseOrderItem, Product.id == PurchaseOrderItem.product_id)\
     .join(PurchaseOrder, PurchaseOrderItem.order_id == PurchaseOrder.id)\
     .filter(PurchaseOrder.order_date.between(start_date, end_date))\
     .filter(PurchaseOrder.status == 'completed')\
     .group_by(Product.id).all()
    
    # 查询销售数据
    sales_data = db.session.query(
        Product.id,
        Product.code,
        Product.name,
        db.func.sum(SalesOrderItem.quantity).label('sales_quantity'),
        db.func.sum(SalesOrderItem.amount).label('sales_amount')
    ).join(SalesOrderItem, Product.id == SalesOrderItem.product_id)\
     .join(SalesOrder, SalesOrderItem.order_id == SalesOrder.id)\
     .filter(SalesOrder.order_date.between(start_date, end_date))\
     .filter(SalesOrder.status == 'completed')\
     .group_by(Product.id).all()
    
    # 合并数据
    report_data = []
    for product in Product.query.all():
        purchase = next((p for p in purchase_data if p.id == product.id), None)
        sales = next((s for s in sales_data if s.id == product.id), None)
        
        report_data.append({
            'id': product.id,
            'code': product.code,
            'name': product.name,
            'unit': product.unit,
            # 期初库存 = 期末库存 - 本期采购入库 + 本期销售出库（反推法）
            'beginning_stock': float(Decimal(str(product.stock_quantity or 0)) - Decimal(str(purchase.purchase_quantity if purchase else 0)) + Decimal(str(sales.sales_quantity if sales else 0))),
            'purchase_quantity': purchase.purchase_quantity if purchase else 0,
            'purchase_amount': float(purchase.purchase_amount) if purchase else 0,
            'sales_quantity': sales.sales_quantity if sales else 0,
            'sales_amount': float(sales.sales_amount) if sales else 0,
            'ending_stock': float(product.stock_quantity)
        })
    
    return render_template('report/inventory_report.html',
                         title='进销存报表',
                         report_data=report_data,
                         start_date=start_date,
                         end_date=end_date)

@bp.route('/sales-ranking')
@login_required
def sales_ranking():
    """销售排行榜"""
    # 获取时间范围参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 如果没有提供日期，默认最近30天
    if not start_date or not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('日期格式无效，请使用YYYY-MM-DD格式', 'error')
            return redirect(url_for('report.index'))

    # 查询销售排行榜
    ranking_data = db.session.query(
        Product.id,
        Product.code,
        Product.name,
        db.func.sum(SalesOrderItem.quantity).label('total_quantity'),
        db.func.sum(SalesOrderItem.amount).label('total_amount')
    ).join(SalesOrderItem, Product.id == SalesOrderItem.product_id)\
     .join(SalesOrder, SalesOrderItem.order_id == SalesOrder.id)\
     .filter(SalesOrder.order_date.between(start_date, end_date))\
     .filter(SalesOrder.status == 'completed')\
     .group_by(Product.id)\
     .order_by(db.func.sum(SalesOrderItem.amount).desc())\
     .limit(20).all()
    
    return render_template('report/sales_ranking.html',
                         title='销售排行榜',
                         ranking_data=ranking_data,
                         start_date=start_date,
                         end_date=end_date)

@bp.route('/customer-statistics')
@login_required
def customer_statistics():
    """客户统计"""
    # 查询客户消费统计
    customer_stats = db.session.query(
        Customer.id,
        Customer.code,
        Customer.name,
        db.func.count(SalesOrder.id).label('order_count'),
        db.func.sum(SalesOrder.total_amount).label('total_amount'),
        db.func.avg(SalesOrder.total_amount).label('avg_amount')
    ).outerjoin(SalesOrder, db.and_(Customer.id == SalesOrder.customer_id, SalesOrder.status == 'completed'))\
     .group_by(Customer.id)\
     .order_by(db.func.sum(SalesOrder.total_amount).desc())\
     .all()
    
    return render_template('report/customer_statistics.html',
                         title='客户统计',
                         customer_stats=customer_stats)

@bp.route('/supplier-statistics')
@login_required
def supplier_statistics():
    """供应商统计"""
    # 查询供应商采购统计
    supplier_stats = db.session.query(
        Supplier.id,
        Supplier.code,
        Supplier.name,
        db.func.count(PurchaseOrder.id).label('order_count'),
        db.func.sum(PurchaseOrder.total_amount).label('total_amount'),
        db.func.avg(PurchaseOrder.total_amount).label('avg_amount')
    ).outerjoin(PurchaseOrder, db.and_(Supplier.id == PurchaseOrder.supplier_id, PurchaseOrder.status == 'completed'))\
     .group_by(Supplier.id)\
     .order_by(db.func.sum(PurchaseOrder.total_amount).desc())\
     .all()
    
    return render_template('report/supplier_statistics.html',
                         title='供应商统计',
                         supplier_stats=supplier_stats)

@bp.route('/daily-report')
@login_required
def daily_report():
    """经营日报"""
    report_date = request.args.get('date', datetime.now().date())
    if isinstance(report_date, str):
        try:
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        except ValueError:
            flash('日期格式无效，请使用YYYY-MM-DD格式', 'error')
            return redirect(url_for('report.index'))

    # 当日销售统计
    daily_sales = db.session.query(
        db.func.sum(SalesOrder.total_amount).label('total_sales'),
        db.func.count(SalesOrder.id).label('order_count')
    ).filter(db.func.date(SalesOrder.order_date) == report_date)\
     .filter(SalesOrder.status == 'completed').first()
    
    # 当日采购统计
    daily_purchase = db.session.query(
        db.func.sum(PurchaseOrder.total_amount).label('total_purchase'),
        db.func.count(PurchaseOrder.id).label('order_count')
    ).filter(db.func.date(PurchaseOrder.order_date) == report_date)\
     .filter(PurchaseOrder.status == 'completed').first()
    
    # 当日收款统计
    daily_receipts = db.session.query(
        db.func.sum(Receipt.amount).label('total_receipts')
    ).filter(db.func.date(Receipt.receipt_date) == report_date).first()

    # 当日销售订单明细
    daily_sales_orders = SalesOrder.query.filter(
        db.func.date(SalesOrder.order_date) == report_date,
        SalesOrder.status == 'completed'
    ).order_by(SalesOrder.created_at.desc()).all()

    # 当日采购订单明细
    daily_purchase_orders = PurchaseOrder.query.filter(
        db.func.date(PurchaseOrder.order_date) == report_date,
        PurchaseOrder.status == 'completed'
    ).order_by(PurchaseOrder.created_at.desc()).all()
    
    return render_template('report/daily_report.html',
                         title='经营日报',
                         report_date=report_date,
                         daily_sales=daily_sales,
                         daily_purchase=daily_purchase,
                         daily_receipts=daily_receipts,
                         daily_sales_orders=daily_sales_orders,
                         daily_purchase_orders=daily_purchase_orders)

@bp.route('/api/sales-trend')
@login_required
def sales_trend_api():
    """销售趋势API，支持按天(days=N)或按月(默认最近12个月)"""
    days = request.args.get('days', type=int)

    if days:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)
        # 按天聚合
        sales_trend = db.session.query(
            db.func.date(SalesOrder.order_date).label('day'),
            db.func.sum(SalesOrder.total_amount).label('amount')
        ).filter(SalesOrder.order_date.between(start_date, end_date))\
         .filter(SalesOrder.status == 'completed')\
         .group_by('day')\
         .order_by('day').all()
        # 补全无数据的日期
        result_data = {}
        for item in sales_trend:
            result_data[str(item.day)] = float(item.amount or 0)
        result = []
        current = start_date
        while current <= end_date:
            key = current.strftime('%Y-%m-%d')
            result.append({'label': current.strftime('%m-%d'), 'amount': result_data.get(key, 0)})
            current += timedelta(days=1)
        return jsonify(result)

    # 默认按月聚合，最近12个月
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)

    sales_trend = db.session.query(
        db.func.strftime('%Y-%m', SalesOrder.order_date).label('month'),
        db.func.sum(SalesOrder.total_amount).label('amount')
    ).filter(SalesOrder.order_date.between(start_date, end_date))\
     .filter(SalesOrder.status == 'completed')\
     .group_by('month')\
     .order_by('month').all()

    result = [{'label': item.month, 'amount': float(item.amount or 0)} for item in sales_trend]
    return jsonify(result)

# ==================== 导出功能 ====================

@bp.route('/export/inventory')
@login_required
def export_inventory():
    """导出进销存报表"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # 获取数据
    purchase_data = db.session.query(
        Product.id,
        db.func.sum(PurchaseOrderItem.quantity).label('purchase_quantity'),
        db.func.sum(PurchaseOrderItem.amount).label('purchase_amount')
    ).join(PurchaseOrderItem, Product.id == PurchaseOrderItem.product_id)\
     .join(PurchaseOrder, PurchaseOrderItem.order_id == PurchaseOrder.id)\
     .filter(PurchaseOrder.order_date.between(start_date, end_date))\
     .filter(PurchaseOrder.status == 'completed')\
     .group_by(Product.id).all()
    
    sales_data = db.session.query(
        Product.id,
        db.func.sum(SalesOrderItem.quantity).label('sales_quantity'),
        db.func.sum(SalesOrderItem.amount).label('sales_amount')
    ).join(SalesOrderItem, Product.id == SalesOrderItem.product_id)\
     .join(SalesOrder, SalesOrderItem.order_id == SalesOrder.id)\
     .filter(SalesOrder.order_date.between(start_date, end_date))\
     .filter(SalesOrder.status == 'completed')\
     .group_by(Product.id).all()
    
    report_data = []
    for product in Product.query.all():
        purchase = next((p for p in purchase_data if p.id == product.id), None)
        sales = next((s for s in sales_data if s.id == product.id), None)
        report_data.append({
            'code': product.code,
            'name': product.name,
            'unit': product.unit,
            'purchase_quantity': purchase.purchase_quantity if purchase else 0,
            'purchase_amount': float(purchase.purchase_amount) if purchase else 0,
            'sales_quantity': sales.sales_quantity if sales else 0,
            'sales_amount': float(sales.sales_amount) if sales else 0,
            'ending_stock': float(product.stock_quantity)
        })
    
    # 创建Excel
    wb = Workbook()
    ws = wb.active
    ws.title = '进销存报表'
    
    # 表头
    headers = ['序号', '商品编码', '商品名称', '单位', '采购数量', '采购金额', '销售数量', '销售金额', '期末库存']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        set_header_style(cell)
    
    # 数据
    for row, item in enumerate(report_data, 2):
        ws.cell(row=row, column=1, value=row-1)
        ws.cell(row=row, column=2, value=item['code'])
        ws.cell(row=row, column=3, value=item['name'])
        ws.cell(row=row, column=4, value=item['unit'])
        ws.cell(row=row, column=5, value=float(item['purchase_quantity']))
        ws.cell(row=row, column=6, value=item['purchase_amount'])
        ws.cell(row=row, column=7, value=float(item['sales_quantity']))
        ws.cell(row=row, column=8, value=item['sales_amount'])
        ws.cell(row=row, column=9, value=item['ending_stock'])
        for col in range(1, 10):
            set_cell_style(ws.cell(row=row, column=col))
    
    # 调整列宽
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 25
    ws.column_dimensions['D'].width = 8
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 12
    ws.column_dimensions['H'].width = 12
    ws.column_dimensions['I'].width = 12
    
    # 发送文件
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    filename = f'inventory_report_{start_date}_{end_date}.xlsx'
    response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quote(filename)}'
    return response

@bp.route('/export/sales-ranking')
@login_required
def export_sales_ranking():
    """导出销售排行榜"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    ranking_data = db.session.query(
        Product.id,
        Product.code,
        Product.name,
        db.func.sum(SalesOrderItem.quantity).label('total_quantity'),
        db.func.sum(SalesOrderItem.amount).label('total_amount')
    ).join(SalesOrderItem, Product.id == SalesOrderItem.product_id)\
     .join(SalesOrder, SalesOrderItem.order_id == SalesOrder.id)\
     .filter(SalesOrder.order_date.between(start_date, end_date))\
     .filter(SalesOrder.status == 'completed')\
     .group_by(Product.id)\
     .order_by(db.func.sum(SalesOrderItem.amount).desc())\
     .limit(20).all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = '销售排行榜'
    
    headers = ['排名', '商品编码', '商品名称', '销售数量', '销售金额', '平均单价']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        set_header_style(cell)
    
    for row, item in enumerate(ranking_data, 2):
        avg_price = item.total_amount / item.total_quantity if item.total_quantity > 0 else 0
        ws.cell(row=row, column=1, value=row-1)
        ws.cell(row=row, column=2, value=item.code)
        ws.cell(row=row, column=3, value=item.name)
        ws.cell(row=row, column=4, value=float(item.total_quantity))
        ws.cell(row=row, column=5, value=float(item.total_amount))
        ws.cell(row=row, column=6, value=avg_price)
        for col in range(1, 7):
            set_cell_style(ws.cell(row=row, column=col))
    
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 25
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 12
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    filename = f'sales_ranking_{start_date}_{end_date}.xlsx'
    response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quote(filename)}'
    return response

@bp.route('/export/customer')
@login_required
def export_customer():
    """导出客户统计"""
    customer_stats = db.session.query(
        Customer.id,
        Customer.code,
        Customer.name,
        db.func.count(SalesOrder.id).label('order_count'),
        db.func.sum(SalesOrder.total_amount).label('total_amount'),
        db.func.avg(SalesOrder.total_amount).label('avg_amount')
    ).outerjoin(SalesOrder, db.and_(Customer.id == SalesOrder.customer_id, SalesOrder.status == 'completed'))\
     .group_by(Customer.id)\
     .order_by(db.func.sum(SalesOrder.total_amount).desc())\
     .all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = '客户统计'
    
    headers = ['序号', '客户编码', '客户名称', '订单数量', '消费总额', '平均订单金额']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        set_header_style(cell)
    
    for row, item in enumerate(customer_stats, 2):
        ws.cell(row=row, column=1, value=row-1)
        ws.cell(row=row, column=2, value=item.code)
        ws.cell(row=row, column=3, value=item.name)
        ws.cell(row=row, column=4, value=item.order_count or 0)
        ws.cell(row=row, column=5, value=float(item.total_amount or 0))
        ws.cell(row=row, column=6, value=float(item.avg_amount or 0))
        for col in range(1, 7):
            set_cell_style(ws.cell(row=row, column=col))
    
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 15
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    filename = f'customer_stats_{datetime.now().strftime("%Y%m%d")}.xlsx'
    response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quote(filename)}'
    return response

@bp.route('/export/supplier')
@login_required
def export_supplier():
    """导出供应商统计"""
    supplier_stats = db.session.query(
        Supplier.id,
        Supplier.code,
        Supplier.name,
        db.func.count(PurchaseOrder.id).label('order_count'),
        db.func.sum(PurchaseOrder.total_amount).label('total_amount'),
        db.func.avg(PurchaseOrder.total_amount).label('avg_amount')
    ).outerjoin(PurchaseOrder, db.and_(Supplier.id == PurchaseOrder.supplier_id, PurchaseOrder.status == 'completed'))\
     .group_by(Supplier.id)\
     .order_by(db.func.sum(PurchaseOrder.total_amount).desc())\
     .all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = '供应商统计'
    
    headers = ['序号', '供应商编码', '供应商名称', '采购订单数', '采购总金额', '平均订单金额']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        set_header_style(cell)
    
    for row, item in enumerate(supplier_stats, 2):
        ws.cell(row=row, column=1, value=row-1)
        ws.cell(row=row, column=2, value=item.code)
        ws.cell(row=row, column=3, value=item.name)
        ws.cell(row=row, column=4, value=item.order_count or 0)
        ws.cell(row=row, column=5, value=float(item.total_amount or 0))
        ws.cell(row=row, column=6, value=float(item.avg_amount or 0))
        for col in range(1, 7):
            set_cell_style(ws.cell(row=row, column=col))
    
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 15
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    filename = f'supplier_stats_{datetime.now().strftime("%Y%m%d")}.xlsx'
    response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quote(filename)}'
    return response

@bp.route('/export-products')
@login_required
def export_products():
    """导出商品数据"""
    from openpyxl import Workbook
    
    products = Product.query.order_by(Product.code).all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = '商品数据'
    
    headers = ['商品编码', '商品名称', '规格', '单位', '分类', '进价', '售价', '库存', '安全库存', '状态']
    ws.append(headers)
    
    for product in products:
        ws.append([
            product.code or '',
            product.name or '',
            product.specification or '',
            product.unit or '',
            product.category.name if product.category else '',
            str(product.purchase_price or ''),
            str(product.sale_price or ''),
            float(product.stock_quantity or 0),
            float(product.safety_stock or 0) if product.safety_stock else '',
            '正常' if float(product.stock_quantity or 0) > 0 else '零库存'
        ])
    
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 8
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 10
    ws.column_dimensions['G'].width = 10
    ws.column_dimensions['H'].width = 10
    ws.column_dimensions['I'].width = 10
    ws.column_dimensions['J'].width = 8
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    filename = f'products_{datetime.now().strftime("%Y%m%d")}.xlsx'
    response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    return response

@bp.route('/export/daily')
@login_required
def export_daily():
    """导出的日报"""
    report_date = request.args.get('date', datetime.now().date())
    if isinstance(report_date, str):
        report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
    
    daily_sales = db.session.query(
        db.func.sum(SalesOrder.total_amount).label('total_sales'),
        db.func.count(SalesOrder.id).label('order_count')
    ).filter(db.func.date(SalesOrder.order_date) == report_date)\
     .filter(SalesOrder.status == 'completed').first()
    
    daily_purchase = db.session.query(
        db.func.sum(PurchaseOrder.total_amount).label('total_purchase'),
        db.func.count(PurchaseOrder.id).label('order_count')
    ).filter(db.func.date(PurchaseOrder.order_date) == report_date)\
     .filter(PurchaseOrder.status == 'completed').first()
    
    daily_receipts = db.session.query(
        db.func.sum(Receipt.amount).label('total_receipts')
    ).filter(db.func.date(Receipt.receipt_date) == report_date).first()
    
    wb = Workbook()
    ws = wb.active
    ws.title = '经营日报'
    
    # 标题
    ws.merge_cells('A1:D1')
    ws.cell(row=1, column=1, value=f'经营日报 - {report_date}')
    ws.cell(row=1, column=1).font = Font(bold=True, size=14)
    ws.cell(row=1, column=1).alignment = Alignment(horizontal='center')
    
    # 统计数据
    ws.cell(row=3, column=1, value='项目')
    ws.cell(row=3, column=2, value='金额')
    ws.cell(row=3, column=3, value='订单数')
    ws.cell(row=3, column=4, value='平均')
    for col in range(1, 5):
        set_header_style(ws.cell(row=3, column=col))
    
    data = [
        ('销售总额', float(daily_sales.total_sales or 0), daily_sales.order_count or 0, 
         (daily_sales.total_sales or 0) / (daily_sales.order_count or 1)),
        ('采购总额', float(daily_purchase.total_purchase or 0), daily_purchase.order_count or 0,
         (daily_purchase.total_purchase or 0) / (daily_purchase.order_count or 1)),
        ('收款总额', float(daily_receipts.total_receipts or 0), '-', '-'),
    ]
    
    for row_idx, (name, amount, count, avg) in enumerate(data, 4):
        ws.cell(row=row_idx, column=1, value=name)
        ws.cell(row=row_idx, column=2, value=amount if amount != '-' else '-')
        ws.cell(row=row_idx, column=3, value=count)
        ws.cell(row=row_idx, column=4, value=avg if avg != '-' else '-')
        for col in range(1, 5):
            set_cell_style(ws.cell(row=row_idx, column=col))
    
    # 汇总
    row_idx = 8
    ws.cell(row=row_idx, column=1, value='汇总')
    ws.cell(row=row_idx, column=1).font = Font(bold=True)
    row_idx += 1
    # 毛利润 = 销售总额 - 采购总额
    ws.cell(row=row_idx, column=1, value='毛利润')
    ws.cell(row=row_idx, column=2, value=(daily_sales.total_sales or 0) - (daily_purchase.total_purchase or 0))
    row_idx += 1
    # 毛利率 = 毛利润 / 采购总额 * 100
    ws.cell(row=row_idx, column=1, value='毛利率')
    ws.cell(row=row_idx, column=2, value=f'{((daily_sales.total_sales or 0) - (daily_purchase.total_purchase or 0)) / (daily_purchase.total_purchase or 1) * 100:.2f}%')
    
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 15
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    filename = f'daily_report_{report_date}.xlsx'
    response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quote(filename)}'
    return response
