#!/usr/bin/env python3
"""
进销存管理系统启动文件
"""

import os
from app import create_app, db
from app.models import User, Category, Product, Supplier, Customer, Warehouse

app = create_app()

@app.route('/')
def index():
    """主页面路由，根据登录状态重定向"""
    from flask import redirect, url_for
    from flask_login import current_user
    
    if current_user.is_authenticated:
        return redirect(url_for('product.index'))
    else:
        return redirect(url_for('auth.login'))

@app.route('/login')
def login_redirect():
    """兼容旧的/login路径，重定向到/auth/login"""
    from flask import redirect, url_for
    return redirect(url_for('auth.login'))

@app.shell_context_processor
def make_shell_context():
    """为Flask shell添加上下文"""
    return {
        'db': db,
        'User': User,
        'Category': Category,
        'Product': Product,
        'Supplier': Supplier,
        'Customer': Customer,
        'Warehouse': Warehouse
    }

def init_database():
    """初始化数据库，创建默认数据"""
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 创建默认管理员用户
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print("创建默认管理员账号: admin / admin123")
        
        # 创建默认仓库
        if not Warehouse.query.filter_by(code='WH001').first():
            warehouse = Warehouse(
                code='WH001',
                name='主仓库',
                address='默认地址',
                manager='管理员',
                phone='13800138000'
            )
            db.session.add(warehouse)
            print("创建默认仓库: 主仓库")
        
        # 创建默认分类
        if not Category.query.filter_by(name='默认分类').first():
            category = Category(name='默认分类', description='系统默认分类')
            db.session.add(category)
            print("创建默认分类: 默认分类")
        
        db.session.commit()
        print("数据库初始化完成！")

if __name__ == '__main__':
    # 初始化数据库
    init_database()
    
    # 启动应用
    print("启动进销存管理系统...")
    print("访问地址: http://127.0.0.1:5000")
    print("默认账号: admin / admin123")
    app.run(host='0.0.0.0', port=5000, debug=True)
