from flask import render_template, redirect, url_for, flash, request, jsonify, Blueprint, make_response, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import Receipt, Payment, Expense, Customer, Supplier, SalesOrder, PurchaseOrder, SalesOrderItem, PurchaseOrderItem, SalesReturn, PurchaseReturn
from app.forms import ReceiptForm, PaymentForm, ExpenseForm
from sqlalchemy.exc import SQLAlchemyError
from app.utils import to_decimal, add_balance, sub_balance, generate_order_number, PAYMENT_METHOD_MAP, apply_excel_header_style, EXCEL_THIN_BORDER
from app.utils_order import match_reference_id_filter
import io

# 创建蓝图
bp = Blueprint('finance', __name__, url_prefix='/finance')


def calc_order_paid_amount(order_id, order_type):
    """计算订单已收/已付金额，支持逗号分隔的多订单ID。
    使用数据库层模糊匹配避免加载全表。
    reference_id 格式: "1" / "1,2,3" / "12,13"
    """
    if order_type == 'sales_order':
        rows = db.session.query(Receipt).filter(
            Receipt.reference_type == 'sales_order',
            Receipt.reference_id.isnot(None),
            match_reference_id_filter(Receipt, order_id)
        ).all()
        return float(sum(to_decimal(r.amount) for r in rows))
    else:
        rows = db.session.query(Payment).filter(
            Payment.reference_type == 'purchase_order',
            Payment.reference_id.isnot(None),
            match_reference_id_filter(Payment, order_id)
        ).all()
        return float(sum(to_decimal(p.amount) for p in rows))


@bp.route('/')
@login_required
def index():
    """财务管理首页"""
    # 获取最近30天的财务数据
    thirty_days_ago = datetime.now() - timedelta(days=30)

    # 统计收款
    total_receipts = db.session.query(db.func.sum(Receipt.amount)).filter(
        Receipt.receipt_date >= thirty_days_ago
    ).scalar() or 0

    # 统计付款
    total_payments = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.payment_date >= thirty_days_ago
    ).scalar() or 0

    # 统计费用
    total_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
        Expense.expense_date >= thirty_days_ago
    ).scalar() or 0

    # 最近收款记录
    recent_receipts = Receipt.query.order_by(Receipt.receipt_date.desc()).limit(10).all()

    return render_template('finance/index.html',
                         title='财务管理',
                         total_receipts=total_receipts,
                         total_payments=total_payments,
                         total_expenses=total_expenses,
                         recent_receipts=recent_receipts)

@bp.route('/receipts')
@login_required
def receipts():
    """收款管理"""
    receipts_list = Receipt.query.order_by(Receipt.receipt_date.desc()).all()
    customers = Customer.query.all()
    today = datetime.now().strftime('%Y-%m-%d')
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    return render_template('finance/receipts.html',
                         title='收款管理',
                         receipts=receipts_list,
                         customers=customers,
                         today=today,
                         thirty_days_ago=thirty_days_ago)

@bp.route('/receipt/add', methods=['GET', 'POST'])
@login_required
def add_receipt():
    """添加收款"""
    form = ReceiptForm()

    # 设置客户选择
    form.customer_id.choices = [(0, '请选择客户')] + [(c.id, c.name) for c in Customer.query.all()]

    if form.validate_on_submit():
        try:
            receipt_number = generate_order_number('RC', Receipt)

            receipt = Receipt(
                receipt_number=receipt_number,
                customer_id=form.customer_id.data,
                amount=form.amount.data,
                receipt_date=form.receipt_date.data,
                payment_method=form.payment_method.data,
                reference_type=form.reference_type.data,
                reference_id=form.reference_id.data.strip() if form.reference_id.data else None,
                notes=form.notes.data,
                created_by=current_user.id
            )
            db.session.add(receipt)

            customer = db.session.get(Customer, form.customer_id.data)
            if customer:
                sub_balance(customer, "receivable_balance", form.amount.data)

            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash('添加失败，请重试！', 'danger')
            return redirect(url_for('finance.add_receipt'))
        flash('收款记录已添加成功！', 'success')
        return redirect(url_for('finance.receipts'))

    customers = Customer.query.all()
    customers_data = [{"id": c.id, "code": c.code, "name": c.name, "phone": c.phone or "", "contact_person": c.contact_person or ""} for c in customers]
    sales_orders_raw = SalesOrder.query.filter_by(status='completed').all()
    # 计算每个订单的已收款金额
    sales_orders_data = []
    for order in sales_orders_raw:
        paid_amount = calc_order_paid_amount(order.id, 'sales_order')
        sales_orders_data.append({
            'order': order,
            'order_id': order.id,
            'paid_amount': paid_amount,
            'balance': to_decimal(order.total_amount or 0) - to_decimal(paid_amount)
        })
    return render_template('finance/receipt_edit.html',
                         title='添加收款',
                         form=form,
                         customers=customers_data,
                         sales_orders=sales_orders_data)

@bp.route('/payments')
@login_required
def payments():
    """付款管理"""
    payments_list = Payment.query.order_by(Payment.payment_date.desc()).all()
    suppliers = Supplier.query.all()
    return render_template('finance/payments.html',
                         title='付款管理',
                         payments=payments_list,
                         suppliers=suppliers)

@bp.route('/payment/add', methods=['GET', 'POST'])
@login_required
def add_payment():
    """添加付款"""
    form = PaymentForm()

    # 设置供应商选择
    form.supplier_id.choices = [(0, '请选择供应商')] + [(s.id, s.name) for s in Supplier.query.all()]

    if form.validate_on_submit():
        try:
            payment_number = generate_order_number('PY', Payment)

            payment = Payment(
                payment_number=payment_number,
                supplier_id=form.supplier_id.data,
                amount=form.amount.data,
                payment_date=form.payment_date.data,
                payment_method=form.payment_method.data,
                reference_type=form.reference_type.data,
                reference_id=form.reference_id.data.strip() if form.reference_id.data else None,
                notes=form.notes.data,
                created_by=current_user.id
            )
            db.session.add(payment)

            supplier = db.session.get(Supplier, form.supplier_id.data)
            if supplier:
                sub_balance(supplier, "payable_balance", form.amount.data)

            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash('添加失败，请重试！', 'danger')
            return redirect(url_for('finance.add_payment'))
        flash('付款记录已添加成功！', 'success')
        return redirect(url_for('finance.payments'))

    suppliers = Supplier.query.all()
    suppliers_data = [{"id": s.id, "code": s.code, "name": s.name, "phone": s.phone or "", "contact_person": s.contact_person or ""} for s in suppliers]
    purchase_orders_raw = PurchaseOrder.query.filter_by(status='completed').all()
    # 计算每个订单的已付款金额
    purchase_orders_data = []
    for order in purchase_orders_raw:
        paid_amount = calc_order_paid_amount(order.id, 'purchase_order')
        purchase_orders_data.append({
            'order': order,
            'order_id': order.id,
            'paid_amount': paid_amount,
            'balance': to_decimal(order.total_amount or 0) - to_decimal(paid_amount)
        })
    return render_template('finance/payment_edit.html',
                         title='添加付款',
                         form=form,
                         suppliers=suppliers_data,
                         purchase_orders=purchase_orders_data)

@bp.route('/expenses')
@login_required
def expenses():
    """费用管理"""
    expenses_list = Expense.query.order_by(Expense.expense_date.desc()).all()
    return render_template('finance/expenses.html',
                         title='费用管理',
                         expenses=expenses_list)

@bp.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    """添加费用"""
    form = ExpenseForm()

    if form.validate_on_submit():
        try:
            expense_number = generate_order_number('EX', Expense)

            expense = Expense(
                expense_number=expense_number,
                category=form.category.data,
                amount=form.amount.data,
                expense_date=form.expense_date.data,
                payee=form.payee.data,
                payment_method=form.payment_method.data,
                notes=form.notes.data,
                created_by=current_user.id
            )
            db.session.add(expense)
            db.session.commit()
            flash('费用记录已添加成功！', 'success')
            return redirect(url_for('finance.expenses'))
        except SQLAlchemyError:
            db.session.rollback()
            flash('添加失败，请重试！', 'danger')
            return redirect(url_for('finance.add_expense'))

    return render_template('finance/expense_edit.html', title='添加费用', form=form)

@bp.route('/expense/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(expense_id):
    """删除费用记录"""
    expense = db.session.get(Expense, expense_id)
    if expense is None:
        abort(404)
    try:
        db.session.delete(expense)
        db.session.commit()
        flash('费用记录已删除！', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        flash('删除费用记录失败，请稍后重试！', 'danger')
    return redirect(url_for('finance.expenses'))

@bp.route('/profit-analysis')
@login_required
def profit_analysis():
    """利润分析"""
    # 按月汇总已完成订单的销售金额和采购金额
    # 利润 = 销售金额 - 采购成本（毛利口径，不含费用）
    sales_data = db.session.query(
        db.func.strftime('%Y-%m', SalesOrder.order_date).label('month'),
        db.func.sum(SalesOrder.total_amount).label('sales_amount')
    ).filter(SalesOrder.status == 'completed').group_by('month').all()

    purchase_data = db.session.query(
        db.func.strftime('%Y-%m', PurchaseOrder.order_date).label('month'),
        db.func.sum(PurchaseOrder.total_amount).label('purchase_amount')
    ).filter(PurchaseOrder.status == 'completed').group_by('month').all()

    return render_template('finance/profit_analysis.html',
                         title='利润分析',
                         sales_data=sales_data,
                         purchase_data=purchase_data)

@bp.route('/receipt/<int:receipt_id>')
@login_required
def view_receipt(receipt_id):
    """查看收款详情"""
    receipt = db.session.get(Receipt, receipt_id)
    if receipt is None:
        abort(404)
    return render_template('finance/receipt_view.html',
                         title='收款详情',
                         receipt=receipt,
                         db=db,
                         SalesOrder=SalesOrder)

@bp.route('/receipt/<int:receipt_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_receipt(receipt_id):
    """编辑收款"""
    if request.method == 'POST':
        receipt = db.session.query(Receipt).filter(Receipt.id == receipt_id).with_for_update().first()
    else:
        receipt = db.session.get(Receipt, receipt_id)
    if receipt is None:
        abort(404)
    form = ReceiptForm(obj=receipt)
    form.customer_id.choices = [(0, '请选择客户')] + [(c.id, c.name) for c in Customer.query.all()]

    if form.validate_on_submit():
        original_amount = receipt.amount
        original_customer_id = receipt.customer_id
        receipt.customer_id = form.customer_id.data
        receipt.amount = form.amount.data
        receipt.receipt_date = form.receipt_date.data
        receipt.payment_method = form.payment_method.data
        receipt.reference_type = form.reference_type.data
        receipt.reference_id = form.reference_id.data.strip() if form.reference_id.data else None
        receipt.notes = form.notes.data

        # 更新客户应收余额（收款减少应收）
        if original_customer_id != receipt.customer_id:
            # 客户变更：回滚旧客户应收，扣减新客户应收
            old_customer = db.session.get(Customer, original_customer_id)
            if old_customer:
                add_balance(old_customer, "receivable_balance", original_amount)
            new_customer = db.session.get(Customer, receipt.customer_id)
            if new_customer:
                sub_balance(new_customer, "receivable_balance", receipt.amount)
        elif original_amount != receipt.amount:
            # 金额变更：先回滚旧金额，再扣减新金额
            customer = db.session.get(Customer, receipt.customer_id)
            if customer:
                add_balance(customer, "receivable_balance", original_amount)
                sub_balance(customer, "receivable_balance", receipt.amount)

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash('收款记录更新失败，请稍后重试！', 'danger')
            return redirect(url_for('finance.edit_receipt', receipt_id=receipt_id))
        flash('收款记录已更新成功！', 'success')
        return redirect(url_for('finance.view_receipt', receipt_id=receipt.id))

    customers = Customer.query.all()
    customers_data = [{"id": c.id, "code": c.code, "name": c.name, "phone": c.phone or "", "contact_person": c.contact_person or ""} for c in customers]
    # Build sales_orders_data for edit mode too
    sales_orders_raw = SalesOrder.query.filter_by(status='completed').all()
    sales_orders_data = []
    for order in sales_orders_raw:
        paid_amount = calc_order_paid_amount(order.id, 'sales_order')
        sales_orders_data.append({
            'order': order,
            'order_id': order.id,
            'paid_amount': paid_amount,
            'balance': to_decimal(order.total_amount or 0) - to_decimal(paid_amount)
        })
    return render_template('finance/receipt_edit.html',
                         title='编辑收款',
                         receipt=receipt,
                         customers=customers_data,
                         sales_orders=sales_orders_data,
                         form=form)

@bp.route('/receipt/<int:receipt_id>/delete', methods=['POST'])
@login_required
def delete_receipt(receipt_id):
    """删除收款记录，同时回滚客户应收余额"""
    receipt = db.session.get(Receipt, receipt_id)
    if receipt is None:
        abort(404)
    try:
        # 回滚客户应收余额（收款时减应收，删除时加回应收）
        customer = receipt.customer
        if customer:
            add_balance(customer, 'receivable_balance', receipt.amount)
        db.session.delete(receipt)
        db.session.commit()
        flash('收款记录已删除！', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        flash('删除收款记录失败，请稍后重试！', 'danger')
    return redirect(url_for('finance.receipts'))

@bp.route('/payment/<int:payment_id>')
@login_required
def view_payment(payment_id):
    """查看付款详情"""
    payment = db.session.get(Payment, payment_id)
    if payment is None:
        abort(404)
    return render_template('finance/payment_view.html',
                         title='付款详情',
                         payment=payment,
                         db=db,
                         PurchaseOrder=PurchaseOrder)

@bp.route('/payment/<int:payment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_payment(payment_id):
    """编辑付款"""
    if request.method == 'POST':
        payment = db.session.query(Payment).filter(Payment.id == payment_id).with_for_update().first()
    else:
        payment = db.session.get(Payment, payment_id)
    if payment is None:
        abort(404)
    form = PaymentForm(obj=payment)
    form.supplier_id.choices = [(0, '请选择供应商')] + [(s.id, s.name) for s in Supplier.query.all()]

    if form.validate_on_submit():
        original_amount = payment.amount
        original_supplier_id = payment.supplier_id
        payment.supplier_id = form.supplier_id.data
        payment.amount = form.amount.data
        payment.payment_date = form.payment_date.data
        payment.payment_method = form.payment_method.data
        payment.reference_type = form.reference_type.data
        payment.reference_id = form.reference_id.data.strip() if form.reference_id.data else None
        payment.notes = form.notes.data

        # 更新供应商应付余额（付款减少应付）
        if original_supplier_id != payment.supplier_id:
            # 供应商变更：回滚旧供应商应付，扣减新供应商应付
            old_supplier = db.session.get(Supplier, original_supplier_id)
            if old_supplier:
                add_balance(old_supplier, "payable_balance", original_amount)
            new_supplier = db.session.get(Supplier, payment.supplier_id)
            if new_supplier:
                sub_balance(new_supplier, "payable_balance", payment.amount)
        elif original_amount != payment.amount:
            # 金额变更：先回滚旧金额，再扣减新金额
            supplier = db.session.get(Supplier, payment.supplier_id)
            if supplier:
                add_balance(supplier, "payable_balance", original_amount)
                sub_balance(supplier, "payable_balance", payment.amount)

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash('付款记录更新失败，请稍后重试！', 'danger')
            return redirect(url_for('finance.edit_payment', payment_id=payment_id))
        flash('付款记录已更新成功！', 'success')
        return redirect(url_for('finance.view_payment', payment_id=payment.id))

    suppliers = Supplier.query.all()
    suppliers_data = [{"id": s.id, "code": s.code, "name": s.name, "phone": s.phone or "", "contact_person": s.contact_person or ""} for s in suppliers]
    # Build purchase_orders_data for edit mode too
    purchase_orders_raw = PurchaseOrder.query.filter_by(status='completed').all()
    purchase_orders_data = []
    for order in purchase_orders_raw:
        paid_amount = calc_order_paid_amount(order.id, 'purchase_order')
        purchase_orders_data.append({
            'order': order,
            'order_id': order.id,
            'paid_amount': paid_amount,
            'balance': to_decimal(order.total_amount or 0) - to_decimal(paid_amount)
        })
    return render_template('finance/payment_edit.html',
                         title='编辑付款',
                         payment=payment,
                         suppliers=suppliers_data,
                         purchase_orders=purchase_orders_data,
                         form=form)

@bp.route('/payment/<int:payment_id>/delete', methods=['POST'])
@login_required
def delete_payment(payment_id):
    """删除付款记录，同时回滚供应商应付余额"""
    payment = db.session.get(Payment, payment_id)
    if payment is None:
        abort(404)
    try:
        # 回滚供应商应付余额（付款减少应付，删除时加回）
        supplier = payment.supplier
        if supplier:
            add_balance(supplier, 'payable_balance', payment.amount)
        db.session.delete(payment)
        db.session.commit()
        flash('付款记录已删除！', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        flash('删除付款记录失败，请稍后重试！', 'danger')
    return redirect(url_for('finance.payments'))

@bp.route('/api/financial-summary')
@login_required
def financial_summary_api():
    """财务摘要API"""
    today = datetime.now().date()

    # 今日收款
    today_receipts = db.session.query(db.func.sum(Receipt.amount)).filter(
        Receipt.receipt_date == today
    ).scalar() or 0

    # 今日付款
    today_payments = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.payment_date == today
    ).scalar() or 0

    # 今日费用
    today_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
        Expense.expense_date == today
    ).scalar() or 0

    return jsonify({
        'today_receipts': float(today_receipts),
        'today_payments': float(today_payments),
        'today_expenses': float(today_expenses),
        'today_net_receipts': float(today_receipts - today_payments - today_expenses)
    })

@bp.route('/ar-ap-search')
@login_required
def ar_ap_search():
    """应收应付检索页面"""
    customers = Customer.query.all()
    suppliers = Supplier.query.all()
    customers_data = [{"id": c.id, "code": c.code, "name": c.name, "phone": c.phone or "", "contact_person": c.contact_person or ""} for c in customers]
    suppliers_data = [{"id": s.id, "code": s.code, "name": s.name, "phone": s.phone or "", "contact_person": s.contact_person or ""} for s in suppliers]

    # 获取查询参数
    customer_id = request.args.get('customer_id', type=int)
    supplier_id = request.args.get('supplier_id', type=int)

    customer_info = None
    customer_total_amount = 0  # 客户订单总金额(应收总额)
    customer_received_amount = 0  # 已收款金额
    customer_ar_balance = 0  # 应收余额
    customer_receipts = []
    customer_orders = []

    supplier_info = None
    supplier_total_amount = 0  # 供应商订单总金额(应付总额)
    supplier_paid_amount = 0  # 已付款金额
    supplier_ap_balance = 0  # 应付余额
    supplier_payments = []
    supplier_orders = []

    customer_returns = []
    customer_return_amount = 0
    supplier_returns = []
    supplier_return_amount = 0

    # 按客户检索应收：关联查询销售订单、收款记录、退货记录
    if customer_id:
        customer_info = db.session.get(Customer, customer_id)
        if customer_info is None:
            abort(404)
        # 获取该客户的所有销售订单(非草稿、非取消状态)
        customer_orders = SalesOrder.query.filter(
            SalesOrder.customer_id == customer_id,
            SalesOrder.status.in_(['confirmed', 'partial', 'completed'])
        ).order_by(SalesOrder.order_date.desc()).all()

        # 为每个订单添加商品名称（N+1优化：一次性加载所有订单的明细）
        customer_order_ids = [o.id for o in customer_orders]
        all_items = db.session.query(SalesOrderItem).filter(SalesOrderItem.order_id.in_(customer_order_ids)).all() if customer_order_ids else []
        items_by_order = {}
        for item in all_items:
            items_by_order.setdefault(item.order_id, []).append(item)
        for order in customer_orders:
            items = items_by_order.get(order.id, [])
            product_names = [item.product.name for item in items if item.product]
            order.product_names = '、'.join(product_names) if product_names else None

        # 计算应收总额
        customer_total_amount = sum(to_decimal(o.total_amount) for o in customer_orders)
        # 获取该客户的所有收款记录
        customer_receipts = Receipt.query.filter_by(customer_id=customer_id).order_by(Receipt.receipt_date.desc()).all()
        # 计算已收款总额
        customer_received_amount = sum(to_decimal(r.amount) for r in customer_receipts)
        # 计算退货金额（需从应收中扣除）
        customer_returns = SalesReturn.query.filter(
            SalesReturn.sales_order_id.in_(customer_order_ids),
            SalesReturn.status == 'completed'
        ).order_by(SalesReturn.return_date.desc()).all() if customer_order_ids else []
        customer_return_amount = sum(to_decimal(r.total_amount) for r in customer_returns)
        # 应收余额 = 订单总额 - 已收款总额 - 退货金额
        customer_ar_balance = customer_total_amount - customer_received_amount - customer_return_amount

    # 按供应商检索应付：关联查询采购订单、付款记录、退货记录
    if supplier_id:
        supplier_info = db.session.get(Supplier, supplier_id)
        if supplier_info is None:
            abort(404)
        # 获取该供应商的所有采购订单(非草稿、非取消状态)
        supplier_orders = PurchaseOrder.query.filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.status.in_(['confirmed', 'partial', 'completed'])
        ).order_by(PurchaseOrder.order_date.desc()).all()

        # 为每个订单添加商品名称（N+1优化：一次性加载所有订单的明细）
        supplier_order_ids = [o.id for o in supplier_orders]
        all_supplier_items = db.session.query(PurchaseOrderItem).filter(PurchaseOrderItem.order_id.in_(supplier_order_ids)).all() if supplier_order_ids else []
        supplier_items_by_order = {}
        for item in all_supplier_items:
            supplier_items_by_order.setdefault(item.order_id, []).append(item)
        for order in supplier_orders:
            items = supplier_items_by_order.get(order.id, [])
            product_names = [item.product.name for item in items if item.product]
            order.product_names = '、'.join(product_names) if product_names else None

        # 计算应付总额
        supplier_total_amount = sum(to_decimal(o.total_amount) for o in supplier_orders)
        # 获取该供应商的所有付款记录
        supplier_payments = Payment.query.filter_by(supplier_id=supplier_id).order_by(Payment.payment_date.desc()).all()
        # 计算已付款总额
        supplier_paid_amount = sum(to_decimal(p.amount) for p in supplier_payments)
        # 计算退货金额（需从应付中扣除）
        supplier_returns = PurchaseReturn.query.filter(
            PurchaseReturn.purchase_order_id.in_(supplier_order_ids),
            PurchaseReturn.status == 'completed'
        ).order_by(PurchaseReturn.return_date.desc()).all() if supplier_order_ids else []
        supplier_return_amount = sum(to_decimal(r.total_amount) for r in supplier_returns)
        # 应付余额 = 订单总额 - 已付款总额 - 退货金额
        supplier_ap_balance = supplier_total_amount - supplier_paid_amount - supplier_return_amount

    return render_template('finance/ar_ap_search.html',
                         title='应收应付检索',
                         customers=customers_data,
                         suppliers=suppliers_data,
                         customer_info=customer_info,
                         customer_total_amount=customer_total_amount,
                         customer_received_amount=customer_received_amount,
                         customer_ar_balance=customer_ar_balance,
                         customer_receipts=customer_receipts,
                         customer_orders=customer_orders,
                         customer_return_amount=customer_return_amount if customer_id else 0,
                         customer_returns=customer_returns if customer_id else [],
                         supplier_info=supplier_info,
                         supplier_total_amount=supplier_total_amount,
                         supplier_paid_amount=supplier_paid_amount,
                         supplier_ap_balance=supplier_ap_balance,
                         supplier_return_amount=supplier_return_amount if supplier_id else 0,
                         supplier_returns=supplier_returns if supplier_id else [],
                         supplier_payments=supplier_payments,
                         supplier_orders=supplier_orders)

@bp.route('/api/customer-ar/<int:customer_id>')
@login_required
def customer_ar_detail(customer_id):
    """获取客户应收详情API"""
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        abort(404)
    receipts = Receipt.query.filter_by(customer_id=customer_id).order_by(Receipt.receipt_date.desc()).all()
    orders = SalesOrder.query.filter_by(customer_id=customer_id).order_by(SalesOrder.order_date.desc()).all()

    receipt_data = [{
        'id': r.id,
        'receipt_number': r.receipt_number,
        'amount': float(r.amount),
        'receipt_date': r.receipt_date.strftime('%Y-%m-%d'),
        'payment_method': r.payment_method
    } for r in receipts]

    order_data = [{
        'id': o.id,
        'order_number': o.order_number,
        'total_amount': float(o.total_amount),
        'order_date': o.order_date.strftime('%Y-%m-%d'),
        'status': o.status
    } for o in orders]

    return jsonify({
        'customer': {
            'id': customer.id,
            'code': customer.code,
            'name': customer.name,
            'contact_person': customer.contact_person,
            'phone': customer.phone,
            'receivable_balance': float(customer.receivable_balance)
        },
        'receipts': receipt_data,
        'orders': order_data
    })

@bp.route('/api/supplier-ap/<int:supplier_id>')
@login_required
def supplier_ap_detail(supplier_id):
    """获取供应商应付详情API"""
    supplier = db.session.get(Supplier, supplier_id)
    if supplier is None:
        abort(404)
    payments = Payment.query.filter_by(supplier_id=supplier_id).order_by(Payment.payment_date.desc()).all()
    orders = PurchaseOrder.query.filter_by(supplier_id=supplier_id).order_by(PurchaseOrder.order_date.desc()).all()

    payment_data = [{
        'id': p.id,
        'payment_number': p.payment_number,
        'amount': float(p.amount),
        'payment_date': p.payment_date.strftime('%Y-%m-%d'),
        'payment_method': p.payment_method
    } for p in payments]

    order_data = [{
        'id': o.id,
        'order_number': o.order_number,
        'total_amount': float(o.total_amount),
        'order_date': o.order_date.strftime('%Y-%m-%d'),
        'status': o.status
    } for o in orders]

    return jsonify({
        'supplier': {
            'id': supplier.id,
            'code': supplier.code,
            'name': supplier.name,
            'contact_person': supplier.contact_person,
            'phone': supplier.phone,
            'payable_balance': float(supplier.payable_balance)
        },
        'payments': payment_data,
        'orders': order_data
    })

@bp.route('/export-customer-ar/<int:customer_id>')
@login_required
def export_customer_ar(customer_id):
    """导出客户应收报表"""
    from urllib.parse import quote
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    # TODO: 添加业务级权限检查，例如检查当前用户是否有权访问该客户的数据
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        abort(404)

    # 获取销售订单
    orders = SalesOrder.query.filter(
        SalesOrder.customer_id == customer_id,
        SalesOrder.status.in_(['confirmed', 'partial', 'completed'])
    ).order_by(SalesOrder.order_date.desc()).all()

    # 获取收款记录
    receipts = Receipt.query.filter_by(customer_id=customer_id).order_by(Receipt.receipt_date.desc()).all()

    # 计算退货金额
    customer_order_ids = [o.id for o in orders]
    return_records = SalesReturn.query.filter(
        SalesReturn.sales_order_id.in_(customer_order_ids),
        SalesReturn.status == 'completed'
    ).all() if customer_order_ids else []
    return_amount = sum(to_decimal(r.total_amount) for r in return_records)

    # 计算金额
    total_amount = sum(to_decimal(o.total_amount) for o in orders)
    received_amount = sum(to_decimal(r.amount) for r in receipts)
    balance = total_amount - received_amount - return_amount

    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "客户应收报表"

    # 样式定义
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
    money_format = '#,##0.00'

    # 写入标题
    ws['A1'] = '客户应收报表'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'] = '客户名称'
    ws['B2'] = customer.name
    ws['A3'] = '客户编码'
    ws['B3'] = customer.code
    ws['A4'] = '联系电话'
    ws['B4'] = customer.phone or '-'
    ws['A5'] = '总应收金额'
    ws['B5'] = total_amount
    ws['B5'].number_format = money_format
    ws['A6'] = '已收金额'
    ws['B6'] = received_amount
    ws['B6'].number_format = money_format
    ws['A7'] = '退货金额'
    ws['B7'] = return_amount
    ws['B7'].number_format = money_format
    ws['A8'] = '应收余额'
    ws['B8'] = balance
    ws['B8'].number_format = money_format

    # 销售订单
    ws.append([])
    ws.append(['销售订单'])
    ws['A' + str(ws.max_row)].font = header_font
    ws.append(['订单编号', '订单日期', '订单金额', '订单状态', '商品名称', '备注'])
    for cell in ws[ws.max_row]:
        cell.font = header_font
        cell.fill = header_fill

    status_map = {'draft': '草稿', 'confirmed': '已确认', 'partial': '部分完成', 'completed': '已完成', 'cancelled': '已取消'}
    for order in orders:
        items = SalesOrderItem.query.filter_by(order_id=order.id).all()
        product_names = '、'.join([item.product.name for item in items if item.product]) if items else '-'
        ws.append([
            order.order_number,
            order.order_date.strftime('%Y-%m-%d'),
            float(order.total_amount),
            status_map.get(order.status, order.status),
            product_names,
            order.notes or '-'
        ])
        ws.cell(row=ws.max_row, column=3).number_format = money_format

    # 收款记录
    ws.append([])
    ws.append(['收款记录'])
    ws['A' + str(ws.max_row)].font = header_font
    ws.append(['收款单号', '收款日期', '收款金额', '支付方式', '备注'])
    for cell in ws[ws.max_row]:
        cell.font = header_font
        cell.fill = header_fill

    for receipt in receipts:
        ws.append([
            receipt.receipt_number,
            receipt.receipt_date.strftime('%Y-%m-%d'),
            float(receipt.amount),
            PAYMENT_METHOD_MAP.get(receipt.payment_method, receipt.payment_method or ''),
            receipt.notes or '-'
        ])
        ws.cell(row=ws.max_row, column=3).number_format = money_format

    # 调整列宽
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 30
    ws.column_dimensions['F'].width = 20

    # 保存到内存
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    filename = f'customer_ar_{customer.code}_{datetime.now().strftime("%Y%m%d")}.xlsx'
    response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quote(filename)}'
    return response

@bp.route('/export-receipts')
@login_required
def export_receipts():
    """导出收款记录"""
    from urllib.parse import quote
    from openpyxl import Workbook

    receipts_list = Receipt.query.order_by(Receipt.receipt_date.desc()).all()

    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = '收款记录'

    # 写入表头
    headers = ['收款单号', '客户', '收款金额', '收款日期', '支付方式', '关联订单', '备注', '创建时间']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    apply_excel_header_style(ws, 1, len(headers))

    # 写入数据
    for row, receipt in enumerate(receipts_list, 2):
        ws.cell(row=row, column=1, value=receipt.receipt_number).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=2, value=receipt.customer.name if receipt.customer else '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=3, value=float(receipt.amount) if receipt.amount else 0).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=3).number_format = '#,##0.00'
        ws.cell(row=row, column=4, value=receipt.receipt_date.strftime('%Y-%m-%d') if receipt.receipt_date else '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=5, value=PAYMENT_METHOD_MAP.get(receipt.payment_method, receipt.payment_method or '')).border = EXCEL_THIN_BORDER
        # 解析reference_id(逗号分隔的订单ID)显示订单号
        ref_orders = ''
        if receipt.reference_type == 'sales_order' and receipt.reference_id:
            try:
                ids = [int(oid.strip()) for oid in receipt.reference_id.split(',') if oid.strip()]
                orders = SalesOrder.query.filter(SalesOrder.id.in_(ids)).all()
                ref_orders = ','.join([o.order_number for o in orders]) or receipt.reference_id
            except (ValueError, TypeError):
                ref_orders = receipt.reference_id or ''
        ws.cell(row=row, column=6, value=ref_orders).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=7, value=receipt.notes or '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=8, value=receipt.created_at.strftime('%Y-%m-%d %H:%M:%S') if receipt.created_at else '').border = EXCEL_THIN_BORDER

    # 设置列宽
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 30
    ws.column_dimensions['H'].width = 20

    # 保存到BytesIO
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f'receipts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quote(filename)}'
    return response


@bp.route('/export-payments')
@login_required
def export_payments():
    """导出付款记录"""
    from urllib.parse import quote
    from openpyxl import Workbook

    payments_list = Payment.query.order_by(Payment.payment_date.desc()).all()

    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = '付款记录'

    # 写入表头
    headers = ['付款单号', '供应商', '付款金额', '付款日期', '支付方式', '关联订单', '备注', '创建时间']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    apply_excel_header_style(ws, 1, len(headers))

    # 写入数据
    for row, payment in enumerate(payments_list, 2):
        ws.cell(row=row, column=1, value=payment.payment_number).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=2, value=payment.supplier.name if payment.supplier else '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=3, value=float(payment.amount) if payment.amount else 0).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=3).number_format = '#,##0.00'
        ws.cell(row=row, column=4, value=payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=5, value=PAYMENT_METHOD_MAP.get(payment.payment_method, payment.payment_method or '')).border = EXCEL_THIN_BORDER
        # 解析reference_id(逗号分隔的订单ID)显示订单号
        ref_orders = ''
        if payment.reference_type == 'purchase_order' and payment.reference_id:
            try:
                ids = [int(oid.strip()) for oid in payment.reference_id.split(',') if oid.strip()]
                orders = PurchaseOrder.query.filter(PurchaseOrder.id.in_(ids)).all()
                ref_orders = ','.join([o.order_number for o in orders]) or payment.reference_id
            except (ValueError, TypeError):
                ref_orders = payment.reference_id or ''
        ws.cell(row=row, column=6, value=ref_orders).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=7, value=payment.notes or '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=8, value=payment.created_at.strftime('%Y-%m-%d %H:%M:%S') if payment.created_at else '').border = EXCEL_THIN_BORDER

    # 设置列宽
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 30
    ws.column_dimensions['H'].width = 20

    # 保存到BytesIO
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f'payments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quote(filename)}'
    return response


@bp.route('/export-profit-analysis')
@login_required
def export_profit_analysis():
    """导出利润分析报表"""
    from urllib.parse import quote
    from openpyxl import Workbook

    # 获取销售数据
    sales_data = db.session.query(
        db.func.strftime('%Y-%m', SalesOrder.order_date).label('month'),
        db.func.sum(SalesOrder.total_amount).label('sales_amount')
    ).filter(SalesOrder.status == 'completed').group_by('month').all()

    # 获取采购数据
    purchase_data = db.session.query(
        db.func.strftime('%Y-%m', PurchaseOrder.order_date).label('month'),
        db.func.sum(PurchaseOrder.total_amount).label('purchase_amount')
    ).filter(PurchaseOrder.status == 'completed').group_by('month').all()

    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = '利润分析'

    headers = ['月份', '销售金额', '采购成本', '毛利', '毛利率(%)']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    apply_excel_header_style(ws, 1, len(headers))

    # 合并数据(以销售数据月份为基准)
    sales_dict = {str(s.month): float(s.sales_amount or 0) for s in sales_data}
    purchase_dict = {str(p.month): float(p.purchase_amount or 0) for p in purchase_data}
    all_months = sorted(set(sales_dict.keys()) | set(purchase_dict.keys()), reverse=True)

    for row_idx, month in enumerate(all_months, 2):
        sales = sales_dict.get(month, 0)
        purchase = purchase_dict.get(month, 0)
        profit = sales - purchase
        margin = (profit / sales * 100) if sales > 0 else 0

        ws.cell(row=row_idx, column=1, value=month).border = EXCEL_THIN_BORDER
        ws.cell(row=row_idx, column=2, value=sales).border = EXCEL_THIN_BORDER
        ws.cell(row=row_idx, column=2).number_format = '#,##0.00'
        ws.cell(row=row_idx, column=3, value=purchase).border = EXCEL_THIN_BORDER
        ws.cell(row=row_idx, column=3).number_format = '#,##0.00'
        ws.cell(row=row_idx, column=4, value=profit).border = EXCEL_THIN_BORDER
        ws.cell(row=row_idx, column=4).number_format = '#,##0.00'
        ws.cell(row=row_idx, column=5, value=margin).border = EXCEL_THIN_BORDER
        ws.cell(row=row_idx, column=5).number_format = '0.00'

    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 12

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f'profit_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quote(filename)}'
    return response


@bp.route('/export-expenses')
@login_required
def export_expenses():
    """导出费用报表"""
    from urllib.parse import quote
    from openpyxl import Workbook

    expenses_list = Expense.query.order_by(Expense.expense_date.desc()).all()

    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = '费用报表'

    # 写入表头
    headers = ['费用单号', '费用类别', '费用金额', '费用日期', '收款方', '付款方式', '备注', '操作人', '创建时间']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    apply_excel_header_style(ws, 1, len(headers))

    # 写入数据
    for row, expense in enumerate(expenses_list, 2):
        ws.cell(row=row, column=1, value=expense.expense_number).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=2, value=expense.category).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=3, value=float(expense.amount) if expense.amount else 0).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=3).number_format = '#,##0.00'
        ws.cell(row=row, column=4, value=expense.expense_date.strftime('%Y-%m-%d') if expense.expense_date else '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=5, value=expense.payee or '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=6, value=PAYMENT_METHOD_MAP.get(expense.payment_method, expense.payment_method or '')).border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=7, value=expense.notes or '').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=8, value=expense.creator.username if expense.creator else '系统').border = EXCEL_THIN_BORDER
        ws.cell(row=row, column=9, value=expense.created_at.strftime('%Y-%m-%d %H:%M:%S') if expense.created_at else '').border = EXCEL_THIN_BORDER

    # 设置列宽
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 20
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 30
    ws.column_dimensions['H'].width = 12
    ws.column_dimensions['I'].width = 20

    # 保存到BytesIO
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f'expenses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quote(filename)}'
    return response

@bp.route('/export-supplier-ap/<int:supplier_id>')
@login_required
def export_supplier_ap(supplier_id):
    """导出供应商应付报表"""
    from urllib.parse import quote
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    # TODO: 添加业务级权限检查，例如检查当前用户是否有权访问该供应商的数据
    supplier = db.session.get(Supplier, supplier_id)
    if supplier is None:
        abort(404)

    # 获取采购订单
    orders = PurchaseOrder.query.filter(
        PurchaseOrder.supplier_id == supplier_id,
        PurchaseOrder.status.in_(['confirmed', 'partial', 'completed'])
    ).order_by(PurchaseOrder.order_date.desc()).all()

    # 获取付款记录
    payments = Payment.query.filter_by(supplier_id=supplier_id).order_by(Payment.payment_date.desc()).all()

    # 计算退货金额
    supplier_order_ids = [o.id for o in orders]
    return_records = PurchaseReturn.query.filter(
        PurchaseReturn.purchase_order_id.in_(supplier_order_ids),
        PurchaseReturn.status == 'completed'
    ).all() if supplier_order_ids else []
    return_amount = sum(to_decimal(r.total_amount) for r in return_records)

    # 计算金额
    total_amount = sum(to_decimal(o.total_amount) for o in orders)
    paid_amount = sum(to_decimal(p.amount) for p in payments)
    balance = total_amount - paid_amount - return_amount

    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "供应商应付报表"

    # 样式定义
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="FFE5CC", end_color="FFE5CC", fill_type="solid")
    money_format = '#,##0.00'

    # 写入标题
    ws['A1'] = '供应商应付报表'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'] = '供应商名称'
    ws['B2'] = supplier.name
    ws['A3'] = '供应商编码'
    ws['B3'] = supplier.code
    ws['A4'] = '联系电话'
    ws['B4'] = supplier.phone or '-'
    ws['A5'] = '总应付金额'
    ws['B5'] = total_amount
    ws['B5'].number_format = money_format
    ws['A6'] = '已付金额'
    ws['B6'] = paid_amount
    ws['B6'].number_format = money_format
    ws['A7'] = '退货金额'
    ws['B7'] = return_amount
    ws['B7'].number_format = money_format
    ws['A8'] = '应付余额'
    ws['B8'] = balance
    ws['B8'].number_format = money_format

    # 采购订单
    ws.append([])
    ws.append(['采购订单'])
    ws['A' + str(ws.max_row)].font = header_font
    ws.append(['订单编号', '订单日期', '订单金额', '订单状态', '商品名称', '备注'])
    for cell in ws[ws.max_row]:
        cell.font = header_font
        cell.fill = header_fill

    status_map = {'draft': '草稿', 'confirmed': '已确认', 'partial': '部分完成', 'completed': '已完成', 'cancelled': '已取消'}
    for order in orders:
        items = PurchaseOrderItem.query.filter_by(order_id=order.id).all()
        product_names = '、'.join([item.product.name for item in items if item.product]) if items else '-'
        ws.append([
            order.order_number,
            order.order_date.strftime('%Y-%m-%d'),
            float(order.total_amount),
            status_map.get(order.status, order.status),
            product_names,
            order.notes or '-'
        ])
        ws.cell(row=ws.max_row, column=3).number_format = money_format

    # 付款记录
    ws.append([])
    ws.append(['付款记录'])
    ws['A' + str(ws.max_row)].font = header_font
    ws.append(['付款单号', '付款日期', '付款金额', '支付方式', '备注'])
    for cell in ws[ws.max_row]:
        cell.font = header_font
        cell.fill = header_fill

    for payment in payments:
        ws.append([
            payment.payment_number,
            payment.payment_date.strftime('%Y-%m-%d'),
            float(payment.amount),
            PAYMENT_METHOD_MAP.get(payment.payment_method, payment.payment_method or ''),
            payment.notes or '-'
        ])
        ws.cell(row=ws.max_row, column=3).number_format = money_format

    # 调整列宽
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 30
    ws.column_dimensions['F'].width = 20

    # 保存到内存
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    filename = f'supplier_ap_{supplier.code}_{datetime.now().strftime("%Y%m%d")}.xlsx'
    response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quote(filename)}'
    return response
