from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db, csrf
from app.models import Product, Category, Log
from app.forms import ProductForm, CategoryForm, SearchForm
from datetime import datetime, timezone
import os
from werkzeug.utils import secure_filename
from flask import Blueprint

# 创建蓝图
bp = Blueprint('product', __name__, url_prefix='/product')

# 商品管理
@bp.route('/')
@bp.route('/products')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    search_form = SearchForm()
    keyword = request.args.get('keyword', '')
    category_id = request.args.get('category_id', type=int)
    
    query = Product.query
    
    if keyword:
        query = query.filter(
            Product.name.contains(keyword) | 
            Product.code.contains(keyword) |
            Product.specification.contains(keyword)
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    products = query.order_by(Product.updated_at.desc()).paginate(page=page, per_page=per_page)
    categories = Category.query.all()
    
    return render_template('product/index.html', 
                         title='商品管理',
                         products=products,
                         categories=categories,
                         search_form=search_form,
                         keyword=keyword,
                         category_id=category_id)

@bp.route('/products/new', methods=['GET', 'POST'])
@login_required
def new_product():
    form = ProductForm()
    form.category_id.choices = [(0, '无分类')] + [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        # 检查编号是否已存在
        if Product.query.filter_by(code=form.code.data).first():
            flash('商品编号已存在，请使用其他编号！', 'danger')
            return render_template('product/edit.html', title='新建商品', form=form)
        
        product = Product(
            code=form.code.data,
            name=form.name.data,
            category_id=form.category_id.data if form.category_id.data != 0 else None,
            specification=form.specification.data,
            unit=form.unit.data,
            purchase_price=form.purchase_price.data or 0,
            sale_price=form.sale_price.data or 0,
            safety_stock=form.safety_stock.data or 0,
            description=form.description.data
        )
        
        # 处理图片上传
        if form.image.data:
            file = form.image.data
            if file.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/jpg']:
                flash('只能上传 JPG/PNG/GIF 格式图片', 'danger')
                return redirect(url_for('product.new_product'))
            file.seek(0, 2)  # seek to end
            size = file.tell()
            file.seek(0)  # reset
            if size > 2 * 1024 * 1024:  # 2MB limit
                flash('图片大小不能超过 2MB', 'danger')
                return redirect(url_for('product.new_product'))
            filename = secure_filename(file.filename)
            if filename:
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    new_filename = f"product_{product.code}{file_ext}"
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
                    file.save(filepath)
                    product.image_path = new_filename
        
        db.session.add(product)
        db.session.commit()
        
        # 记录日志
        log = Log(
            user_id=current_user.id,
            action='添加商品',
            details=f'添加商品: {product.code} - {product.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('商品添加成功！', 'success')
        return redirect(url_for('product.index'))
    
    return render_template('product/edit.html', 
                         title='添加商品',
                         form=form,
                         action='new')

@bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(0, '无分类')] + [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        # 检查编号是否已存在（排除自身）
        existing = Product.query.filter_by(code=form.code.data).first()
        if existing and existing.id != product.id:
            flash('商品编号已存在，请使用其他编号！', 'danger')
            return render_template('product/edit.html', title='编辑商品', form=form, product=product)
        
        product.code = form.code.data
        product.name = form.name.data
        product.category_id = form.category_id.data if form.category_id.data != 0 else None
        product.specification = form.specification.data
        product.unit = form.unit.data
        product.purchase_price = form.purchase_price.data or 0
        product.sale_price = form.sale_price.data or 0
        product.safety_stock = form.safety_stock.data or 0
        product.description = form.description.data
        product.updated_at = datetime.now()
        
        # 处理图片上传
        if form.image.data:
            file = form.image.data
            if file.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/jpg']:
                flash('只能上传 JPG/PNG/GIF 格式图片', 'danger')
                return redirect(url_for('product.edit_product', id=product.id))
            file.seek(0, 2)  # seek to end
            size = file.tell()
            file.seek(0)  # reset
            if size > 2 * 1024 * 1024:  # 2MB limit
                flash('图片大小不能超过 2MB', 'danger')
                return redirect(url_for('product.edit_product', id=product.id))
            filename = secure_filename(file.filename)
            if filename:
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    # 删除旧图片
                    if product.image_path:
                        old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], product.image_path)
                        if os.path.exists(old_filepath):
                            os.remove(old_filepath)
                    
                    new_filename = f"product_{product.code}{file_ext}"
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
                    file.save(filepath)
                    product.image_path = new_filename
        
        db.session.commit()
        
        # 记录日志
        log = Log(
            user_id=current_user.id,
            action='修改商品',
            details=f'修改商品: {product.code} - {product.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('商品修改成功！', 'success')
        return redirect(url_for('product.index'))
    
    return render_template('product/edit.html', 
                         title='编辑商品',
                         form=form,
                         product=product,
                         action='edit')

@bp.route('/products/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)

    # 检查是否有相关记录
    if (len(product.purchase_order_items) > 0 or len(product.sales_order_items) > 0
            or len(product.stock_in_items) > 0 or len(product.stock_out_items) > 0
            or len(product.stock_logs) > 0):
        flash('该商品已有库存或订单记录，无法删除！', 'danger')
        return redirect(url_for('product.index'))
    
    # 删除图片
    if product.image_path:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], product.image_path)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    # 记录日志
    log = Log(
        user_id=current_user.id,
        action='删除商品',
        details=f'删除商品: {product.code} - {product.name}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.delete(product)
    db.session.commit()
    
    flash('商品删除成功！', 'success')
    return redirect(url_for('product.index'))

@bp.route('/products/<int:id>')
@login_required
def view_product(id):
    product = Product.query.get_or_404(id)
    return render_template('product/view.html', 
                         title='商品详情',
                         product=product)

# 分类管理
@bp.route('/categories')
@login_required
def categories():
    categories = Category.query.all()
    return render_template('product/categories.html', 
                         title='商品分类',
                         categories=categories)

@bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
def new_category():
    form = CategoryForm()
    form.parent_id.choices = [(0, '无父级')] + [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            parent_id=form.parent_id.data if form.parent_id.data != 0 else None,
            description=form.description.data
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('分类添加成功！', 'success')
        return redirect(url_for('product.categories'))
    
    return render_template('product/category_edit.html', 
                         title='添加分类',
                         form=form,
                         action='new')

@bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    form.parent_id.choices = [(0, '无父级')] + [(c.id, c.name) for c in Category.query.filter(Category.id != id).all()]
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        category.description = form.description.data
        
        db.session.commit()
        flash('分类修改成功！', 'success')
        return redirect(url_for('product.categories'))
    
    return render_template('product/category_edit.html', 
                         title='编辑分类',
                         form=form,
                         category=category,
                         action='edit')

@bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    # 检查是否有子分类
    if len(category.children) > 0:
        flash('该分类下有子分类，无法删除！', 'danger')
        return redirect(url_for('product.categories'))
    
    # 检查是否有商品
    if len(category.products) > 0:
        flash('该分类下有商品，无法删除！', 'danger')
        return redirect(url_for('product.categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('分类删除成功！', 'success')
    return redirect(url_for('product.categories'))

# API接口
@bp.route('/api/products')
@login_required
def api_products():
    products = Product.query.all()
    result = []
    for product in products:
        result.append({
            'id': product.id,
            'code': product.code,
            'name': product.name,
            'specification': product.specification,
            'unit': product.unit,
            'purchase_price': float(product.purchase_price),
            'sale_price': float(product.sale_price),
            'stock_quantity': float(product.stock_quantity)
        })
    return jsonify(result)

@bp.route('/api/product/price', methods=['POST'])
@login_required
def api_update_price():
    """更新商品价格"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的JSON数据'})

    product_id = data.get('product_id')
    price_type = data.get('price_type')  # 'sale_price' or 'purchase_price'
    price = data.get('price')

    if not product_id or not price_type or price is None or price is False:
        return jsonify({'success': False, 'message': '参数不完整'})
    
    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '商品ID无效'})
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': '商品不存在'})
    
    try:
        if price_type == 'sale_price':
            product.sale_price = float(price)
        elif price_type == 'purchase_price':
            product.purchase_price = float(price)
        else:
            return jsonify({'success': False, 'message': '价格类型无效'})
        
        db.session.commit()
        return jsonify({'success': True, 'message': '价格已更新'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/categories')
@login_required
def api_categories():
    categories = Category.query.all()
    result = []
    for category in categories:
        result.append({
            'id': category.id,
            'name': category.name,
            'parent_id': category.parent_id
        })
    return jsonify(result)