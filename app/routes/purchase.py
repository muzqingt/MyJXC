from flask import render_template, redirect, url_for, flash, request, jsonify, Blueprint
from flask_login import login_required, current_user
from app import db
from app.models import PurchaseOrder, PurchaseOrderItem, StockIn, StockInItem, Supplier, Warehouse, Product, StockLog, Log
from app.forms import PurchaseOrderForm, PurchaseOrderItemForm, StockInForm
from datetime import datetime
import urllib.parse

def get_redirect_tab():
    """从referer获取当前tab，默认返回orders"""
    referer = request.referrer
    if referer:
        parsed = urllib.parse.urlparse(referer)
        query_params = urllib.parse.parse_qs(parsed.query)
        if 'tab' in query_params:
            return query_params['tab'][0]
    return 'orders'

# 创建蓝图
bp = Blueprint('purchase', __name__, url_prefix='/purchase')

# 采购管理 - 合并页面（订单 + 入库）
@bp.route('/')
@bp.route('/index')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    status = request.args.get('status', '')
    supplier_id = request.args.get('supplier_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    tab = request.args.get('tab', 'orders')
    
    # 获取采购订单
    order_query = PurchaseOrder.query
    
    if status:
        order_query = order_query.filter_by(status=status)
    
    if supplier_id:
        order_query = order_query.filter_by(supplier_id=supplier_id)
    
    if start_date:
        order_query = order_query.filter(PurchaseOrder.order_date >= start_date)
    
    if end_date:
        order_query = order_query.filter(PurchaseOrder.order_date <= end_date)
    
    orders = order_query.order_by(PurchaseOrder.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # 获取入库单
    stock_in_query = StockIn.query
    
    if warehouse_id:
        stock_in_query = stock_in_query.filter_by(warehouse_id=warehouse_id)
    
    if start_date:
        stock_in_query = stock_in_query.filter(StockIn.receipt_date >= start_date)
    
    if end_date:
        stock_in_query = stock_in_query.filter(StockIn.receipt_date <= end_date)
    
    stock_ins = stock_in_query.order_by(StockIn.created_at.desc()).paginate(page=page, per_page=per_page)
    
    suppliers = Supplier.query.all()
    warehouses = Warehouse.query.all()
    
    return render_template('purchase/index.html', 
                         title='采购管理',
                         orders=orders,
                         stock_ins=stock_ins,
                         suppliers=suppliers,
                         warehouses=warehouses,
                         status=status,
                         supplier_id=supplier_id,
                         warehouse_id=warehouse_id,
                         start_date=start_date,
                         end_date=end_date)

@bp.route('/orders/new', methods=['GET', 'POST'])
@login_required
def new_order():
    suppliers = Supplier.query.all()
    suppliers_data = [{
        'id': s.id,
        'code': s.code,
        'name': s.name
    } for s in suppliers]
    warehouses = Warehouse.query.all()
    products = Product.query.all()
    products_data = [{
        'id': p.id,
        'code': p.code,
        'name': p.name,
        'specification': p.specification or '',
        'unit': p.unit,
        'purchase_price': float(p.purchase_price) if p.purchase_price else 0,
        'stock_quantity': float(p.stock_quantity) if p.stock_quantity else 0
    } for p in products]
    
    if request.method == 'POST':
        action = request.form.get('action', 'save')
        
        # 获取表单数据
        supplier_id = request.form.get('supplier_id', type=int)
        warehouse_id = request.form.get('warehouse_id', type=int)
        order_date = request.form.get('order_date')
        expected_date = request.form.get('expected_date')
        notes = request.form.get('notes', '')
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        
        if not supplier_id or not warehouse_id or not order_date:
            flash('请填写必填字段！', 'danger')
            # 重建商品明细数据（用于回填）
            order_items_list = []
            for i in range(len(product_ids)):
                if product_ids[i] and quantities[i] and unit_prices[i]:
                    product = Product.query.get(int(product_ids[i]))
                    if product:
                        order_items_list.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'product_code': product.code,
                            'quantity': quantities[i],
                            'unit_price': unit_prices[i]
                        })
            return render_template('purchase/order_items.html',
                                 title='新建采购订单',
                                 suppliers=suppliers_data,
                                 warehouses=warehouses,
                                 products=products_data,
                                 action='new',
                                 submitted_supplier_id=supplier_id,
                                 submitted_warehouse_id=warehouse_id,
                                 submitted_order_date=order_date,
                                 submitted_expected_date=expected_date,
                                 submitted_notes=notes,
                                 orderItems=order_items_list)
        
        # 生成订单号
        today = datetime.now().strftime('%Y%m%d')
        last_order = PurchaseOrder.query.filter(PurchaseOrder.order_number.like(f'PO{today}%')).order_by(PurchaseOrder.id.desc()).first()
        if last_order:
            last_num = int(last_order.order_number[10:]) if len(last_order.order_number) > 10 else 0
            order_number = f'PO{today}{last_num + 1:03d}'
        else:
            order_number = f'PO{today}001'
        
        order = PurchaseOrder(
            order_number=order_number,
            supplier_id=supplier_id,
            warehouse_id=warehouse_id,
            order_date=datetime.strptime(order_date, '%Y-%m-%d').date(),
            expected_date=datetime.strptime(expected_date, '%Y-%m-%d').date() if expected_date else None,
            notes=notes,
            created_by=current_user.id,
            status='confirmed'
        )
        
        db.session.add(order)
        db.session.flush()  # Get order.id
        
        total_amount = 0
        order_items_list = []
        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_prices[i]:
                product = Product.query.get(int(product_ids[i]))
                if product:
                    quantity = float(quantities[i])
                    unit_price = float(unit_prices[i])
                    amount = quantity * unit_price
                    item = PurchaseOrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        amount=amount
                    )
                    db.session.add(item)
                    total_amount += amount
                    order_items_list.append({
                        'product': product,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'amount': amount
                    })
        
        order.total_amount = total_amount
        
        flash('采购订单创建成功！', 'success')
        
        db.session.commit()
        return redirect(url_for('purchase.index', tab=get_redirect_tab()))
    
    return render_template('purchase/order_items.html', 
                         title='新建采购订单',
                         suppliers=suppliers_data,
                         warehouses=warehouses,
                         products=products_data,
                         action='new')

@bp.route('/orders/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_order(id):
    order = PurchaseOrder.query.get_or_404(id)
    
    if order.status == 'completed':
        flash('已完成的订单不能修改！', 'danger')
        return redirect(url_for('purchase.index', tab=get_redirect_tab()))
    
    suppliers = Supplier.query.all()
    suppliers_data = [{
        'id': s.id,
        'code': s.code,
        'name': s.name
    } for s in suppliers]
    warehouses = Warehouse.query.all()
    products = Product.query.all()
    products_data = [{
        'id': p.id,
        'code': p.code,
        'name': p.name,
        'specification': p.specification or '',
        'unit': p.unit,
        'purchase_price': float(p.purchase_price) if p.purchase_price else 0,
        'stock_quantity': float(p.stock_quantity) if p.stock_quantity else 0
    } for p in products]
    
    # 订单商品明细
    order_items_data = []
    for item in order.items:
        order_items_data.append({
            'product_id': item.product_id,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price)
        })
    
    if request.method == 'POST':
        action = request.form.get('action', 'save')
        
        # 获取表单数据
        supplier_id = request.form.get('supplier_id', type=int)
        warehouse_id = request.form.get('warehouse_id', type=int)
        order_date = request.form.get('order_date')
        expected_date = request.form.get('expected_date')
        notes = request.form.get('notes', '')
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        
        if not supplier_id or not warehouse_id or not order_date:
            flash('请填写必填字段！', 'danger')
            # 重建商品明细数据（用于回填）
            order_items_list = []
            for i in range(len(product_ids)):
                if product_ids[i] and quantities[i] and unit_prices[i]:
                    product = Product.query.get(int(product_ids[i]))
                    if product:
                        order_items_list.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'product_code': product.code,
                            'quantity': quantities[i],
                            'unit_price': unit_prices[i]
                        })
            return render_template('purchase/order_items.html',
                                 title='编辑采购订单',
                                 order=order,
                                 suppliers=suppliers_data,
                                 warehouses=warehouses,
                                 products=products_data,
                                 action='edit',
                                 submitted_supplier_id=supplier_id,
                                 submitted_warehouse_id=warehouse_id,
                                 submitted_order_date=order_date,
                                 submitted_expected_date=expected_date,
                                 submitted_notes=notes,
                                 orderItems=order_items_list)
        
        # 更新订单基本信息
        order.supplier_id = supplier_id
        order.warehouse_id = warehouse_id
        order.order_date = datetime.strptime(order_date, '%Y-%m-%d').date()
        order.expected_date = datetime.strptime(expected_date, '%Y-%m-%d').date() if expected_date else None
        order.notes = notes
        
        # 更新商品明细
        PurchaseOrderItem.query.filter_by(order_id=order.id).delete()
        
        total_amount = 0
        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_prices[i]:
                product = Product.query.get(int(product_ids[i]))
                if product:
                    quantity = float(quantities[i])
                    unit_price = float(unit_prices[i])
                    amount = quantity * unit_price
                    item = PurchaseOrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        amount=amount
                    )
                    db.session.add(item)
                    total_amount += amount
        
        order.total_amount = total_amount
        
        if action == 'confirm':
            if len(product_ids) == 0 or total_amount == 0:
                flash('请先添加商品明细！', 'danger')
                db.session.rollback()
                return render_template('purchase/order_items.html',
                                     title='编辑采购订单',
                                     order=order,
                                     suppliers=suppliers_data,
                                     warehouses=warehouses,
                                     products=products_data,
                                     order_items=order_items_data,
                                     action='edit')
        
        db.session.commit()
        
        flash('采购订单修改成功！', 'success')
        return redirect(url_for('purchase.index', tab=get_redirect_tab()))
    
    return render_template('purchase/order_items.html', 
                         title='编辑采购订单',
                         order=order,
                         suppliers=suppliers_data,
                         warehouses=warehouses,
                         products=products_data,
                         order_items=order_items_data,
                         action='edit')

# 保留旧路由用于兼容，重定向到 edit_order
@bp.route('/orders/<int:id>/items')
@login_required
def edit_order_items(id):
    return redirect(url_for('purchase.edit_order', id=id))

@bp.route('/orders/<int:id>/delete', methods=['POST'])
@login_required
def delete_order(id):
    order = PurchaseOrder.query.get_or_404(id)
    
    # 检查是否有关联的入库单
    if order.stock_ins:
        flash('此订单有关联的入库单，无法删除！', 'danger')
        return redirect(url_for('purchase.index', tab=get_redirect_tab()))
    
    # 检查是否有库存流水记录
    from app.models import StockLog
    if StockLog.query.filter_by(reference_type='purchase_order', reference_id=order.id).first():
        flash('此订单已有库存操作记录，无法删除！', 'danger')
        return redirect(url_for('purchase.index', tab=get_redirect_tab()))
    
    db.session.delete(order)
    db.session.commit()
    flash('采购订单删除成功！', 'success')
    return redirect(url_for('purchase.index', tab=get_redirect_tab()))

@bp.route('/orders/<int:id>')
@login_required
def view_order(id):
    order = PurchaseOrder.query.get_or_404(id)
    related_stock_ins = StockIn.query.filter_by(purchase_order_id=id).order_by(StockIn.created_at.desc()).all()
    
    # 准备订单商品数据用于JavaScript确认框
    order_items_data = []
    for item in order.items:
        remaining = float(item.quantity) - float(item.received_quantity)
        if remaining > 0:
            order_items_data.append({
                'name': item.product.name,
                'remaining': round(remaining, 2),
                'unit': item.product.unit
            })
    
    return render_template('purchase/order_view.html', 
                         title='采购订单详情',
                         order=order,
                         related_stock_ins=related_stock_ins,
                         order_items_data=order_items_data)

# 从采购订单直接创建入库单（直接入库）
@bp.route('/orders/<int:id>/stock-in', methods=['GET', 'POST'])
@login_required
def new_stock_in_from_order(id):
    order = PurchaseOrder.query.get_or_404(id)
    
    if order.status not in ['confirmed', 'partial']:
        flash('只有已确认或部分入库的订单可以入库！', 'danger')
        return redirect(url_for('purchase.view_order', id=id))
    
    # 生成入库单号
    today = datetime.now().strftime('%Y%m%d')
    last_stock_in = StockIn.query.filter(StockIn.receipt_number.like(f'SI{today}%')).order_by(StockIn.id.desc()).first()
    if last_stock_in:
        last_num = int(last_stock_in.receipt_number[10:]) if len(last_stock_in.receipt_number) > 10 else 0
        receipt_number = f'SI{today}{last_num + 1:03d}'
    else:
        receipt_number = f'SI{today}001'
    
    # 创建入库单，预填采购订单信息
    stock_in = StockIn(
        receipt_number=receipt_number,
        purchase_order_id=order.id,
        warehouse_id=order.warehouse_id,
        receipt_date=datetime.now().date(),  # 默认入库时间为今天
        handler=current_user.username,  # 经办人为当前账号
        notes=f'从采购订单 {order.order_number} 创建入库单',
        created_by=current_user.id,
        status='pending'
    )
    
    db.session.add(stock_in)
    
    # 添加订单中未入库的商品明细
    total_amount = 0
    for order_item in order.items:
        remaining_qty = float(order_item.quantity) - float(order_item.received_quantity)
        if remaining_qty > 0:
            unit_price = float(order_item.unit_price)
            amount = remaining_qty * unit_price
            stock_in_item = StockInItem(
                stock_in_id=stock_in.id,
                product_id=order_item.product_id,
                quantity=remaining_qty,
                unit_price=unit_price,
                amount=amount
            )
            db.session.add(stock_in_item)
            # 同步更新商品进价
            order_item.product.purchase_price = unit_price
            total_amount += amount
    
    stock_in.total_amount = total_amount
    db.session.commit()
    
    flash(f'入库单 {receipt_number} 创建成功！请编辑入库明细后完成入库。', 'success')
    return redirect(url_for('purchase.edit_stock_in_items', id=stock_in.id))

@bp.route('/stock-ins/new', methods=['GET', 'POST'])
@login_required
def new_stock_in():
    form = StockInForm()
    form.purchase_order_id.choices = [(0, '直接入库')] + [(o.id, f"{o.order_number} - {o.supplier.name}") 
                                                         for o in PurchaseOrder.query.filter_by(status='confirmed').all()]
    form.warehouse_id.choices = [(w.id, f"{w.code} - {w.name}") for w in Warehouse.query.all()]
    
    # 默认入库日期为今天
    if request.method == 'GET':
        form.receipt_date.data = datetime.now().date()
        form.handler.data = current_user.username
    
    if form.validate_on_submit():
        # 生成入库单号
        today = datetime.now().strftime('%Y%m%d')
        last_stock_in = StockIn.query.filter(StockIn.receipt_number.like(f'SI{today}%')).order_by(StockIn.id.desc()).first()
        if last_stock_in:
            last_num = int(last_stock_in.receipt_number[10:]) if len(last_stock_in.receipt_number) > 10 else 0
            receipt_number = f'SI{today}{last_num + 1:03d}'
        else:
            receipt_number = f'SI{today}001'
        
        stock_in = StockIn(
            receipt_number=receipt_number,
            purchase_order_id=form.purchase_order_id.data if form.purchase_order_id.data != 0 else None,
            warehouse_id=form.warehouse_id.data,
            receipt_date=form.receipt_date.data,
            handler=form.handler.data,
            notes=form.notes.data,
            created_by=current_user.id,
            status='pending'
        )
        
        db.session.add(stock_in)
        db.session.commit()
        
        flash('入库单创建成功！请添加商品明细。', 'success')
        return redirect(url_for('purchase.edit_stock_in_items', id=stock_in.id))
    
    return render_template('purchase/stock_in_edit.html', 
                         title='新建入库单',
                         form=form,
                         action='new')

@bp.route('/stock-ins/<int:id>/items', methods=['GET', 'POST'])
@login_required
def edit_stock_in_items(id):
    stock_in = StockIn.query.get_or_404(id)
    
    if request.method == 'POST':
        # 处理商品明细
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        
        # 删除原有明细
        StockInItem.query.filter_by(stock_in_id=stock_in.id).delete()
        
        total_amount = 0
        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_prices[i]:
                product = Product.query.get(int(product_ids[i]))
                if product:
                    quantity = float(quantities[i])
                    unit_price = float(unit_prices[i])
                    amount = quantity * unit_price
                    
                    item = StockInItem(
                        stock_in_id=stock_in.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        amount=amount
                    )
                    db.session.add(item)
                    total_amount += amount
        
        stock_in.total_amount = total_amount
        db.session.commit()
        
        flash('商品明细保存成功！', 'success')
        return redirect(url_for('purchase.index', tab='stockins'))
    
    products = Product.query.all()
    # Convert products to dictionaries for JSON serialization
    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'code': product.code,
            'name': product.name,
            'specification': product.specification or '',
            'unit': product.unit,
            'purchase_price': float(product.purchase_price) if product.purchase_price else 0,
            'stock_quantity': float(product.stock_quantity) if product.stock_quantity else 0
        })
    
    # 获取采购订单的商品信息和剩余未入库数量
    order_items_data = []
    if stock_in.purchase_order:
        for order_item in stock_in.purchase_order.items:
            remaining_qty = float(order_item.quantity) - float(order_item.received_quantity)
            order_items_data.append({
                'product_id': order_item.product_id,
                'product_code': order_item.product.code,
                'product_name': order_item.product.name,
                'specification': order_item.product.specification or '',
                'unit': order_item.product.unit,
                'order_quantity': float(order_item.quantity),
                'received_quantity': float(order_item.received_quantity),
                'remaining_quantity': remaining_qty,
                'unit_price': float(order_item.unit_price)
            })
    
    return render_template('purchase/stock_in_items.html', 
                         title='编辑入库明细',
                         stock_in=stock_in,
                         products=products_data,
                         order_items=order_items_data)

@bp.route('/stock-ins/<int:id>/complete', methods=['POST'])
@login_required
def complete_stock_in(id):
    stock_in = StockIn.query.get_or_404(id)
    
    # 检查是否已经完成
    if stock_in.status == 'completed':
        flash('此入库单已经完成，不能重复确认！', 'danger')
        return redirect(url_for('purchase.index', tab='stockins'))
    
    # 检查状态是否为未入库
    if stock_in.status != 'pending':
        flash('此入库单状态异常，无法确认！', 'danger')
        return redirect(url_for('purchase.index', tab='stockins'))
    
    if len(stock_in.items) == 0:
        flash('请先添加商品明细！', 'danger')
        return redirect(url_for('purchase.edit_stock_in_items', id=stock_in.id))
    
    # 开始事务
    try:
        # 更新库存和记录流水
        for item in stock_in.items:
            product = item.product
            warehouse = stock_in.warehouse
            
            # 记录当前库存（更新前）
            before_quantity = product.stock_quantity
            
            # 更新商品库存
            before_quantity = float(product.stock_quantity)
            after_quantity = before_quantity + float(item.quantity)
            product.stock_quantity = after_quantity
            
            # 记录库存流水
            log = StockLog(
                product_id=product.id,
                warehouse_id=warehouse.id,
                change_type='in',
                quantity=item.quantity,
                before_quantity=before_quantity,
                after_quantity=product.stock_quantity,
                reference_id=stock_in.id,
                reference_type='stock_in',
                notes=f'采购入库: {stock_in.receipt_number}',
                created_by=current_user.id
            )
            db.session.add(log)
        
        # 如果有关联采购订单，重新计算已入库数量（基于所有已完成入库单）
        if stock_in.purchase_order:
            order = stock_in.purchase_order
            for order_item in order.items:
                total_received = sum(
                    si_item.quantity
                    for si in order.stock_ins
                    if si.status == 'completed'
                    for si_item in si.items
                    if si_item.product_id == order_item.product_id
                )
                order_item.received_quantity = total_received
            
            # 检查订单是否全部入库
            all_received = all(
                oi.received_quantity >= oi.quantity
                for oi in order.items
            )
            
            if all_received:
                order.status = 'completed'
                # 更新供应商应付余额（入库增加应付）
                supplier = order.supplier
                if supplier:
                    supplier.payable_balance = float(supplier.payable_balance) + float(order.total_amount)
            else:
                order.status = 'partial'
        
        # 更新入库单状态为已完成
        stock_in.status = 'completed'
        stock_in.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('入库单完成！库存已更新。', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'入库失败: {str(e)}', 'danger')
    
    return redirect(url_for('purchase.index', tab='stockins'))

@bp.route('/stock-ins/<int:id>/delete', methods=['POST'])
@login_required
def delete_stock_in(id):
    stock_in = StockIn.query.get_or_404(id)
    
    # 只有未入库状态的入库单可以删除
    if stock_in.status != 'pending':
        flash('只有未入库状态的入库单可以删除！', 'danger')
        return redirect(url_for('purchase.index', tab='stockins'))
    
    db.session.delete(stock_in)
    db.session.commit()
    
    flash('入库单删除成功！', 'success')
    return redirect(url_for('purchase.index', tab='stockins'))

@bp.route('/stock-ins/<int:id>')
@login_required
def view_stock_in(id):
    stock_in = StockIn.query.get_or_404(id)
    return render_template('purchase/stock_in_view.html', 
                         title='入库单详情',
                         stock_in=stock_in)

# API接口
@bp.route('/api/purchase-orders/<int:order_id>/items')
@login_required
def api_order_items(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    items = []
    for item in order.items:
        items.append({
            'product_id': item.product_id,
            'product_code': item.product.code,
            'product_name': item.product.name,
            'specification': item.product.specification,
            'unit': item.product.unit,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'amount': float(item.amount),
            'received_quantity': float(item.received_quantity)
        })
    return jsonify(items)
