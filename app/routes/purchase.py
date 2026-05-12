from flask import render_template, redirect, url_for, flash, request, jsonify, Blueprint
from flask_login import login_required, current_user
from app import db
from sqlalchemy.orm import selectinload
from app.models import PurchaseOrder, SystemSetting, PurchaseOrderItem, StockIn, StockInItem, Supplier, Warehouse, Product, StockLog, Log, PurchaseReturn, PurchaseReturnItem
from app.utils import to_decimal, add_balance, sub_balance
from app.forms import PurchaseOrderForm, PurchaseOrderItemForm, StockInForm
from datetime import datetime, timezone
import urllib.parse

def get_redirect_tab():
    """从referer获取当前tab,默认返回orders"""
    referer = request.referrer
    if referer:
        parsed = urllib.parse.urlparse(referer)
        query_params = urllib.parse.parse_qs(parsed.query)
        if 'tab' in query_params:
            return query_params['tab'][0]
    return 'orders'

# 创建蓝图
bp = Blueprint('purchase', __name__, url_prefix='/purchase')

# 采购管理 - 合并页面(订单 + 入库)
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

    orders = order_query.order_by(PurchaseOrder.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    # 获取入库单
    stock_in_query = StockIn.query

    if warehouse_id:
        stock_in_query = stock_in_query.filter_by(warehouse_id=warehouse_id)

    if start_date:
        stock_in_query = stock_in_query.filter(StockIn.receipt_date >= start_date)

    if end_date:
        stock_in_query = stock_in_query.filter(StockIn.receipt_date <= end_date)

    stock_ins = stock_in_query.order_by(StockIn.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    # 获取退货单
    return_query = PurchaseReturn.query
    if start_date:
        return_query = return_query.filter(PurchaseReturn.return_date >= start_date)
    if end_date:
        return_query = return_query.filter(PurchaseReturn.return_date <= end_date)
    returns_list = return_query.order_by(PurchaseReturn.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    suppliers = Supplier.query.all()
    warehouses = Warehouse.query.all()

    # 预计算已退货的订单ID集合（用于模板显示"已退货"状态）
    returned_order_ids = set(
        r.purchase_order_id for r in PurchaseReturn.query.filter(
            PurchaseReturn.status == 'completed',
            PurchaseReturn.purchase_order_id.isnot(None)
        ).all()
    )

    return render_template('purchase/index.html',
                         title='采购管理',
                         orders=orders,
                         stock_ins=stock_ins,
                         returns=returns_list,
                         returned_order_ids=returned_order_ids,
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

    # 获取默认仓库设置
    default_warehouse_id = SystemSetting.get_value('DEFAULT_WAREHOUSE')
    if default_warehouse_id:
        try:
            default_warehouse_id = int(default_warehouse_id)
        except (ValueError, TypeError):
            default_warehouse_id = None

    if request.method == 'POST':
        action = request.form.get('action', 'save')
        order_status = request.form.get('order_status', 'draft')

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
            flash('请填写必填字段!', 'danger')
            # 重建商品明细数据(用于回填)
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
                                 submitted_warehouse_id=warehouse_id if warehouse_id else '',
                                 submitted_order_date=order_date,
                                 submitted_expected_date=expected_date,
                                 submitted_notes=notes,
                                 order_items=order_items_list)

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

        # 如果选择直接入库,完成入库流程
        if order_status == 'completed':
            try:
                # 生成入库单号
                last_stock_in = StockIn.query.filter(StockIn.receipt_number.like(f'SI{today}%')).order_by(StockIn.id.desc()).first()
                if last_stock_in:
                    last_num = int(last_stock_in.receipt_number[10:]) if len(last_stock_in.receipt_number) > 10 else 0
                    receipt_number = f'SI{today}{last_num + 1:03d}'
                else:
                    receipt_number = f'SI{today}001'

                stock_in = StockIn(
                    receipt_number=receipt_number,
                    purchase_order_id=order.id,
                    warehouse_id=warehouse_id,
                    receipt_date=datetime.now().date(),
                    handler=current_user.username,
                    notes='创建订单时直接入库',
                    created_by=current_user.id,
                    status='completed',
                    total_amount=total_amount
                )
                db.session.add(stock_in)
                db.session.flush()

                # 创建入库明细并更新库存
                for item_data in order_items_list:
                    product = item_data['product']
                    quantity = item_data['quantity']
                    unit_price = item_data['unit_price']
                    amount = item_data['amount']

                    stock_in_item = StockInItem(
                        stock_in_id=stock_in.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        amount=amount
                    )
                    db.session.add(stock_in_item)

                    before_quantity = float(product.stock_quantity)
                    after_quantity = before_quantity + quantity
                    product.stock_quantity = after_quantity
                    product.purchase_price = unit_price

                    log = StockLog(
                        product_id=product.id,
                        warehouse_id=warehouse_id,
                        change_type='in',
                        quantity=quantity,
                        before_quantity=before_quantity,
                        after_quantity=after_quantity,
                        reference_id=stock_in.id,
                        reference_type='stock_in',
                        notes=f'创建订单时直接入库: {receipt_number}',
                        created_by=current_user.id
                    )
                    db.session.add(log)

                    for order_item in order.items:
                        if order_item.product_id == product.id:
                            order_item.received_quantity = quantity

                order.status = 'completed'

                supplier = order.supplier
                if supplier:
                    add_balance(supplier, "payable_balance", total_amount)

                flash(f'采购订单创建并入库完成!入库单号: {receipt_number}', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'直接入库失败: {str(e)}', 'danger')
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
                                     order_items=order_items_list,
                                     default_warehouse_id=default_warehouse_id)
        else:
            flash('采购订单创建成功!', 'success')

        db.session.commit()
        return redirect(url_for('purchase.index', tab=get_redirect_tab()))

    return render_template('purchase/order_items.html',
                         title='新建采购订单',
                         suppliers=suppliers_data,
                         warehouses=warehouses,
                         products=products_data,
                         action='new',
                         default_warehouse_id=default_warehouse_id)

@bp.route('/orders/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_order(id):
    order = PurchaseOrder.query.options(selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.product)).get_or_404(id)

    if order.status == 'completed':
        flash('已完成的订单不能修改!', 'danger')
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
            flash('请填写必填字段!', 'danger')
            # 重建商品明细数据(用于回填)
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
                                 submitted_warehouse_id=warehouse_id if warehouse_id else '',
                                 submitted_order_date=order_date,
                                 submitted_expected_date=expected_date,
                                 submitted_notes=notes,
                                 order_items=order_items_list)

        # 更新订单基本信息
        old_supplier = order.supplier
        order.supplier_id = supplier_id
        order.warehouse_id = warehouse_id
        order.order_date = datetime.strptime(order_date, '%Y-%m-%d').date()
        order.expected_date = datetime.strptime(expected_date, '%Y-%m-%d').date() if expected_date else None
        order.notes = notes

        # 更新商品明细（保留已入库数量，只删除本次移除的商品）
        original_total = float(order.total_amount)
        existing_items = {item.product_id: item for item in order.items}
        remaining_product_ids = set()
        total_amount = 0

        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_prices[i]:
                product_id = int(product_ids[i])
                remaining_product_ids.add(product_id)
                product = Product.query.get(product_id)
                if product:
                    quantity = float(quantities[i])
                    unit_price = float(unit_prices[i])
                    amount = quantity * unit_price
                    total_amount += amount

                    if product_id in existing_items:
                        # 保留已有的 received_quantity，只更新数量和单价
                        item = existing_items[product_id]
                        item.quantity = quantity
                        item.unit_price = unit_price
                        item.amount = amount
                    else:
                        # 新增商品，received_quantity 从 0 开始
                        item = PurchaseOrderItem(
                            order_id=order.id,
                            product_id=product_id,
                            quantity=quantity,
                            unit_price=unit_price,
                            amount=amount
                        )
                        db.session.add(item)

        # 删除本次编辑中移除的商品明细（保护已入库的数量记录）
        items_to_delete = [item for item in order.items if item.product_id not in remaining_product_ids]
        for item in items_to_delete:
            db.session.delete(item)

        order.total_amount = total_amount

        # 调整供应商余额(差额)- 仅对已完成的订单
        # 注意:confirmed/partial 状态的订单尚未实际入库,不调整余额
        # 余额仅在订单 status=completed(已全部入库)时才记录
        if order.status == 'completed':
            if old_supplier and old_supplier.id != supplier_id:
                # 换了供应商:回滚旧供应商余额,增加新供应商余额
                sub_balance(old_supplier, "payable_balance", original_total)
                new_supplier = Supplier.query.get(supplier_id)
                if new_supplier:
                    add_balance(new_supplier, "payable_balance", total_amount)
            elif order.supplier:
                # 同供应商:调整差额
                add_balance(order.supplier, "payable_balance", total_amount - original_total)

        if action == 'confirm':
            if len(product_ids) == 0 or total_amount == 0:
                flash('请先添加商品明细!', 'danger')
                # 重建商品明细数据(用于回填)
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
                                     submitted_warehouse_id=warehouse_id if warehouse_id else '',
                                     submitted_order_date=order_date,
                                     submitted_expected_date=expected_date,
                                     submitted_notes=notes,
                                     order_items=order_items_list)

        db.session.commit()

        flash('采购订单修改成功!', 'success')
        return redirect(url_for('purchase.index', tab=get_redirect_tab()))

    return render_template('purchase/order_items.html',
                         title='编辑采购订单',
                         order=order,
                         suppliers=suppliers_data,
                         warehouses=warehouses,
                         products=products_data,
                         order_items=order_items_data,
                         action='edit')

# 保留旧路由用于兼容,重定向到 edit_order
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
        flash('此订单有关联的入库单,无法删除!', 'danger')
        return redirect(url_for('purchase.index', tab=get_redirect_tab()))

    # 检查是否有付款记录（通过 reference_type=order.id 关联）
    from app.models import Payment
    if Payment.query.filter_by(reference_type='purchase_order', reference_id=order.id).first():
        flash('此订单已有付款记录，无法删除！', 'danger')
        return redirect(url_for('purchase.index', tab=get_redirect_tab()))

    # 检查是否有库存流水记录
    from app.models import StockLog
    if StockLog.query.filter_by(reference_type='purchase_order', reference_id=order.id).first():
        flash('此订单已有库存操作记录，无法删除！', 'danger')
        return redirect(url_for('purchase.index', tab=get_redirect_tab()))

    # 只有已完成的订单才需要回滚供应商应付余额（confirmed/partial 未实际入库，无余额记录）
    supplier = order.supplier
    if supplier and order.status == 'completed':
        sub_balance(supplier, "payable_balance", order.total_amount)

    db.session.delete(order)
    db.session.commit()
    flash('采购订单删除成功!', 'success')
    return redirect(url_for('purchase.index', tab=get_redirect_tab()))


@bp.route('/orders/<int:id>/quick-stock-in', methods=['POST'])
@login_required
def quick_stock_in(id):
    """快捷入库:从采购订单直接入库(一次性完成)"""
    order = PurchaseOrder.query.options(
        selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.product)
    ).with_for_update().get_or_404(id)

    if order.status == 'completed':
        flash('此订单已入库完成!', 'danger')
        return redirect(url_for('purchase.index', tab=get_redirect_tab()))

    if len(order.items) == 0:
        flash('此订单没有商品明细,无法入库!', 'danger')
        return redirect(url_for('purchase.index', tab=get_redirect_tab()))

    try:
        today = datetime.now().strftime('%Y%m%d')
        last_stock_in = StockIn.query.filter(StockIn.receipt_number.like(f'SI{today}%')).order_by(StockIn.id.desc()).first()
        if last_stock_in:
            last_num = int(last_stock_in.receipt_number[10:]) if len(last_stock_in.receipt_number) > 10 else 0
            receipt_number = f'SI{today}{last_num + 1:03d}'
        else:
            receipt_number = f'SI{today}001'

        stock_in = StockIn(
            receipt_number=receipt_number,
            purchase_order_id=order.id,
            warehouse_id=order.warehouse_id,
            receipt_date=datetime.now().date(),
            handler=current_user.username,
            notes='快捷入库',
            created_by=current_user.id,
            status='completed',
            total_amount=0
        )
        db.session.add(stock_in)
        db.session.flush()

        total_amount = 0
        has_partial = False
        stock_in_details = []
        for order_item in order.items:
            remaining_qty = float(order_item.quantity) - float(order_item.received_quantity)
            if remaining_qty <= 0:
                continue

            has_partial = True
            unit_price = float(order_item.unit_price)
            amount = remaining_qty * unit_price

            item = StockInItem(
                stock_in_id=stock_in.id,
                product_id=order_item.product_id,
                quantity=remaining_qty,
                unit_price=unit_price,
                amount=amount
            )
            db.session.add(item)
            total_amount += amount

            # 锁定商品行，防止并发入库导致库存计算错误
            product = Product.query.with_for_update().get(order_item.product_id)
            if not product:
                continue
            product.purchase_price = unit_price
            before_quantity = float(product.stock_quantity)
            after_quantity = before_quantity + remaining_qty
            product.stock_quantity = after_quantity

            log = StockLog(
                product_id=product.id,
                warehouse_id=order.warehouse_id,
                change_type='in',
                quantity=remaining_qty,
                before_quantity=before_quantity,
                after_quantity=after_quantity,
                reference_id=stock_in.id,
                reference_type='stock_in',
                notes=f'快捷入库: {receipt_number}',
                created_by=current_user.id
            )
            db.session.add(log)

            order_item.received_quantity = order_item.quantity

            stock_in_details.append(f"{product.name} 库存增加 {remaining_qty} {product.unit}")

        # 无需入库时：检查是否所有商品已入库但订单未完成（需更新状态+加余额）
        if total_amount == 0:
            # 检查是否所有商品都已入库
            all_received = all(
                float(oi.received_quantity) >= float(oi.quantity)
                for oi in order.items
            )
            if all_received and order.status != 'completed':
                # 所有商品已入库但订单状态未更新，补记状态和余额
                order.status = 'completed'
                supplier = order.supplier
                if supplier:
                    add_balance(supplier, 'payable_balance', float(order.total_amount))
                db.session.commit()
            elif order.status == 'completed':
                db.session.commit()  # 已完成，无需操作
            else:
                db.session.rollback()
            flash('此订单所有商品都已入库！', 'warning')
            return redirect(url_for('purchase.index', tab=get_redirect_tab()))

        stock_in.total_amount = total_amount

        # 检查订单是否全部入库
        all_received = all(
            float(oi.received_quantity) >= float(oi.quantity)
            for oi in order.items
        )

        if all_received:
            order.status = 'completed'
            # 更新供应商应付余额
            supplier = order.supplier
            if supplier:
                add_balance(supplier, "payable_balance", total_amount)
        else:
            order.status = 'partial'

        db.session.commit()
        flash(f'入库单 {receipt_number} 创建成功,库存已更新', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'入库失败: {str(e)}', 'danger')

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

# 从采购订单直接创建入库单(直接入库)
@bp.route('/orders/<int:id>/stock-in', methods=['GET', 'POST'])
@login_required
def new_stock_in_from_order(id):
    order = PurchaseOrder.query.options(selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.product)).get_or_404(id)

    if order.status not in ['confirmed', 'partial']:
        flash('只有已确认或部分入库的订单可以入库!', 'danger')
        return redirect(url_for('purchase.view_order', id=id))

    # 生成入库单号
    today = datetime.now().strftime('%Y%m%d')
    last_stock_in = StockIn.query.filter(StockIn.receipt_number.like(f'SI{today}%')).order_by(StockIn.id.desc()).first()
    if last_stock_in:
        last_num = int(last_stock_in.receipt_number[10:]) if len(last_stock_in.receipt_number) > 10 else 0
        receipt_number = f'SI{today}{last_num + 1:03d}'
    else:
        receipt_number = f'SI{today}001'

    # 创建入库单,预填采购订单信息
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

    flash(f'入库单 {receipt_number} 创建成功!请编辑入库明细后完成入库。', 'success')
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

        flash('入库单创建成功!请添加商品明细。', 'success')
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

        # 构建 products_data(供验证失败时重新渲染模板用)
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

        # 验证:至少要有一行商品明细
        has_items = False
        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_prices[i]:
                has_items = True
                # 验证数量和单价为正数
                try:
                    qty = float(quantities[i])
                    price = float(unit_prices[i])
                    if qty <= 0 or price < 0:
                        flash('数量必须大于0,单价不能为负数!', 'danger')
                        items_data = [{
                            'product_id': int(product_ids[i]),
                            'quantity': qty,
                            'unit_price': price
                        } for i in range(len(product_ids)) if product_ids[i]]
                        return render_template('purchase/stock_in_items.html',
                            title='编辑入库明细',
                            stock_in=stock_in,
                            products=products_data,
                            order_items=items_data)
                except (ValueError, TypeError):
                    flash('数量和单价必须是有效数字!', 'danger')
                    items_data = [{
                        'product_id': int(product_ids[i]) if product_ids[i] else 0,
                        'quantity': float(quantities[i]) if quantities[i] else 0,
                        'unit_price': float(unit_prices[i]) if unit_prices[i] else 0
                    } for i in range(len(product_ids)) if product_ids[i]]
                    return render_template('purchase/stock_in_items.html',
                        title='编辑入库明细',
                        stock_in=stock_in,
                        products=products_data,
                        order_items=items_data)

        if not has_items:
            flash('请至少添加一个商品明细!', 'danger')
            return render_template('purchase/stock_in_items.html',
                                 title='编辑入库明细',
                                 stock_in=stock_in,
                                 products=products_data,
                                 order_items=[])

        # 删除原有明细并重建
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
                    # 同步更新商品进价（与 quick_stock_in 保持一致）
                    product.purchase_price = unit_price

        stock_in.total_amount = total_amount
        db.session.commit()

        flash('商品明细保存成功!', 'success')
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
    # 获取已保存的入库明细
    saved_items = []
    for item in stock_in.items:
        saved_items.append({
            'product_id': item.product_id,
            'product_code': item.product.code,
            'product_name': item.product.name,
            'specification': item.product.specification or '',
            'unit': item.product.unit,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'remaining_quantity': float(item.quantity)
        })

    # 如果没有采购订单关联,使用已保存的明细
    if not stock_in.purchase_order and saved_items:
        order_items_data = saved_items
    elif stock_in.purchase_order:
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
    stock_in = StockIn.query.options(selectinload(StockIn.items).selectinload(StockInItem.product)).with_for_update().get_or_404(id)

    # 检查是否已经完成
    if stock_in.status == 'completed':
        flash('此入库单已经完成,不能重复确认!', 'danger')
        return redirect(url_for('purchase.index', tab='stockins'))

    # 检查状态是否为未入库
    if stock_in.status != 'pending':
        flash('此入库单状态异常,无法确认!', 'danger')
        return redirect(url_for('purchase.index', tab='stockins'))

    if len(stock_in.items) == 0:
        flash('请先添加商品明细!', 'danger')
        return redirect(url_for('purchase.edit_stock_in_items', id=stock_in.id))

    # 开始事务
    try:
        # 更新库存和记录流水
        for item in stock_in.items:
            warehouse = stock_in.warehouse
            # 锁定商品行，防止并发入库导致库存计算错误
            product = Product.query.with_for_update().get(item.product_id)
            if not product:
                continue

            # 记录当前库存(更新前)
            before_quantity = float(product.stock_quantity)

            # 更新商品库存
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

        # 如果有关联采购订单,重新计算已入库数量(基于所有已完成入库单)
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
                # 更新供应商应付余额
                supplier = order.supplier
                if supplier:
                    add_balance(supplier, "payable_balance", stock_in.total_amount)
            else:
                order.status = 'partial'

        # 更新入库单状态为已完成
        stock_in.status = 'completed'
        stock_in.updated_at = datetime.now()

        db.session.commit()
        flash('入库单完成!库存已更新。', 'success')

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
        flash('只有未入库状态的入库单可以删除!', 'danger')
        return redirect(url_for('purchase.index', tab='stockins'))

    db.session.delete(stock_in)
    db.session.commit()

    flash('入库单删除成功!', 'success')
    return redirect(url_for('purchase.index', tab='stockins'))

@bp.route('/stock-ins/<int:id>')
@login_required
def view_stock_in(id):
    stock_in = StockIn.query.get_or_404(id)
    return render_template('purchase/stock_in_view.html',
                         title='入库单详情',
                         stock_in=stock_in)


# ==================== 采购退货管理 ====================

@bp.route('/orders/<int:id>/quick-return', methods=['POST'])
@login_required
def quick_return(id):
    """快捷退货: 从采购订单直接退货(一次性完成)"""
    order = PurchaseOrder.query.options(
        selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.product)
    ).get_or_404(id)

    if order.status != 'completed':
        flash('只有已完成的采购订单可以退货！', 'danger')
        return redirect(url_for('purchase.index', tab='orders'))

    if len(order.items) == 0:
        flash('此订单没有商品明细，无法退货！', 'danger')
        return redirect(url_for('purchase.index', tab='orders'))

    if PurchaseReturn.query.filter_by(purchase_order_id=id, status='completed').first():
        flash('此订单已经退货，不能重复退货！', 'danger')
        return redirect(url_for('purchase.index', tab='orders'))

    try:
        today = datetime.now().strftime('%Y%m%d')
        last_return = PurchaseReturn.query.filter(PurchaseReturn.return_number.like(f'PR{today}%')).order_by(PurchaseReturn.id.desc()).first()
        if last_return:
            last_num = int(last_return.return_number[10:]) if len(last_return.return_number) > 10 else 0
            return_number = f'PR{today}{last_num + 1:03d}'
        else:
            return_number = f'PR{today}001'

        purchase_return = PurchaseReturn(
            return_number=return_number,
            purchase_order_id=order.id,
            warehouse_id=order.warehouse_id,
            return_date=datetime.now().date(),
            handler=current_user.username,
            notes='快捷退货',
            created_by=current_user.id,
            status='completed',
            total_amount=0
        )
        db.session.add(purchase_return)
        db.session.flush()

        total_amount = 0
        has_items = False
        for order_item in order.items:
            product = Product.query.with_for_update().get(order_item.product_id)
            if not product or float(product.stock_quantity) <= 0:
                continue

            return_qty = min(float(order_item.quantity), float(product.stock_quantity))
            if return_qty <= 0:
                continue

            has_items = True
            unit_price = float(order_item.unit_price)
            amount = return_qty * unit_price

            item = PurchaseReturnItem(
                return_id=purchase_return.id,
                product_id=product.id,
                quantity=return_qty,
                unit_price=unit_price,
                amount=amount
            )
            db.session.add(item)
            total_amount += amount

            before_quantity = float(product.stock_quantity)
            after_quantity = before_quantity - return_qty
            product.stock_quantity = after_quantity

            log = StockLog(
                product_id=product.id,
                warehouse_id=order.warehouse_id,
                change_type='return_out',
                quantity=return_qty,
                before_quantity=before_quantity,
                after_quantity=after_quantity,
                reference_id=purchase_return.id,
                reference_type='purchase_return',
                notes=f'采购退货: {return_number}',
                created_by=current_user.id
            )
            db.session.add(log)

        if not has_items:
            db.session.rollback()
            flash('没有可退货的商品（库存不足或已全部退货）！', 'warning')
            return redirect(url_for('purchase.index', tab='orders'))

        purchase_return.total_amount = total_amount

        # 减少供应商应付余额（退货=减少应付）
        supplier = order.supplier
        if supplier:
            sub_balance(supplier, 'payable_balance', total_amount)

        db.session.commit()
        flash(f'退货单 {return_number} 创建成功，库存已更新！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'退货失败: {str(e)}', 'danger')

    return redirect(url_for('purchase.index', tab='returns'))


@bp.route('/returns')
@login_required
def returns():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = PurchaseReturn.query
    if start_date:
        query = query.filter(PurchaseReturn.return_date >= start_date)
    if end_date:
        query = query.filter(PurchaseReturn.return_date <= end_date)

    returns_list = query.order_by(PurchaseReturn.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('purchase/returns.html',
                         title='采购退货管理',
                         returns=returns_list,
                         start_date=start_date or '',
                         end_date=end_date or '')


@bp.route('/returns/<int:id>')
@login_required
def view_return(id):
    purchase_return = PurchaseReturn.query.get_or_404(id)
    return render_template('purchase/return_view.html',
                         title='退货单详情',
                         purchase_return=purchase_return)


@bp.route('/returns/<int:id>/delete', methods=['POST'])
@login_required
def delete_return(id):
    purchase_return = PurchaseReturn.query.get_or_404(id)

    if purchase_return.status != 'pending':
        flash('只有未完成的退货单可以删除！', 'danger')
        return redirect(url_for('purchase.returns'))

    db.session.delete(purchase_return)
    db.session.commit()
    flash('退货单删除成功！', 'success')
    return redirect(url_for('purchase.returns'))


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
