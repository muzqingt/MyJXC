from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Supplier, Customer, Warehouse, PurchaseOrder, Payment, SalesOrder, Receipt, StockIn, StockOut, StockLog, Log
from app.forms import SupplierForm, CustomerForm, WarehouseForm
from flask import Blueprint
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# 创建蓝图
bp = Blueprint('partner', __name__, url_prefix='/partner')

# 供应商管理
@bp.route('/suppliers')
@login_required
def suppliers():
    suppliers = Supplier.query.order_by(Supplier.created_at.desc()).limit(500).all()
    return render_template('product/suppliers.html',
                         title='供应商管理',
                         suppliers=suppliers)

@bp.route('/suppliers/new', methods=['GET', 'POST'])
@login_required
def add_supplier():
    form = SupplierForm()

    if form.validate_on_submit():
        # 检查编号是否已存在
        if Supplier.query.filter_by(code=form.code.data).first():
            flash('供应商编号已存在，请使用其他编号！', 'danger')
            return render_template('product/supplier_edit.html', title='添加供应商', form=form, action='new')

        supplier = Supplier(
            code=form.code.data,
            name=form.name.data,
            contact_person=form.contact_person.data,
            phone=form.phone.data,
            address=form.address.data,
            email=form.email.data
        )

        db.session.add(supplier)
        log = Log(
            user_id=current_user.id,
            action='添加供应商',
            details=f'添加供应商: {supplier.code} - {supplier.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('编码已存在，请使用其他编码！', 'danger')
            return render_template('product/supplier_edit.html', title='添加供应商', form=form, action='new')
        except SQLAlchemyError:
            db.session.rollback()
            flash('数据库错误，操作失败！', 'danger')
            return render_template('product/supplier_edit.html', title='添加供应商', form=form, action='new')

        flash('供应商添加成功！', 'success')
        return redirect(url_for('partner.suppliers'))

    return render_template('product/supplier_edit.html',
                         title='添加供应商',
                         form=form,
                         action='new')

@bp.route('/suppliers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_supplier(id):
    supplier = db.session.get(Supplier, id)
    if supplier is None:
        abort(404)
    form = SupplierForm(obj=supplier)

    if form.validate_on_submit():
        # 检查编号是否已存在（排除自身）
        existing = Supplier.query.filter_by(code=form.code.data).first()
        if existing and existing.id != supplier.id:
            flash('供应商编号已存在，请使用其他编号！', 'danger')
            return render_template('product/supplier_edit.html', title='编辑供应商', form=form, supplier=supplier)

        supplier.code = form.code.data
        supplier.name = form.name.data
        supplier.contact_person = form.contact_person.data
        supplier.phone = form.phone.data
        supplier.address = form.address.data
        supplier.email = form.email.data

        log = Log(
            user_id=current_user.id,
            action='修改供应商',
            details=f'修改供应商: {supplier.code} - {supplier.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('编码已存在，请使用其他编码！', 'danger')
            return render_template('product/supplier_edit.html', title='编辑供应商', form=form, supplier=supplier)
        except SQLAlchemyError:
            db.session.rollback()
            flash('数据库错误，操作失败！', 'danger')
            return render_template('product/supplier_edit.html', title='编辑供应商', form=form, supplier=supplier)

        flash('供应商修改成功！', 'success')
        return redirect(url_for('partner.suppliers'))

    return render_template('product/supplier_edit.html',
                         title='编辑供应商',
                         form=form,
                         supplier=supplier,
                         action='edit')

@bp.route('/suppliers/<int:id>/delete', methods=['POST'])
@login_required
def delete_supplier(id):
    supplier = db.session.get(Supplier, id)
    if supplier is None:
        abort(404)

    has_orders = db.session.query(PurchaseOrder).filter_by(supplier_id=supplier.id).first() is not None
    has_payments = db.session.query(Payment).filter_by(supplier_id=supplier.id).first() is not None
    has_stock_ins = db.session.query(StockIn).join(PurchaseOrder, StockIn.purchase_order_id == PurchaseOrder.id).filter(PurchaseOrder.supplier_id == supplier.id).first() is not None
    has_stock_logs = db.session.query(StockLog).filter(StockLog.reference_type == 'purchase_order', StockLog.reference_id.in_(db.session.query(PurchaseOrder.id).filter_by(supplier_id=supplier.id))).first() is not None
    if has_orders or has_payments or has_stock_ins or has_stock_logs:
        flash('该供应商已有采购或付款记录，无法删除！', 'danger')
        return redirect(url_for('partner.suppliers'))

    log = Log(
        user_id=current_user.id,
        action='删除供应商',
        details=f'删除供应商: {supplier.code} - {supplier.name}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    try:
        db.session.delete(supplier)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash('数据库错误，删除失败！', 'danger')
        return redirect(url_for('partner.suppliers'))

    flash('供应商删除成功！', 'success')
    return redirect(url_for('partner.suppliers'))

# 客户管理
@bp.route('/customers')
@login_required
def customers():
    customers = Customer.query.order_by(Customer.created_at.desc()).limit(500).all()
    return render_template('product/customers.html',
                         title='客户管理',
                         customers=customers)

@bp.route('/customers/new', methods=['GET', 'POST'])
@login_required
def add_customer():
    form = CustomerForm()

    if form.validate_on_submit():
        # 检查编号是否已存在
        if Customer.query.filter_by(code=form.code.data).first():
            flash('客户编号已存在，请使用其他编号！', 'danger')
            return render_template('product/customer_edit.html', title='添加客户', form=form, action='new')

        customer = Customer(
            code=form.code.data,
            name=form.name.data,
            contact_person=form.contact_person.data,
            phone=form.phone.data,
            address=form.address.data,
            email=form.email.data
        )

        db.session.add(customer)
        log = Log(
            user_id=current_user.id,
            action='添加客户',
            details=f'添加客户: {customer.code} - {customer.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('编码已存在，请使用其他编码！', 'danger')
            return render_template('product/customer_edit.html', title='添加客户', form=form, action='new')
        except SQLAlchemyError:
            db.session.rollback()
            flash('数据库错误，操作失败！', 'danger')
            return render_template('product/customer_edit.html', title='添加客户', form=form, action='new')

        flash('客户添加成功！', 'success')
        return redirect(url_for('partner.customers'))

    return render_template('product/customer_edit.html',
                         title='添加客户',
                         form=form,
                         action='new')

@bp.route('/customers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = db.session.get(Customer, id)
    if customer is None:
        abort(404)
    form = CustomerForm(obj=customer)

    if form.validate_on_submit():
        # 检查编号是否已存在（排除自身）
        existing = Customer.query.filter_by(code=form.code.data).first()
        if existing and existing.id != customer.id:
            flash('客户编号已存在，请使用其他编号！', 'danger')
            return render_template('product/customer_edit.html', title='编辑客户', form=form, customer=customer)

        customer.code = form.code.data
        customer.name = form.name.data
        customer.contact_person = form.contact_person.data
        customer.phone = form.phone.data
        customer.address = form.address.data
        customer.email = form.email.data

        log = Log(
            user_id=current_user.id,
            action='修改客户',
            details=f'修改客户: {customer.code} - {customer.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('编码已存在，请使用其他编码！', 'danger')
            return render_template('product/customer_edit.html', title='编辑客户', form=form, customer=customer)
        except SQLAlchemyError:
            db.session.rollback()
            flash('数据库错误，操作失败！', 'danger')
            return render_template('product/customer_edit.html', title='编辑客户', form=form, customer=customer)

        flash('客户修改成功！', 'success')
        return redirect(url_for('partner.customers'))

    return render_template('product/customer_edit.html',
                         title='编辑客户',
                         form=form,
                         customer=customer,
                         action='edit')

@bp.route('/customers/<int:id>/delete', methods=['POST'])
@login_required
def delete_customer(id):
    customer = db.session.get(Customer, id)
    if customer is None:
        abort(404)

    # 检查是否有销售记录或收款记录
    has_sales = db.session.query(SalesOrder).filter_by(customer_id=customer.id).first() is not None
    has_receipts = db.session.query(Receipt).filter_by(customer_id=customer.id).first() is not None
    if has_sales or has_receipts:
        flash('该客户已有销售或收款记录，无法删除！', 'danger')
        return redirect(url_for('partner.customers'))

    log = Log(
        user_id=current_user.id,
        action='删除客户',
        details=f'删除客户: {customer.code} - {customer.name}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    try:
        db.session.delete(customer)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash('数据库错误，删除失败！', 'danger')
        return redirect(url_for('partner.customers'))

    flash('客户删除成功！', 'success')
    return redirect(url_for('partner.customers'))

# 仓库管理
@bp.route('/warehouses')
@login_required
def warehouses():
    warehouses = Warehouse.query.order_by(Warehouse.created_at.desc()).limit(500).all()
    return render_template('product/warehouses.html',
                         title='仓库管理',
                         warehouses=warehouses)

@bp.route('/warehouses/new', methods=['GET', 'POST'])
@login_required
def add_warehouse():
    form = WarehouseForm()

    if form.validate_on_submit():
        # 检查编号是否已存在
        if Warehouse.query.filter_by(code=form.code.data).first():
            flash('仓库编号已存在，请使用其他编号！', 'danger')
            return render_template('product/warehouse_edit.html', title='添加仓库', form=form, action='new')

        warehouse = Warehouse(
            code=form.code.data,
            name=form.name.data,
            address=form.address.data,
            manager=form.manager.data,
            phone=form.phone.data
        )

        db.session.add(warehouse)
        log = Log(
            user_id=current_user.id,
            action='添加仓库',
            details=f'添加仓库: {warehouse.code} - {warehouse.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('编码已存在，请使用其他编码！', 'danger')
            return render_template('product/warehouse_edit.html', title='添加仓库', form=form, action='new')
        except SQLAlchemyError:
            db.session.rollback()
            flash('数据库错误，操作失败！', 'danger')
            return render_template('product/warehouse_edit.html', title='添加仓库', form=form, action='new')

        flash('仓库添加成功！', 'success')
        return redirect(url_for('partner.warehouses'))

    return render_template('product/warehouse_edit.html',
                         title='添加仓库',
                         form=form,
                         action='new')

@bp.route('/warehouses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_warehouse(id):
    warehouse = db.session.get(Warehouse, id)
    if warehouse is None:
        abort(404)
    form = WarehouseForm(obj=warehouse)

    if form.validate_on_submit():
        # 检查编号是否已存在（排除自身）
        existing = Warehouse.query.filter_by(code=form.code.data).first()
        if existing and existing.id != warehouse.id:
            flash('仓库编号已存在，请使用其他编号！', 'danger')
            return render_template('product/warehouse_edit.html', title='编辑仓库', form=form, warehouse=warehouse)

        warehouse.code = form.code.data
        warehouse.name = form.name.data
        warehouse.address = form.address.data
        warehouse.manager = form.manager.data
        warehouse.phone = form.phone.data

        log = Log(
            user_id=current_user.id,
            action='修改仓库',
            details=f'修改仓库: {warehouse.code} - {warehouse.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('编码已存在，请使用其他编码！', 'danger')
            return render_template('product/warehouse_edit.html', title='编辑仓库', form=form, warehouse=warehouse)
        except SQLAlchemyError:
            db.session.rollback()
            flash('数据库错误，操作失败！', 'danger')
            return render_template('product/warehouse_edit.html', title='编辑仓库', form=form, warehouse=warehouse)

        flash('仓库修改成功！', 'success')
        return redirect(url_for('partner.warehouses'))

    return render_template('product/warehouse_edit.html',
                         title='编辑仓库',
                         form=form,
                         warehouse=warehouse,
                         action='edit')

@bp.route('/warehouses/<int:id>/delete', methods=['POST'])
@login_required
def delete_warehouse(id):
    warehouse = db.session.get(Warehouse, id)
    if warehouse is None:
        abort(404)

    # 检查是否有库存记录
    has_stock_ins = db.session.query(StockIn).filter_by(warehouse_id=warehouse.id).first() is not None
    has_stock_outs = db.session.query(StockOut).filter_by(warehouse_id=warehouse.id).first() is not None
    has_stock_logs = db.session.query(StockLog).filter_by(warehouse_id=warehouse.id).first() is not None
    if has_stock_ins or has_stock_outs or has_stock_logs:
        flash('该仓库已有库存记录，无法删除！', 'danger')
        return redirect(url_for('partner.warehouses'))

    log = Log(
        user_id=current_user.id,
        action='删除仓库',
        details=f'删除仓库: {warehouse.code} - {warehouse.name}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    try:
        db.session.delete(warehouse)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash('数据库错误，删除失败！', 'danger')
        return redirect(url_for('partner.warehouses'))

    flash('仓库删除成功！', 'success')
    return redirect(url_for('partner.warehouses'))
