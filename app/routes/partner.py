from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required
from app import db
from app.models import Supplier, Customer, Warehouse
from app.forms import SupplierForm, CustomerForm, WarehouseForm
from flask import Blueprint
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# 创建蓝图
bp = Blueprint('partner', __name__, url_prefix='/partner')

# 供应商管理
@bp.route('/suppliers')
@login_required
def suppliers():
    suppliers = Supplier.query.order_by(Supplier.created_at.desc()).all()
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

    # 检查是否有采购记录或付款记录
    if len(supplier.purchase_orders) > 0 or len(supplier.payments) > 0:
        flash('该供应商已有采购或付款记录，无法删除！', 'danger')
        return redirect(url_for('partner.suppliers'))

    db.session.delete(supplier)
    try:
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
    customers = Customer.query.order_by(Customer.created_at.desc()).all()
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
    if len(customer.sales_orders) > 0 or len(customer.receipts) > 0:
        flash('该客户已有销售或收款记录，无法删除！', 'danger')
        return redirect(url_for('partner.customers'))

    db.session.delete(customer)
    try:
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
    warehouses = Warehouse.query.order_by(Warehouse.created_at.desc()).all()
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
    if (len(warehouse.stock_ins) > 0 or len(warehouse.stock_outs) > 0
            or len(warehouse.stock_logs) > 0):
        flash('该仓库已有库存记录，无法删除！', 'danger')
        return redirect(url_for('partner.warehouses'))

    db.session.delete(warehouse)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash('数据库错误，删除失败！', 'danger')
        return redirect(url_for('partner.warehouses'))

    flash('仓库删除成功！', 'success')
    return redirect(url_for('partner.warehouses'))
