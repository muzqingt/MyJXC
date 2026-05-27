from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, make_response, abort
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal
from app import db
from app.models import Product, Warehouse, StockLog
import io
from app.forms import StockAdjustForm, StockTransferForm
from app.utils import to_decimal, apply_excel_header_style, EXCEL_THIN_BORDER
from sqlalchemy.exc import SQLAlchemyError

VALID_LOG_TYPES = {'in', 'out', 'check_in', 'check_out', 'adjust_in', 'adjust_out', 'return_in', 'return_out', 'stock_transfer'}

def get_product_stock_in_warehouse(product_id, warehouse_id):
    """根据 StockLog 计算某商品在指定仓库的实际库存

    注意：返回实际库存（可为负数），调用方需自行判断库存异常。
    使用 max(0, ...) 会掩盖调拨/出库计算错误，不利于排查问题。
    """
    stock_in_types = ('in', 'check_in', 'adjust_in', 'return_in')
    result = db.session.query(
        db.func.sum(
            db.case(
                (StockLog.change_type.in_(stock_in_types), StockLog.quantity),
                else_=-StockLog.quantity
            )
        )
    ).filter(
        StockLog.product_id == product_id,
        StockLog.warehouse_id == warehouse_id
    ).scalar()
    return to_decimal(result) if result is not None else Decimal('0')

# 创建蓝图
bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@bp.route('/')
@login_required
def index():
    """库存管理首页"""
    products = Product.query.all()
    warehouses = Warehouse.query.all()
    
    low_stock_products = [p for p in products if p.safety_stock > 0 and p.stock_quantity <= p.safety_stock]
    
    return render_template('inventory/index.html', 
                         title='库存管理',
                         products=products,
                         warehouses=warehouses,
                         low_stock_products=low_stock_products)

@bp.route('/products')
@login_required
def product_list():
    """商品库存列表"""
    products = Product.query.all()
    
    # 计算总库存价值和潜在销售价值
    total_stock_value = Decimal('0')
    total_potential_value = Decimal('0')
    for product in products:
        stock_qty = Decimal(str(product.stock_quantity or 0))
        purchase_price = Decimal(str(product.purchase_price or 0))
        sale_price = Decimal(str(product.sale_price or 0))
        total_stock_value += stock_qty * purchase_price
        total_potential_value += stock_qty * sale_price
    
    return render_template('inventory/products.html', 
                         title='商品库存',
                         products=products,
                         total_stock_value=total_stock_value,
                         total_potential_value=total_potential_value)

@bp.route('/warehouse/<int:warehouse_id>')
@login_required
def warehouse_stock(warehouse_id):
    """仓库库存明细 - 显示指定仓库中所有产品的库存"""
    warehouse = db.session.get(Warehouse, warehouse_id)
    if warehouse is None:
        abort(404)
    products = Product.query.all()
    
    # Calculate per-product stock in this specific warehouse
    product_stocks = {}
    for product in products:
        product_stocks[product.id] = get_product_stock_in_warehouse(product.id, warehouse_id)
    
    return render_template('inventory/warehouse_stock.html',
                         title=f'{warehouse.name}库存',
                         warehouse=warehouse,
                         products=products,
                         product_stocks=product_stocks,
                         StockLog=StockLog)

@bp.route('/stock-check', methods=['GET', 'POST'])
@login_required
def stock_check():
    """库存盘点"""
    if request.method == 'POST':
        try:
            product_ids = request.form.getlist('product_id[]')
            actual_quantities = request.form.getlist('actual_quantity[]')
            notes = request.form.get('notes', '')
            warehouse_id = int(request.form.get('warehouse_id') or 0)

            if len(actual_quantities) != len(product_ids):
                flash('盘点数据不完整，请重新提交！', 'danger')
                return redirect(url_for('inventory.stock_check'))

            # 校验仓库是否存在
            warehouse = db.session.get(Warehouse, warehouse_id)
            if not warehouse:
                flash('仓库不存在！', 'danger')
                return redirect(url_for('inventory.stock_check'))
            
            for i in range(len(product_ids)):
                if product_ids[i] and actual_quantities[i]:
                    product = db.session.query(Product).filter(Product.id == int(product_ids[i])).with_for_update().first()
                    if product:
                        book_quantity = to_decimal(product.stock_quantity)
                        actual_quantity = to_decimal(actual_quantities[i])
                        
                        # 计算差异：正值为盘盈(入库)，负值为盘亏(出库)
                        if book_quantity != actual_quantity:
                            diff = actual_quantity - book_quantity
                            change_type = 'check_in' if diff > 0 else 'check_out'
                            
                            product.stock_quantity = actual_quantity
                            
                            log = StockLog(
                                product_id=product.id,
                                warehouse_id=warehouse_id,
                                change_type=change_type,
                                quantity=abs(diff),
                                before_quantity=book_quantity,
                                after_quantity=actual_quantity,
                                reference_type='stock_check',
                                notes=f'库存盘点: {notes}',
                                created_by=current_user.id
                            )
                            db.session.add(log)
            
            db.session.commit()
            flash('库存盘点完成！', 'success')
            return redirect(url_for('inventory.stock_check'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('盘点失败，请重试', 'danger')
    
    products = Product.query.all()
    warehouses = Warehouse.query.all()
    
    # Pre-calculate per-warehouse stock for each product
    # Build a dict: {(product_id, warehouse_id): stock}
    warehouse_stocks = {}
    all_warehouses = {w.id: w for w in warehouses}
    for product in products:
        product_wh_stocks = {}
        for wh_id in all_warehouses:
            stock = get_product_stock_in_warehouse(product.id, wh_id)
            warehouse_stocks[(product.id, wh_id)] = stock
            product_wh_stocks[wh_id] = stock
        warehouse_stocks[product.id] = product_wh_stocks  # Store per-product lookup
    
    return render_template('inventory/stock_check.html',
                         title='库存盘点',
                         products=products,
                         warehouses=warehouses,
                         warehouse_stocks=warehouse_stocks)

@bp.route('/stock-transfer', methods=['GET', 'POST'])
@login_required
def stock_transfer():
    """库存调拨"""
    warehouses = Warehouse.query.all()
    products = Product.query.all()
    today = datetime.now().strftime('%Y-%m-%d')

    products_list = [{
        'id': p.id,
        'code': p.code,
        'name': p.name,
        'specification': p.specification or '',
        'unit': p.unit,
        'stock_quantity': float(p.stock_quantity) if p.stock_quantity else 0,
        'purchase_price': float(p.purchase_price) if p.purchase_price else 0
    } for p in products]

    # 创建表单并设置仓库选项
    form = StockTransferForm()
    form.from_warehouse.choices = [(w.id, f"{w.code} - {w.name}") for w in warehouses]
    form.to_warehouse.choices = form.from_warehouse.choices
    form.transfer_date.data = datetime.now().date()

    # 设置产品选项（动态）
    product_choices = [(p.id, f"{p.code} - {p.name}") for p in products]
    for entry in form.items.entries:
        entry.form.product_id.choices = product_choices

    # 用于存储验证失败时回填JS表格的数据
    items_data = []

    if form.validate_on_submit():
        try:
            # 使用 WTForms FieldList 获取数据
            items = form.items.data
            from_warehouse_id = form.from_warehouse.data
            to_warehouse_id = form.to_warehouse.data
            notes = form.remark.data or ''

            if from_warehouse_id == to_warehouse_id:
                flash('调出仓库和调入仓库不能相同！', 'danger')
                items_data = [
                    {'product_id': item['product_id'], 'quantity': item['quantity']}
                    for item in items
                    if item['product_id']
                ]
                return render_template('inventory/stock_transfer.html',
                                     title='库存调拨',
                                     form=form,
                                     warehouses=warehouses,
                                     products=products,
                                     products_list=products_list,
                                     today=today,
                                     items_data=items_data)

            to_warehouse = db.session.get(Warehouse, to_warehouse_id)
            from_warehouse_obj = db.session.get(Warehouse, from_warehouse_id)
            to_warehouse_name = to_warehouse.name if to_warehouse else '未知仓库'
            from_warehouse_name = from_warehouse_obj.name if from_warehouse_obj else '未知仓库'

            # 预计算初始仓库库存（用于追踪同一商品多次调拨的正确 before_quantity）
            # product.stock_quantity 是全局库存，需结合 StockLog 计算出各仓库基准库存
            product_warehouse_stock = {}
            for item in items:
                if item['product_id'] and item['quantity']:
                    pid = item['product_id']
                    if pid not in product_warehouse_stock:
                        product = db.session.get(Product, pid)
                        if product:
                            # 全局库存减去各仓库的 StockLog 合计，得到"未记录"的起点
                            # 再加上源仓库的 StockLog，得到源仓库初始库存
                            global_stock = to_decimal(product.stock_quantity)
                            from_log = get_product_stock_in_warehouse(pid, from_warehouse_id)
                            to_log = get_product_stock_in_warehouse(pid, to_warehouse_id)
                            # 各仓库 StockLog 总和
                            all_log = to_decimal(db.session.query(db.func.sum(
                                db.case(
                                    (StockLog.change_type.in_(['in', 'check_in', 'adjust_in', 'return_in']), StockLog.quantity),
                                    else_=0 - StockLog.quantity
                                )
                            )).filter(StockLog.product_id == pid).scalar())
                            # 仓库粒度的初始库存
                            product_warehouse_stock[pid] = {
                                from_warehouse_id: global_stock - all_log + from_log,
                                to_warehouse_id: global_stock - all_log + to_log
                            }

            for item in items:
                if item['product_id'] and item['quantity']:
                    product = db.session.query(Product).filter(Product.id == item['product_id']).with_for_update().first()
                    if product:
                        quantity = to_decimal(item['quantity'])
                        pid = product.id

                        actual_stock = get_product_stock_in_warehouse(pid, from_warehouse_id)
                        if actual_stock < quantity:
                            flash(f'{product.name} 库存不足！', 'danger')
                            items_data = [
                                {'product_id': i['product_id'], 'quantity': i['quantity']}
                                for i in items
                                if i['product_id']
                            ]
                            db.session.rollback()
                            return render_template('inventory/stock_transfer.html',
                                                 title='库存调拨',
                                                 form=form,
                                                 warehouses=warehouses,
                                                 products=products,
                                                 products_list=products_list,
                                                 today=today,
                                                 items_data=items_data)

                        # 步骤1：源仓库扣减库存，记录出库日志
                        product.stock_quantity -= quantity
                        before_out = actual_stock
                        after_out = actual_stock - quantity
                        log_out = StockLog(
                            product_id=product.id,
                            warehouse_id=from_warehouse_id,
                            change_type='out',
                            quantity=quantity,
                            before_quantity=before_out,
                            after_quantity=after_out,
                            reference_type='stock_transfer',
                            notes=f'调拨出库至{to_warehouse_name}: {notes}',
                            created_by=current_user.id
                        )
                        product_warehouse_stock[pid][from_warehouse_id] = after_out
                        db.session.add(log_out)

                        # 步骤2：目标仓库增加库存，记录入库日志
                        product.stock_quantity += quantity
                        actual_stock_to = product_warehouse_stock[pid][to_warehouse_id]
                        before_in = actual_stock_to
                        after_in = actual_stock_to + quantity
                        log_in = StockLog(
                            product_id=product.id,
                            warehouse_id=to_warehouse_id,
                            change_type='in',
                            quantity=quantity,
                            before_quantity=before_in,
                            after_quantity=after_in,
                            reference_type='stock_transfer',
                            notes=f'调拨入库自{from_warehouse_name}: {notes}',
                            created_by=current_user.id
                        )
                        product_warehouse_stock[pid][to_warehouse_id] = after_in
                        db.session.add(log_in)

            db.session.commit()
            flash('库存调拨完成！', 'success')
            return redirect(url_for('inventory.stock_transfer'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('调拨失败，请重试', 'danger')

    # 验证失败时，从 form.items 构建 items_data 供 JS 回填
    if form.items.data:
        items_data = [
            {'product_id': item['product_id'], 'quantity': item['quantity']}
            for item in form.items.data
            if item['product_id']
        ]

    return render_template('inventory/stock_transfer.html',
                         title='库存调拨',
                         form=form,
                         warehouses=warehouses,
                         products=products,
                         products_list=products_list,
                         today=today,
                         items_data=items_data)


@bp.route('/export-warehouse-stock/<int:warehouse_id>')
@login_required
def export_warehouse_stock(warehouse_id):
    """导出仓库库存报表"""
    from urllib.parse import quote
    from openpyxl import Workbook

    warehouse = db.session.get(Warehouse, warehouse_id)
    if warehouse is None:
        abort(404)
    products = Product.query.all()

    wb = Workbook()
    ws = wb.active
    ws.title = f'{warehouse.name}库存'

    headers = ['商品编码', '商品名称', '规格', '单位', '当前库存', '安全库存', '采购价', '销售价', '库存状态']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    apply_excel_header_style(ws, 1, len(headers))

    for row_idx, product in enumerate(products, 2):
        stock = float(product.stock_quantity or 0)
        safety = float(product.safety_stock or 0)
        if stock <= 0:
            status = '零库存'
        elif stock <= safety:
            status = '低库存'
        else:
            status = '正常'

        ws.cell(row=row_idx, column=1, value=product.code).border = EXCEL_THIN_BORDER
        ws.cell(row=row_idx, column=2, value=product.name).border = EXCEL_THIN_BORDER
        ws.cell(row=row_idx, column=3, value=product.specification or '').border = EXCEL_THIN_BORDER
        ws.cell(row=row_idx, column=4, value=product.unit or '').border = EXCEL_THIN_BORDER
        ws.cell(row=row_idx, column=5, value=stock).border = EXCEL_THIN_BORDER
        ws.cell(row=row_idx, column=5).number_format = '#,##0.00'
        ws.cell(row=row_idx, column=6, value=safety).border = EXCEL_THIN_BORDER
        ws.cell(row=row_idx, column=6).number_format = '#,##0.00'
        ws.cell(row=row_idx, column=7, value=float(product.purchase_price or 0)).border = EXCEL_THIN_BORDER
        ws.cell(row=row_idx, column=7).number_format = '#,##0.00'
        ws.cell(row=row_idx, column=8, value=float(product.sale_price or 0)).border = EXCEL_THIN_BORDER
        ws.cell(row=row_idx, column=8).number_format = '#,##0.00'
        ws.cell(row=row_idx, column=9, value=status).border = EXCEL_THIN_BORDER

    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 8
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 12
    ws.column_dimensions['H'].width = 12
    ws.column_dimensions['I'].width = 10

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f'warehouse_stock_{warehouse.name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8''{quote(filename)}'
    return response


@bp.route('/logs')
@login_required
def stock_logs():
    """库存流水记录"""
    product_id = request.args.get('product_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    log_type = request.args.get('log_type')
    
    query = StockLog.query
    
    if product_id:
        query = query.filter_by(product_id=product_id)
    if start_date:
        query = query.filter(StockLog.created_at >= start_date)
    if end_date:
        query = query.filter(StockLog.created_at <= end_date + ' 23:59:59')
    if log_type:
        if log_type == 'check':
            query = query.filter(StockLog.change_type.like('check%'))
        elif log_type == 'adjust':
            query = query.filter(StockLog.change_type.like('adjust%'))
        elif log_type in VALID_LOG_TYPES:
            query = query.filter_by(change_type=log_type)

    logs = query.order_by(StockLog.created_at.desc()).limit(100).all()

    return render_template('inventory/logs.html',
                         title='库存流水',
                         logs=logs,
                         start_date=start_date or '',
                         end_date=end_date or '',
                         log_type=log_type or '')

@bp.route('/api/low-stock')
@login_required
def low_stock_api():
    """低库存预警API"""
    products = Product.query.filter(
        Product.safety_stock > 0,
        Product.stock_quantity <= Product.safety_stock
    ).all()
    
    result = [{
        'id': p.id,
        'code': p.code,
        'name': p.name,
        'stock_quantity': float(p.stock_quantity),
        'safety_stock': float(p.safety_stock),
        'unit': p.unit
    } for p in products]
    
    return jsonify(result)

@bp.route('/api/export-logs')
@login_required
def export_logs():
    """导出库存流水日志"""
    from flask import Response
    from openpyxl import Workbook
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    log_type = request.args.get('log_type')
    
    query = StockLog.query
    
    if start_date:
        query = query.filter(StockLog.created_at >= start_date)
    if end_date:
        query = query.filter(StockLog.created_at <= end_date + ' 23:59:59')
    if log_type:
        if log_type == 'check':
            query = query.filter(StockLog.change_type.like('check%'))
        elif log_type == 'adjust':
            query = query.filter(StockLog.change_type.like('adjust%'))
        elif log_type in VALID_LOG_TYPES:
            query = query.filter_by(change_type=log_type)

    logs = query.order_by(StockLog.created_at.desc()).limit(10000).all()

    # 创建Excel工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = '库存流水'
    
    # 写入表头
    headers = ['时间', '单号', '类型', '商品编码', '商品名称', '仓库', '数量', '操作前库存', '操作后库存', '操作人', '备注']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    apply_excel_header_style(ws, 1, len(headers))
    
    # 类型映射
    type_mapping = {
        'in': '入库',
        'out': '出库',
        'transfer': '调拨',
        'check_in': '盘点',
        'check_out': '盘点',
        'adjust_in': '调整',
        'adjust_out': '调整',
        'return_in': '退货入库',
        'return_out': '退货出库',
    }
    
    # 写入数据
    for row, log in enumerate(logs, 2):
        ws.cell(row=row, column=1, value=log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=2, value=log.reference_number or '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=3, value=type_mapping.get(log.change_type, log.change_type)).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=4, value=log.product.code if log.product else '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=5, value=log.product.name if log.product else '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=6, value=log.warehouse.name if log.warehouse else '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=7, value=float(log.quantity) if log.quantity else 0).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=8, value=float(log.before_quantity) if log.before_quantity else 0).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=9, value=float(log.after_quantity) if log.after_quantity else 0).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=10, value=log.creator.username if log.creator else '系统').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=11, value=log.notes or '').border = EXCEL_THIN_BORDER
    
    # 设置列宽
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 25
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 10
    ws.column_dimensions['H'].width = 12
    ws.column_dimensions['I'].width = 12
    ws.column_dimensions['J'].width = 12
    ws.column_dimensions['K'].width = 30
    
    # 保存到BytesIO
    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    from urllib.parse import quote
    filename = f'inventory_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename*=UTF-8\'\'{quote(filename)}'}
    )

@bp.route('/api/logs-statistics')
@login_required
def logs_statistics():
    """库存流水统计API"""
    from sqlalchemy import func
    
    stock_in_count = StockLog.query.filter_by(change_type='in').count()
    stock_out_count = StockLog.query.filter_by(change_type='out').count()
    transfer_count = StockLog.query.filter(
        StockLog.change_type.in_(['out', 'in']),
        StockLog.reference_type == 'stock_transfer'
    ).count()
    check_count = StockLog.query.filter(StockLog.change_type.like('check%')).count()
    
    return jsonify({
        'stock_in_count': stock_in_count,
        'stock_out_count': stock_out_count,
        'transfer_count': transfer_count,
        'check_count': check_count
    })

@bp.route('/api/stock-check', methods=['POST'])
@login_required
def api_stock_check():
    """库存盘点API"""
    try:
        data = request.get_json()
        
        check_data = data.get('check_data', [])
        check_date = data.get('check_date', datetime.now().strftime('%Y-%m-%d'))
        
        for item in check_data:
            product_id = item.get('product_id')
            actual_stock = item.get('actual_stock')
            remark = item.get('remark', '')
            warehouse_id = item.get('warehouse_id')

            try:
                product_id = int(product_id)
                actual_stock = float(actual_stock)
                warehouse_id = int(warehouse_id)
            except (TypeError, ValueError):
                continue

            if product_id and actual_stock is not None and warehouse_id:
                product = db.session.query(Product).filter(Product.id == product_id).with_for_update().first()
                if product:
                    warehouse_id = int(warehouse_id)
                    system_stock = to_decimal(product.stock_quantity)
                    new_stock = to_decimal(actual_stock)
                    
                    if system_stock != new_stock:
                        # 更新产品库存
                        product.stock_quantity = new_stock
                        
                        # 记录库存日志
                        diff = new_stock - system_stock
                        change_type = 'check_in' if diff > 0 else 'check_out'
                        
                        log = StockLog(
                            product_id=product.id,
                            warehouse_id=warehouse_id,
                            change_type=change_type,
                            quantity=abs(diff),
                            before_quantity=system_stock,
                            after_quantity=new_stock,
                            reference_type='stock_check',
                            notes=f'库存盘点: {remark}',
                            created_by=current_user.id
                        )
                        db.session.add(log)
        
        db.session.commit()
        return jsonify({'success': True, 'message': '盘点保存成功'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '盘点保存失败，请重试'}), 500

@bp.route('/stock-adjust', methods=['GET', 'POST'])
@login_required
def stock_adjust():
    """库存调整"""
    products = Product.query.all()
    products_data = [{
        'id': p.id,
        'code': p.code,
        'name': p.name,
        'specification': p.specification or '',
        'unit': p.unit,
        'stock_quantity': float(p.stock_quantity) if p.stock_quantity else 0,
        'purchase_price': float(p.purchase_price) if p.purchase_price else 0
    } for p in products]
    warehouses = Warehouse.query.all()
    warehouses_data = [{'id': w.id, 'code': w.code, 'name': w.name} for w in warehouses]

    form = StockAdjustForm()
    # 设置SelectField选项
    form.product_id.choices = [(p.id, f"{p.code} - {p.name}") for p in products]
    form.warehouse_id.choices = [(w.id, f"{w.code} - {w.name}") for w in warehouses]

    if form.validate_on_submit():
        try:
            product = db.session.query(Product).filter(Product.id == form.product_id.data).with_for_update().first()
            if product is None:
                abort(404)
            before_quantity = to_decimal(product.stock_quantity)
            quantity = to_decimal(form.quantity.data)

            if form.adjust_type.data == 'adjust_in':
                product.stock_quantity += quantity
                after_quantity = to_decimal(product.stock_quantity)
            elif form.adjust_type.data == 'adjust_out':
                if product.stock_quantity < quantity:
                    flash('库存不足，无法调整！', 'danger')
                    return render_template('inventory/stock_adjust.html',
                                         title='库存调整',
                                         form=form,
                                         products=products_data,
                                         warehouses=warehouses_data)
                product.stock_quantity -= quantity
                after_quantity = to_decimal(product.stock_quantity)
            else:
                flash('无效的调整类型！', 'danger')
                return render_template('inventory/stock_adjust.html',
                                     title='库存调整',
                                     form=form,
                                     products=products_data,
                                     warehouses=warehouses_data)

            log = StockLog(
                product_id=product.id,
                warehouse_id=form.warehouse_id.data,
                change_type=form.adjust_type.data,
                quantity=quantity,
                before_quantity=before_quantity,
                after_quantity=after_quantity,
                reference_type='stock_adjust',
                notes=form.notes.data or '',
                created_by=current_user.id
            )
            db.session.add(log)
            db.session.commit()

            flash('库存调整成功！', 'success')
            return redirect(url_for('inventory.product_list'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('调整失败，请重试', 'danger')

    return render_template('inventory/stock_adjust.html',
                         title='库存调整',
                         form=form,
                         products=products_data,
                         warehouses=warehouses_data)
