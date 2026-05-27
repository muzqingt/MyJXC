from flask import render_template, redirect, url_for, flash, request, jsonify, Blueprint, abort
from flask_login import login_required, current_user
from app import db
from sqlalchemy.orm import selectinload
from app.models import SalesOrder, SystemSetting, SalesOrderItem, StockOut, StockOutItem, Customer, Warehouse, Product, StockLog, SalesReturn, SalesReturnItem
from app.utils import to_decimal, add_balance, sub_balance, get_redirect_tab, build_products_data, build_partners_data, generate_order_number
from app.forms import StockOutForm
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

# 创建蓝图
bp = Blueprint('sales', __name__, url_prefix='/sales')

# 销售管理 - 合并页面（订单 + 出库）
@bp.route('/')
@bp.route('/index')
@login_required
def index():
    """销售管理首页，展示订单、出库单、退货单列表"""
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

    orders = order_query.order_by(SalesOrder.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    # 获取出库单
    stock_out_query = StockOut.query

    if warehouse_id:
        stock_out_query = stock_out_query.filter_by(warehouse_id=warehouse_id)

    if start_date:
        stock_out_query = stock_out_query.filter(StockOut.delivery_date >= start_date)

    if end_date:
        stock_out_query = stock_out_query.filter(StockOut.delivery_date <= end_date)

    stock_outs = stock_out_query.order_by(StockOut.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    # 获取退货单
    return_query = SalesReturn.query
    if start_date:
        return_query = return_query.filter(SalesReturn.return_date >= start_date)
    if end_date:
        return_query = return_query.filter(SalesReturn.return_date <= end_date)
    returns_list = return_query.order_by(SalesReturn.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    customers = Customer.query.all()
    warehouses = Warehouse.query.all()

    # 预计算已退货的订单ID集合（用于模板显示"已退货"状态）
    returned_order_ids = set(
        r.sales_order_id for r in SalesReturn.query.filter(
            SalesReturn.status == 'completed',
            SalesReturn.sales_order_id.isnot(None)
        ).all()
    )

    return render_template('sales/index.html',
                         title='销售管理',
                         orders=orders,
                         stock_outs=stock_outs,
                         returns=returns_list,
                         returned_order_ids=returned_order_ids,
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
    """创建销售订单，支持直接出库"""
    customers = Customer.query.all()
    customers_data = build_partners_data(customers)
    warehouses = Warehouse.query.all()
    products = Product.query.all()
    products_data = build_products_data(products, include_purchase_price=False)

    # 获取默认仓库设置
    default_warehouse_id = SystemSetting.get_value('DEFAULT_WAREHOUSE')
    if default_warehouse_id:
        try:
            default_warehouse_id = int(default_warehouse_id)
        except (ValueError, TypeError):
            default_warehouse_id = None
    
    if request.method == 'POST':
        order_status = request.form.get('order_status', 'draft')
        
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
            # 重建商品明细数据（用于回填）
            order_items_list = []
            for i in range(len(product_ids)):
                if product_ids[i] and quantities[i] and unit_prices[i]:
                    product = db.session.get(Product, int(product_ids[i]))
                    if product:
                        order_items_list.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'product_code': product.code,
                            'quantity': quantities[i],
                            'unit_price': unit_prices[i]
                        })
            return render_template('sales/order_items.html',
                                 title='新建销售订单',
                                 customers=customers_data,
                                 warehouses=warehouses,
                                 products=products_data,
                                 action='new',
                                 submitted_customer_id=customer_id,
                                 submitted_warehouse_id=warehouse_id if warehouse_id else '',
                                 submitted_order_date=order_date,
                                 submitted_delivery_date=delivery_date,
                                 submitted_notes=notes,
                                 order_items=order_items_list)

        # 生成订单号
        order_number = generate_order_number('SO', SalesOrder)

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
                product = db.session.get(Product, int(product_ids[i]))
                if product:
                    quantity = to_decimal(quantities[i])
                    unit_price = to_decimal(unit_prices[i])
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

        # 如果选择直接出库
        if order_status == 'completed':
            # 检查库存是否充足
            insufficient_stock = []
            for item_data in order_items_list:
                product = item_data['product']
                if product.stock_quantity < item_data['quantity']:
                    insufficient_stock.append(f"{product.code} - {product.name} (库存: {product.stock_quantity}, 需求: {item_data['quantity']})")

            if insufficient_stock:
                db.session.rollback()
                flash(f'库存不足: {", ".join(insufficient_stock)}', 'danger')
                return render_template('sales/order_items.html',
                                     title='新建销售订单',
                                     customers=customers_data,
                                     warehouses=warehouses,
                                     products=products_data,
                                     action='new',
                                     submitted_customer_id=customer_id,
                                     submitted_warehouse_id=warehouse_id if warehouse_id else '',
                                     submitted_order_date=order_date,
                                     submitted_delivery_date=delivery_date,
                                     submitted_notes=notes,
                                     order_items=order_items_list,
                                     default_warehouse_id=default_warehouse_id)

            try:
                delivery_number = generate_order_number('OUT', StockOut)

                stock_out = StockOut(
                    delivery_number=delivery_number,
                    sales_order_id=order.id,
                    warehouse_id=warehouse_id,
                    delivery_date=datetime.now().date(),
                    handler=current_user.username,
                    notes='创建订单时直接出库',
                    created_by=current_user.id,
                    status='completed',
                    total_amount=total_amount
                )
                db.session.add(stock_out)
                db.session.flush()

                for item_data in order_items_list:
                    product = item_data['product']
                    quantity = item_data['quantity']
                    unit_price = item_data['unit_price']
                    amount = item_data['amount']

                    stock_out_item = StockOutItem(
                        stock_out_id=stock_out.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        amount=amount
                    )
                    db.session.add(stock_out_item)

                    before_quantity = to_decimal(product.stock_quantity)
                    after_quantity = before_quantity - to_decimal(quantity)
                    product.stock_quantity = after_quantity
                    product.sale_price = unit_price

                    log = StockLog(
                        product_id=product.id,
                        warehouse_id=warehouse_id,
                        change_type='out',
                        quantity=quantity,
                        before_quantity=before_quantity,
                        after_quantity=after_quantity,
                        reference_id=stock_out.id,
                        reference_type='stock_out',
                        notes=f'创建订单时直接出库: {delivery_number}',
                        created_by=current_user.id
                    )
                    db.session.add(log)

                    for order_item in order.items:
                        if order_item.product_id == product.id:
                            order_item.delivered_quantity = quantity

                order.status = 'completed'

                customer = order.customer
                if customer:
                    add_balance(customer, "receivable_balance", total_amount)

                flash(f'销售订单创建并出库完成！出库单号: {delivery_number}', 'success')
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f'直接出库失败: {str(e)}', 'danger')
                return render_template('sales/order_items.html',
                                     title='新建销售订单',
                                     customers=customers_data,
                                     warehouses=warehouses,
                                     products=products_data,
                                     action='new',
                                     submitted_customer_id=customer_id,
                                     submitted_warehouse_id=warehouse_id if warehouse_id else '',
                                     submitted_order_date=order_date,
                                     submitted_delivery_date=delivery_date,
                                     submitted_notes=notes,
                                     order_items=order_items_list,
                                     default_warehouse_id=default_warehouse_id)
        else:
            flash('销售订单创建成功！', 'success')

        db.session.commit()
        return redirect(url_for('sales.index'))

    return render_template('sales/order_items.html',
                         title='新建销售订单',
                         customers=customers_data,
                         warehouses=warehouses,
                         products=products_data,
                         action='new',
                         default_warehouse_id=default_warehouse_id)

# 编辑订单基本信息
@bp.route('/orders/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_order(id):
    """编辑销售订单，支持调整客户应收余额"""
    order = db.session.query(SalesOrder).options(selectinload(SalesOrder.items).selectinload(SalesOrderItem.product)).filter(SalesOrder.id == id).first()
    if order is None:
        abort(404)

    if order.status == 'completed':
        flash('已完成的订单不能修改！', 'danger')
        return redirect(url_for('sales.index', tab=get_redirect_tab(order.status)))
    
    customers = Customer.query.all()
    customers_data = build_partners_data(customers)
    warehouses = Warehouse.query.all()
    products = Product.query.all()
    products_data = build_products_data(products, include_purchase_price=False)

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
            # 重建商品明细数据（用于回填）
            order_items_list = []
            for i in range(len(product_ids)):
                if product_ids[i] and quantities[i] and unit_prices[i]:
                    product = db.session.get(Product, int(product_ids[i]))
                    if product:
                        order_items_list.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'product_code': product.code,
                            'quantity': quantities[i],
                            'unit_price': unit_prices[i]
                        })
            return render_template('sales/order_items.html',
                                 title='编辑销售订单',
                                 order=order,
                                 customers=customers_data,
                                 warehouses=warehouses,
                                 products=products_data,
                                 action='edit',
                                 submitted_customer_id=customer_id,
                                 submitted_warehouse_id=warehouse_id if warehouse_id else '',
                                 submitted_order_date=order_date,
                                 submitted_delivery_date=delivery_date,
                                 submitted_notes=notes,
                                 order_items=order_items_list)
        
        # 更新订单基本信息
        old_customer = order.customer
        order.customer_id = customer_id
        order.warehouse_id = warehouse_id
        order.order_date = datetime.strptime(order_date, '%Y-%m-%d').date()
        order.delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d').date() if delivery_date else None
        order.notes = notes
        
        # 更新商品明细（保留已出库数量，只删除本次移除的商品）
        original_total = to_decimal(order.total_amount)
        existing_items = {item.product_id: item for item in order.items}
        remaining_product_ids = set()
        total_amount = 0

        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_prices[i]:
                product_id = int(product_ids[i])
                remaining_product_ids.add(product_id)
                product = db.session.get(Product, product_id)
                if product:
                    quantity = to_decimal(quantities[i])
                    unit_price = to_decimal(unit_prices[i])
                    amount = quantity * unit_price
                    total_amount += amount

                    if product_id in existing_items:
                        # 保留已有的 delivered_quantity，只更新数量和单价
                        item = existing_items[product_id]
                        item.quantity = quantity
                        item.unit_price = unit_price
                        item.amount = amount
                    else:
                        # 新增商品，delivered_quantity 从 0 开始
                        item = SalesOrderItem(
                            order_id=order.id,
                            product_id=product_id,
                            quantity=quantity,
                            unit_price=unit_price,
                            amount=amount
                        )
                        db.session.add(item)

        # 删除本次编辑中移除的商品明细（保护已出库的数量记录）
        items_to_delete = [item for item in order.items if item.product_id not in remaining_product_ids]
        for item in items_to_delete:
            db.session.delete(item)

        order.total_amount = total_amount
        
        # 调整客户应收余额（差额）- 仅对已完成的订单
        # 注意：confirmed/partial 状态的订单尚未实际出库，不调整余额
        # 余额仅在订单 status=completed（已全部出库）时才记录
        if order.status == 'completed':
            if old_customer and old_customer.id != customer_id:
                # 换了客户：回滚旧客户余额，增加新客户余额
                sub_balance(old_customer, "receivable_balance", original_total)
                new_customer = db.session.get(Customer, customer_id)
                if new_customer:
                    add_balance(new_customer, "receivable_balance", total_amount)
            elif order.customer:
                # 同客户：调整差额
                add_balance(order.customer, "receivable_balance", total_amount - original_total)
        
        db.session.commit()
        flash('销售订单修改成功！', 'success')
        return redirect(url_for('sales.index', tab=get_redirect_tab(order.status)))
    
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
    """兼容旧路由，重定向到订单编辑页"""
    return redirect(url_for('sales.edit_order', id=id))

# 删除订单
@bp.route('/orders/<int:id>/delete', methods=['POST'])
@login_required
def delete_order(id):
    """删除销售订单，含关联数据校验"""
    order = db.session.get(SalesOrder, id)
    if order is None:
        abort(404)

    # 检查是否有关联的发货单
    if order.stock_outs:
        flash('此订单有关联的发货单，无法删除！', 'danger')
        return redirect(url_for('sales.index'))

    # 检查是否有收款记录（reference_id 为逗号分隔的字符串，需模糊匹配）
    from app.models import Receipt
    from sqlalchemy import or_
    oid = str(order.id)
    if Receipt.query.filter(
        Receipt.reference_type == 'sales_order',
        Receipt.reference_id.isnot(None),
        or_(
            Receipt.reference_id == oid,
            Receipt.reference_id.like(f'{oid},%'),
            Receipt.reference_id.like(f'%,{oid},%'),
            Receipt.reference_id.like(f'%,{oid}'),
        )
    ).first():
        flash('此订单已有收款记录，无法删除！', 'danger')
        return redirect(url_for('sales.index'))

    # 检查是否有库存流水记录（包括退货等关联操作）
    if StockLog.query.filter_by(reference_type='sales_order', reference_id=order.id).first():
        flash('此订单已有库存操作记录，无法删除！', 'danger')
        return redirect(url_for('sales.index'))

    # 检查是否已退货
    if SalesReturn.query.filter_by(sales_order_id=id, status='completed').first():
        flash('此订单已退货，无法删除！', 'danger')
        return redirect(url_for('sales.index'))

    # 回滚客户应收余额（订单创建时已累加）
    customer = order.customer
    # 只有已完成的订单才需要回滚应收余额（confirmed/partial 未实际出库，无余额记录）
    if customer and order.status == 'completed':
        sub_balance(customer, "receivable_balance", order.total_amount)
    
    db.session.delete(order)
    db.session.commit()
    
    flash('销售订单删除成功！', 'success')
    return redirect(url_for('sales.index'))

@bp.route('/orders/<int:id>/quick-stock-out', methods=['POST'])
@login_required
def quick_stock_out(id):
    """快捷出库：从销售订单直接出库（一次性完成）"""
    order = db.session.query(SalesOrder).options(
        selectinload(SalesOrder.items).selectinload(SalesOrderItem.product)
    ).filter(SalesOrder.id == id).with_for_update().first()
    if order is None:
        abort(404)
    
    if order.status == 'completed':
        flash('已完成的订单不能快捷出库！', 'danger')
        return redirect(url_for('sales.index'))
    
    if len(order.items) == 0:
        flash('此订单没有商品明细！', 'danger')
        return redirect(url_for('sales.index'))
    
    try:
        delivery_number = generate_order_number('OUT', StockOut)

        stock_out = StockOut(
            delivery_number=delivery_number,
            sales_order_id=order.id,
            warehouse_id=order.warehouse_id,
            delivery_date=datetime.now().date(),
            handler=current_user.username,
            notes='快捷出库',
            created_by=current_user.id,
            status='completed',
            total_amount=0
        )
        db.session.add(stock_out)
        db.session.flush()
        
        total_amount = 0
        for item in order.items:
            remaining_qty = to_decimal(item.quantity) - to_decimal(item.delivered_quantity)
            if remaining_qty <= 0:
                continue

            # 锁定商品行，防止并发出库导致库存计算错误
            product = db.session.query(Product).filter(Product.id == item.product_id).with_for_update().first()
            if not product:
                continue
            if to_decimal(product.stock_quantity) < remaining_qty:
                db.session.rollback()
                flash(f'商品 {product.name} 库存不足，当前库存: {to_decimal(product.stock_quantity)}，需要: {remaining_qty}', 'danger')
                return redirect(url_for('sales.view_order', id=order.id))
            unit_price = to_decimal(item.unit_price)
            product.sale_price = unit_price

            amount = remaining_qty * unit_price
            total_amount += amount

            stock_out_item = StockOutItem(
                stock_out_id=stock_out.id,
                product_id=product.id,
                quantity=remaining_qty,
                unit_price=unit_price,
                amount=amount
            )
            db.session.add(stock_out_item)

            before_quantity = to_decimal(product.stock_quantity)
            after_quantity = before_quantity - remaining_qty
            product.stock_quantity = after_quantity

            log = StockLog(
                product_id=product.id,
                warehouse_id=order.warehouse_id,
                change_type='out',
                quantity=remaining_qty,
                before_quantity=before_quantity,
                after_quantity=after_quantity,
                reference_id=stock_out.id,
                reference_type='stock_out',
                notes=f'快捷出库: {delivery_number}',
                created_by=current_user.id
            )
            db.session.add(log)
            
            item.delivered_quantity = to_decimal(item.delivered_quantity) + remaining_qty
        
        stock_out.total_amount = total_amount

        # 无需出库时：检查是否所有商品已出库但订单未完成（需更新状态+加余额）
        if total_amount == 0:
            all_delivered = all(
                to_decimal(oi.delivered_quantity) >= to_decimal(oi.quantity)
                for oi in order.items
            )
            if all_delivered and order.status != 'completed':
                order.status = 'completed'
                customer = order.customer
                if customer:
                    add_balance(customer, 'receivable_balance', order.total_amount)
                db.session.commit()
            elif order.status == 'completed':
                db.session.commit()
            else:
                db.session.rollback()
            flash('此订单所有商品都已出库！', 'warning')
            return redirect(url_for('sales.index', tab='stockouts'))

        # 检查订单是否全部出库
        all_delivered = all(
            item.delivered_quantity >= item.quantity
            for item in order.items
        )
        
        if all_delivered:
            # 订单首次完成时补记应收余额（非completed→completed不重复记）
            if order.customer:
                add_balance(order.customer, "receivable_balance", order.total_amount)
            order.status = 'completed'
        else:
            order.status = 'partial'

        db.session.commit()
        flash(f'快捷出库完成！出库单号: {delivery_number}', 'success')
        
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'出库失败: {str(e)}', 'danger')
    
    return redirect(url_for('sales.index', tab='stockouts'))


# 查看订单详情
@bp.route('/orders/<int:id>')
@login_required
def view_order(id):
    """查看销售订单详情及关联出库单"""
    order = db.session.query(SalesOrder).options(selectinload(SalesOrder.items).selectinload(SalesOrderItem.product)).filter(SalesOrder.id == id).first()
    if order is None:
        abort(404)
    related_stock_outs = StockOut.query.filter_by(sales_order_id=id).order_by(StockOut.created_at.desc()).all()
    
    # 准备订单商品数据用于JavaScript确认框
    order_items_data = []
    for item in order.items:
        remaining = to_decimal(item.quantity) - to_decimal(item.delivered_quantity)
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
    """从销售订单创建出库单（预填未出库商品）"""
    order = db.session.query(SalesOrder).options(selectinload(SalesOrder.items).selectinload(SalesOrderItem.product)).filter(SalesOrder.id == id).first()
    if order is None:
        abort(404)

    if order.status not in ['confirmed', 'partial']:
        flash('只有已确认或部分出库的订单可以创建出库单！', 'danger')
        return redirect(url_for('sales.view_order', id=id))
    
    # 生成出库单号
    delivery_number = generate_order_number('OUT', StockOut)

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
        remaining_qty = to_decimal(order_item.quantity) - to_decimal(order_item.delivered_quantity)
        if remaining_qty > 0:
            unit_price = to_decimal(order_item.unit_price)
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
    """新建出库单，支持关联销售订单或直接出库"""
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
        delivery_number = generate_order_number('OUT', StockOut)

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
    """编辑出库单商品明细"""
    stock_out = db.session.get(StockOut, id)
    if stock_out is None:
        abort(404)

    if request.method == 'POST':
        # 处理商品明细
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        
        # 构建 products_data（供验证失败时重新渲染模板用）
        products = Product.query.all()
        products_data = build_products_data(products, include_purchase_price=False)
        
        # 验证：至少要有一行商品明细
        has_items = False
        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_prices[i]:
                has_items = True
                try:
                    qty = float(quantities[i])
                    price = float(unit_prices[i])
                    if qty <= 0 or price < 0:
                        flash('数量必须大于0，单价不能为负数！', 'danger')
                        items_data = [{
                            'product_id': int(product_ids[i]),
                            'quantity': qty,
                            'unit_price': price
                        } for i in range(len(product_ids)) if product_ids[i]]
                        return render_template('sales/stock_out_items.html',
                            title='编辑出库明细',
                            stock_out=stock_out,
                            products=products_data,
                            order_items=items_data)
                except (ValueError, TypeError):
                    flash('数量和单价必须是有效数字！', 'danger')
                    items_data = [{
                        'product_id': int(product_ids[i]) if product_ids[i] else 0,
                        'quantity': float(quantities[i]) if quantities[i] else 0,
                        'unit_price': float(unit_prices[i]) if unit_prices[i] else 0
                    } for i in range(len(product_ids)) if product_ids[i]]
                    return render_template('sales/stock_out_items.html',
                        title='编辑出库明细',
                        stock_out=stock_out,
                        products=products_data,
                        order_items=items_data)
        
        if not has_items:
            flash('请至少添加一个商品明细！', 'danger')
            return render_template('sales/stock_out_items.html',
                                 title='编辑出库明细',
                                 stock_out=stock_out,
                                 products=products_data,
                                 order_items=[])
        
        # 删除原有明细并重建
        StockOutItem.query.filter_by(stock_out_id=stock_out.id).delete()
        
        total_amount = 0
        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_prices[i]:
                product = db.session.get(Product, int(product_ids[i]))
                if product:
                    quantity = to_decimal(quantities[i])
                    unit_price = to_decimal(unit_prices[i])
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
                    # 同步更新商品销价（与 quick_stock_out 保持一致）
                    product.sale_price = unit_price
        
        stock_out.total_amount = total_amount
        db.session.commit()
        
        flash('商品明细保存成功！', 'success')
        return redirect(url_for('sales.index', tab='stockouts'))
    
    products = Product.query.all()
    products_data = build_products_data(products, include_purchase_price=False)
    
    return render_template('sales/stock_out_items.html', 
                         title='编辑出库明细',
                         stock_out=stock_out,
                         products=products_data)

# 完成出库
@bp.route('/stock-outs/<int:id>/complete', methods=['POST'])
@login_required
def complete_stock_out(id):
    """确认出库，更新库存并同步订单状态和客户应收余额"""
    stock_out = db.session.query(StockOut).options(selectinload(StockOut.items).selectinload(StockOutItem.product)).filter(StockOut.id == id).with_for_update().first()
    if stock_out is None:
        abort(404)
    
    # 检查是否已经完成
    if stock_out.status == 'completed':
        flash('此出库单已经完成，不能重复确认！', 'danger')
        return redirect(url_for('sales.index', tab='stockouts'))
    
    if stock_out.status != 'pending':
        flash('此出库单状态异常，无法确认！', 'danger')
        return redirect(url_for('sales.index', tab='stockouts'))
    
    if len(stock_out.items) == 0:
        flash('请先添加商品明细！', 'danger')
        return redirect(url_for('sales.edit_stock_out_items', id=stock_out.id))
    
    # 开始事务
    try:
        # 锁定并检查所有商品库存（单个循环，避免重复迭代）
        locked_products = {}
        insufficient_stock = []
        warehouse = stock_out.warehouse

        for item in stock_out.items:
            # 锁定商品行，防止并发出库导致库存计算错误
            product = db.session.query(Product).filter(Product.id == item.product_id).with_for_update().first()
            if not product:
                continue
            locked_products[item.id] = product
            if product.stock_quantity < item.quantity:
                insufficient_stock.append(
                    f"{product.code} - {product.name} (库存: {product.stock_quantity}, 需求: {item.quantity})"
                )

        if insufficient_stock:
            flash(f'库存不足: {", ".join(insufficient_stock)}', 'danger')
            db.session.rollback()
            return redirect(url_for('sales.index', tab='stockouts'))

        # 更新库存和记录流水
        for item in stock_out.items:
            product = locked_products.get(item.id)
            if not product:
                continue

            before_quantity = to_decimal(product.stock_quantity)
            after_quantity = before_quantity - to_decimal(item.quantity)
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
        
        # 先更新出库单状态为已完成（必须在前，delivered_quantity 只统计已完成的单）
        stock_out.status = 'completed'
        stock_out.updated_at = datetime.now()

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
                # 更新客户应收余额（使用订单总额，而非仅本次出库金额）
                customer = order.customer
                if customer:
                    add_balance(customer, "receivable_balance", order.total_amount)
            else:
                order.status = 'partial'

        
        db.session.commit()
        flash('出库单完成！库存已更新。', 'success')
        
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'出库失败: {str(e)}', 'danger')
    
    return redirect(url_for('sales.index', tab='stockouts'))

# 删除出库单
@bp.route('/stock-outs/<int:id>/delete', methods=['POST'])
@login_required
def delete_stock_out(id):
    """删除未出库状态的出库单"""
    stock_out = db.session.get(StockOut, id)
    if stock_out is None:
        abort(404)

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
    """查看出库单详情"""
    stock_out = db.session.get(StockOut, id)
    if stock_out is None:
        abort(404)
    return render_template('sales/stock_out_view.html',
                         title='出库单详情',
                         stock_out=stock_out)


# ==================== 销售退货管理 ====================

@bp.route('/orders/<int:id>/quick-return', methods=['POST'])
@login_required
def quick_return(id):
    """快捷退货: 从销售订单直接退货(一次性完成)"""
    order = db.session.query(SalesOrder).options(
        selectinload(SalesOrder.items).selectinload(SalesOrderItem.product)
    ).filter(SalesOrder.id == id).first()
    if order is None:
        abort(404)

    if order.status != 'completed':
        flash('只有已完成的销售订单可以退货！', 'danger')
        return redirect(url_for('sales.index', tab='orders'))

    if len(order.items) == 0:
        flash('此订单没有商品明细，无法退货！', 'danger')
        return redirect(url_for('sales.index', tab='orders'))

    if SalesReturn.query.filter_by(sales_order_id=id, status='completed').first():
        flash('此订单已经退货，不能重复退货！', 'danger')
        return redirect(url_for('sales.index', tab='orders'))

    try:
        return_number = generate_order_number('SR', SalesReturn)

        sales_return = SalesReturn(
            return_number=return_number,
            sales_order_id=order.id,
            warehouse_id=order.warehouse_id,
            return_date=datetime.now().date(),
            handler=current_user.username,
            notes='快捷退货',
            created_by=current_user.id,
            status='completed',
            total_amount=0
        )
        db.session.add(sales_return)
        db.session.flush()

        total_amount = 0
        has_items = False
        for order_item in order.items:
            product = db.session.query(Product).filter(Product.id == order_item.product_id).with_for_update().first()
            if not product:
                continue

            # 退货数量等于已出库数量（销售退货是入库操作，不受库存上限限制）
            return_qty = to_decimal(order_item.delivered_quantity or 0)
            if return_qty <= 0:
                continue

            has_items = True
            unit_price = to_decimal(order_item.unit_price)
            amount = return_qty * unit_price

            item = SalesReturnItem(
                return_id=sales_return.id,
                product_id=product.id,
                quantity=return_qty,
                unit_price=unit_price,
                amount=amount
            )
            db.session.add(item)
            total_amount += amount

            before_quantity = to_decimal(product.stock_quantity)
            after_quantity = before_quantity + return_qty
            product.stock_quantity = after_quantity

            log = StockLog(
                product_id=product.id,
                warehouse_id=order.warehouse_id,
                change_type='return_in',
                quantity=return_qty,
                before_quantity=before_quantity,
                after_quantity=after_quantity,
                reference_id=sales_return.id,
                reference_type='sales_return',
                notes=f'销售退货: {return_number}',
                created_by=current_user.id
            )
            db.session.add(log)

        if not has_items:
            db.session.rollback()
            flash('此订单没有可退货的商品！', 'warning')
            return redirect(url_for('sales.index', tab='orders'))

        sales_return.total_amount = total_amount

        # 减少客户应收余额（退货=减少应收）
        customer = order.customer
        if customer:
            sub_balance(customer, 'receivable_balance', total_amount)

        db.session.commit()
        flash(f'退货单 {return_number} 创建成功，库存已更新！', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'退货失败: {str(e)}', 'danger')

    return redirect(url_for('sales.index', tab='returns'))


@bp.route('/returns')
@login_required
def returns():
    """销售退货单列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = SalesReturn.query
    if start_date:
        query = query.filter(SalesReturn.return_date >= start_date)
    if end_date:
        query = query.filter(SalesReturn.return_date <= end_date)

    returns_list = query.order_by(SalesReturn.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('sales/returns.html',
                         title='销售退货管理',
                         returns=returns_list,
                         start_date=start_date or '',
                         end_date=end_date or '')


@bp.route('/returns/<int:id>')
@login_required
def view_return(id):
    """查看退货单详情"""
    sales_return = db.session.get(SalesReturn, id)
    if sales_return is None:
        abort(404)
    return render_template('sales/return_view.html',
                         title='退货单详情',
                         sales_return=sales_return)


@bp.route('/returns/<int:id>/delete', methods=['POST'])
@login_required
def delete_return(id):
    """删除未完成的退货单"""
    sales_return = db.session.get(SalesReturn, id)
    if sales_return is None:
        abort(404)

    if sales_return.status != 'pending':
        flash('只有未完成的退货单可以删除！', 'danger')
        return redirect(url_for('sales.returns'))

    db.session.delete(sales_return)
    db.session.commit()
    flash('退货单删除成功！', 'success')
    return redirect(url_for('sales.returns'))


# API接口
@bp.route('/api/sales-orders/<int:order_id>/items')
@login_required
def api_order_items(order_id):
    """获取销售订单商品明细的JSON接口"""
    order = db.session.get(SalesOrder, order_id)
    if order is None:
        abort(404)
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
