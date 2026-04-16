from flask import render_template, redirect, url_for, flash, request, jsonify, Blueprint
from flask_login import login_required, current_user
from app import db
from app.models import SalesOrder, SalesOrderItem, StockOut, StockOutItem, Customer, Warehouse, Product, StockLog, Log
from app.forms import SalesOrderForm, SalesOrderItemForm, StockOutForm
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
bp = Blueprint('sales', __name__, url_prefix='/sales')

# 销售管理 - 合并页面（订单 + 出库）
@bp.route('/')
@bp.route('/index')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    status = request.args.get('status', '')
    customer_id = request.args.get('customer_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    tab = request.args.get('tab', 'orders')

    # 获取销售订单
    order_query = SalesOrder.query

    if status:
        order_query = order_query.filter_by(status=status)

    if customer_id:
        order_query = order_query.filter_by(customer_id=customer_id)

    if start_date:
        order_query = order_query.filter(SalesOrder.order_date >= start_date)

    if end_date:
        order_query = order_query.filter(SalesOrder.order_date <= end_date)

    orders = order_query.order_by(SalesOrder.created_at.desc()).paginate(page=page, per_page=per_page)

    # 获取出库单
    stock_out_query = StockOut.query

    if warehouse_id:
        stock_out_query = stock_out_query.filter_by(warehouse_id=warehouse_id)

    if start_date:
        stock_out_query = stock_out_query.filter(StockOut.delivery_date >= start_date)

    if end_date:
        stock_out_query = stock_out_query.filter(StockOut.delivery_date <= end_date)

    stock_outs = stock_out_query.order_by(StockOut.created_at.desc()).paginate(page=page, per_page=per_page)

    customers = Customer.query.all()
    warehouses = Warehouse.query.all()

    return render_template('sales/index.html',
                         title='销售管理',
                         orders=orders,
                         stock_outs=stock_outs,
                         customers=customers,
                         warehouses=warehouses,
                         status=status,
                         customer_id=customer_id,
                         warehouse_id=warehouse_id,
                         start_date=start_date,
                         end_date=end_date)

# 新建销售订单
@bp.route('/orders/new', methods=['GET', 'POST'])
@login_required
def new_order():
    customers = Customer.query.all()
    customers_data = [{
        'id': c.id,
        'code': c.code,
        'name': c.name
    } for c in customers]
    warehouses = Warehouse.query.all()
    products = Product.query.all()
    products_data = [{
        'id': p.id,
        'code': p.code,
        'name': p.name,
        'specification': p.specification or '',
        'unit': p.unit,
        'sale_price': float(p.sale_price) if p.sale_price else 0,
        'stock_quantity': float(p.stock_quantity) if p.stock_quantity else 0
    } for p in products]
    
    if request.method == 'POST':
        # 获取表单数据
        customer_id = request.form.get('customer_id', type=int)
        warehouse_id = request.form.get('warehouse_id', type=int)
        order_date = request.form.get('order_date')
        delivery_date = request.form.get('delivery_date')
        notes = request.form.get('notes', '')
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        
        if not customer_id or not warehouse_id or not order_date:
            flash('请填写必填字段！', 'danger')
            return render_template('sales/order_items.html',
                                 title='新建销售订单',
                                 customers=customers_data,
                                 warehouses=warehouses,
                                 products=products_data,
                                 action='new')

        # 生成订单号
        today = datetime.now().strftime('%Y%m%d')
        last_order = SalesOrder.query.filter(SalesOrder.order_number.like(f'SO{today}%')).order_by(SalesOrder.id.desc()).first()
        if last_order:
            last_num = int(last_order.order_number[10:]) if len(last_order.order_number) > 10 else 0
            order_number = f'SO{today}{last_num + 1:03d}'
        else:
            order_number = f'SO{today}001'

        order = SalesOrder(
            order_number=order_number,
            customer_id=customer_id,
            warehouse_id=warehouse_id,
            order_date=datetime.strptime(order_date, '%Y-%m-%d').date(),
            delivery_date=datetime.strptime(delivery_date, '%Y-%m-%d').date() if delivery_date else None,
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
                    item = SalesOrderItem(
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

        flash('销售订单创建成功！', 'success')

        db.session.commit()
        return redirect(url_for('sales.index'))

    return render_template('sales/order_items.html',
                         title='新建销售订单',
                         customers=customers_data,
                         warehouses=warehouses,
                         products=products_data,
                         action='new')

# 编辑订单基本信息
@bp.route('/orders/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_order(id):
    order = SalesOrder.query.get_or_404(id)
    
    if order.status == 'completed':
        flash('已完成的订单不能修改！', 'danger')
        return redirect(url_for('sales.index', tab=get_redirect_tab()))
    
    customers = Customer.query.all()
    customers_data = [{
        'id': c.id,
        'code': c.code,
        'name': c.name
    } for c in customers]
    warehouses = Warehouse.query.all()
    products = Product.query.all()
    products_data = [{
        'id': p.id,
        'code': p.code,
        'name': p.name,
        'specification': p.specification or '',
        'unit': p.unit,
        'sale_price': float(p.sale_price) if p.sale_price else 0,
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
        customer_id = request.form.get('customer_id', type=int)
        warehouse_id = request.form.get('warehouse_id', type=int)
        order_date = request.form.get('order_date')
        delivery_date = request.form.get('delivery_date')
        notes = request.form.get('notes', '')
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        
        if not customer_id or not warehouse_id or not order_date:
            flash('请填写必填字段！', 'danger')
            return render_template('sales/order_items.html',
                                 title='编辑销售订单',
                                 order=order,
                                 customers=customers_data,
                                 warehouses=warehouses,
                                 products=products_data,
                                 order_items=order_items_data,
                                 action='edit')
        
        # 更新订单基本信息
        order.customer_id = customer_id
        order.warehouse_id = warehouse_id
        order.order_date = datetime.strptime(order_date, '%Y-%m-%d').date()
        order.delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d').date() if delivery_date else None
        order.notes = notes
        
        # 更新商品明细
        SalesOrderItem.query.filter_by(order_id=order.id).delete()
        
        total_amount = 0
        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_prices[i]:
                product = Product.query.get(int(product_ids[i]))
                if product:
                    quantity = float(quantities[i])
                    unit_price = float(unit_prices[i])
                    amount = quantity * unit_price
                    item = SalesOrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        amount=amount
                    )
                    db.session.add(item)
                    total_amount += amount
        
        order.total_amount = total_amount
        
        db.session.commit()
        flash('销售订单修改成功！', 'success')
        return redirect(url_for('sales.index', tab=get_redirect_tab()))
    
    return render_template('sales/order_items.html',
                         title='编辑销售订单',
                         order=order,
                         customers=customers_data,
                         warehouses=warehouses,
                         products=products_data,
                         order_items=order_items_data,
                         action='edit')

# 保留旧路由用于兼容，重定向到 edit_order
@bp.route('/orders/<int:id>/items')
@login_required
def edit_order_items(id):
    return redirect(url_for('sales.edit_order', id=id))

# 删除订单
@bp.route('/orders/<int:id>/delete', methods=['POST'])
@login_required
def delete_order(id):
    order = SalesOrder.query.get_or_404(id)
    
    # 检查是否有关联的发货单
    if order.stock_outs:
        flash('此订单有关联的发货单，无法删除！', 'danger')
        return redirect(url_for('sales.index'))
    
    db.session.delete(order)
    db.session.commit()
    
    flash('销售订单删除成功！', 'success')
    return redirect(url_for('sales.index'))

# 查看订单详情
@bp.route('/orders/<int:id>')
@login_required
def view_order(id):
    order = SalesOrder.query.get_or_404(id)
    related_stock_outs = StockOut.query.filter_by(sales_order_id=id).order_by(StockOut.created_at.desc()).all()
    
    # 准备订单商品数据用于JavaScript确认框
    order_items_data = []
    for item in order.items:
        remaining = float(item.quantity) - float(item.delivered_quantity)
        if remaining > 0:
            order_items_data.append({
                'name': item.product.name,
                'remaining': round(remaining, 2),
                'unit': item.product.unit
            })
    
    return render_template('sales/order_view.html',
                         title='销售订单详情',
                         order=order,
                         related_stock_outs=related_stock_outs,
                         order_items_data=order_items_data)

# 从销售订单创建出库单（直接出库）
@bp.route('/orders/<int:id>/stock-out', methods=['GET', 'POST'])
@login_required
def new_stock_out_from_order(id):
    order = SalesOrder.query.get_or_404(id)
    
    if order.status not in ['confirmed', 'partial']:
        flash('只有已确认或部分出库的订单可以创建出库单！', 'danger')
        return redirect(url_for('sales.view_order', id=id))
    
    # 生成出库单号
    today = datetime.now().strftime('%Y%m%d')
    last_stock_out = StockOut.query.filter(StockOut.delivery_number.like(f'OUT{today}%')).order_by(StockOut.id.desc()).first()
    if last_stock_out:
        last_num = int(last_stock_out.delivery_number[11:]) if len(last_stock_out.delivery_number) > 11 else 0
        delivery_number = f'OUT{today}{last_num + 1:03d}'
    else:
        delivery_number = f'OUT{today}001'
    
    # 创建出库单，预填销售订单信息
    stock_out = StockOut(
        delivery_number=delivery_number,
        sales_order_id=order.id,
        warehouse_id=order.warehouse_id,
        delivery_date=datetime.now().date(),
        handler=current_user.username,
        notes=f'从销售订单 {order.order_number} 创建出库单',
        created_by=current_user.id,
        status='pending'
    )
    
    db.session.add(stock_out)
    
    # 添加订单中未出库的商品明细
    total_amount = 0
    for order_item in order.items:
        remaining_qty = float(order_item.quantity) - float(order_item.delivered_quantity)
        if remaining_qty > 0:
            unit_price = float(order_item.unit_price)
            amount = remaining_qty * unit_price
            stock_out_item = StockOutItem(
                stock_out_id=stock_out.id,
                product_id=order_item.product_id,
                quantity=remaining_qty,
                unit_price=unit_price,
                amount=amount
            )
            db.session.add(stock_out_item)
            # 同步更新商品销价
            order_item.product.sale_price = unit_price
            total_amount += amount
    
    stock_out.total_amount = total_amount
    db.session.commit()
    
    flash(f'出库单 {delivery_number} 创建成功！请编辑出库明细后完成出库。', 'success')
    return redirect(url_for('sales.edit_stock_out_items', id=stock_out.id))

# 新建出库单
@bp.route('/stock-outs/new', methods=['GET', 'POST'])
@login_required
def new_stock_out():
    form = StockOutForm()
    form.sales_order_id.choices = [(0, '直接出库')] + [(o.id, f"{o.order_number} - {o.customer.name}") 
                                                      for o in SalesOrder.query.filter_by(status='confirmed').all()]
    form.warehouse_id.choices = [(w.id, f"{w.code} - {w.name}") for w in Warehouse.query.all()]
    
    # 默认出库日期为今天
    if request.method == 'GET':
        form.delivery_date.data = datetime.now().date()
        form.handler.data = current_user.username
    
    if form.validate_on_submit():
        # 生成出库单号
        today = datetime.now().strftime('%Y%m%d')
        last_stock_out = StockOut.query.filter(StockOut.delivery_number.like(f'OUT{today}%')).order_by(StockOut.id.desc()).first()
        if last_stock_out:
            last_num = int(last_stock_out.delivery_number[11:]) if len(last_stock_out.delivery_number) > 11 else 0
            delivery_number = f'OUT{today}{last_num + 1:03d}'
        else:
            delivery_number = f'OUT{today}001'
        
        stock_out = StockOut(
            delivery_number=delivery_number,
            sales_order_id=form.sales_order_id.data if form.sales_order_id.data != 0 else None,
            warehouse_id=form.warehouse_id.data,
            delivery_date=form.delivery_date.data,
            handler=form.handler.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        
        db.session.add(stock_out)
        db.session.commit()
        
        flash('出库单创建成功！请添加商品明细。', 'success')
        return redirect(url_for('sales.edit_stock_out_items', id=stock_out.id))
    
    return render_template('sales/stock_out_edit.html', 
                         title='新建出库单',
                         form=form,
                         action='new')

# 编辑出库明细
@bp.route('/stock-outs/<int:id>/items', methods=['GET', 'POST'])
@login_required
def edit_stock_out_items(id):
    stock_out = StockOut.query.get_or_404(id)
    
    if request.method == 'POST':
        # 处理商品明细
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        
        # 删除原有明细
        StockOutItem.query.filter_by(stock_out_id=stock_out.id).delete()
        
        total_amount = 0
        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_prices[i]:
                product = Product.query.get(int(product_ids[i]))
                if product:
                    quantity = float(quantities[i])
                    unit_price = float(unit_prices[i])
                    amount = quantity * unit_price
                    
                    item = StockOutItem(
                        stock_out_id=stock_out.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        amount=amount
                    )
                    db.session.add(item)
                    total_amount += amount
        
        stock_out.total_amount = total_amount
        db.session.commit()
        
        flash('商品明细保存成功！', 'success')
        return redirect(url_for('sales.index', tab='stockouts'))
    
    products = Product.query.all()
    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'code': product.code,
            'name': product.name,
            'specification': product.specification or '',
            'unit': product.unit,
            'sale_price': float(product.sale_price) if product.sale_price else 0,
            'stock_quantity': float(product.stock_quantity) if product.stock_quantity else 0
        })
    
    return render_template('sales/stock_out_items.html', 
                         title='编辑出库明细',
                         stock_out=stock_out,
                         products=products_data)

# 完成出库
@bp.route('/stock-outs/<int:id>/complete', methods=['POST'])
@login_required
def complete_stock_out(id):
    stock_out = StockOut.query.get_or_404(id)
    
    # 检查是否已经完成
    if stock_out.status == 'completed':
        flash('此出库单已经完成，不能重复确认！', 'danger')
        return redirect(url_for('sales.index', tab='stockouts'))
    
    if len(stock_out.items) == 0:
        flash('请先添加商品明细！', 'danger')
        return redirect(url_for('sales.edit_stock_out_items', id=stock_out.id))
    
    # 开始事务
    try:
        # 检查库存是否充足
        insufficient_stock = []
        
        for item in stock_out.items:
            product = item.product
            warehouse = stock_out.warehouse
            
            if product.stock_quantity < item.quantity:
                insufficient_stock.append(f"{product.code} - {product.name} (库存: {product.stock_quantity}, 需求: {item.quantity})")
        
        if insufficient_stock:
            flash(f'库存不足: {", ".join(insufficient_stock)}', 'danger')
            return redirect(url_for('sales.index', tab='stockouts'))
        
        # 更新库存和记录流水
        for item in stock_out.items:
            product = item.product
            warehouse = stock_out.warehouse
            
            before_quantity = float(product.stock_quantity)
            after_quantity = before_quantity - float(item.quantity)
            product.stock_quantity = after_quantity
            
            # 记录库存流水
            log = StockLog(
                product_id=product.id,
                warehouse_id=warehouse.id,
                change_type='out',
                quantity=item.quantity,
                before_quantity=before_quantity,
                after_quantity=product.stock_quantity,
                reference_id=stock_out.id,
                reference_type='stock_out',
                notes=f'销售出库: {stock_out.delivery_number}',
                created_by=current_user.id
            )
            db.session.add(log)
        
        # 如果有关联销售订单，重新计算已出库数量（基于所有已完成出库单）
        if stock_out.sales_order:
            order = stock_out.sales_order
            for order_item in order.items:
                total_delivered = sum(
                    so_item.quantity
                    for so in order.stock_outs
                    if so.status == 'completed'
                    for so_item in so.items
                    if so_item.product_id == order_item.product_id
                )
                order_item.delivered_quantity = total_delivered
            
            # 检查订单是否全部出库
            all_delivered = all(
                oi.delivered_quantity >= oi.quantity
                for oi in order.items
            )
            
            if all_delivered:
                order.status = 'completed'
                # 更新客户应收余额（出库增加应收）
                customer = order.customer
                if customer:
                    customer.receivable_balance = float(customer.receivable_balance) + float(order.total_amount)
            else:
                order.status = 'partial'
        
        # 更新出库单状态为已完成
        stock_out.status = 'completed'
        stock_out.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('出库单完成！库存已更新。', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'出库失败: {str(e)}', 'danger')
    
    return redirect(url_for('sales.index', tab='stockouts'))

# 删除出库单
@bp.route('/stock-outs/<int:id>/delete', methods=['POST'])
@login_required
def delete_stock_out(id):
    stock_out = StockOut.query.get_or_404(id)
    
    # 只有未出库状态的出库单可以删除
    if stock_out.status != 'pending':
        flash('只有未出库状态的出库单可以删除！', 'danger')
        return redirect(url_for('sales.index', tab='stockouts'))
    
    db.session.delete(stock_out)
    db.session.commit()
    
    flash('出库单删除成功！', 'success')
    return redirect(url_for('sales.index', tab='stockouts'))

# 查看出库单详情
@bp.route('/stock-outs/<int:id>')
@login_required
def view_stock_out(id):
    stock_out = StockOut.query.get_or_404(id)
    return render_template('sales/stock_out_view.html', 
                         title='出库单详情',
                         stock_out=stock_out)

# API接口
@bp.route('/api/sales-orders/<int:order_id>/items')
@login_required
def api_order_items(order_id):
    order = SalesOrder.query.get_or_404(order_id)
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
            'delivered_quantity': float(item.delivered_quantity)
        })
    return jsonify(items)
