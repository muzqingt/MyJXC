#!/usr/bin/env python3
"""
进销存管理系统启动文件
"""

import os
import socket
import threading
from app import create_app, db
from app.models import User, Category, Product, Supplier, Customer, Warehouse

app = create_app()


def get_local_ip():
    """获取本机局域网IP"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def register_mdns(port=5000):
    """注册mDNS服务，实现局域网.local域名发现"""
    try:
        from zeroconf import ServiceInfo, Zeroconf
    except ImportError:
        print("[mDNS] zeroconf 未安装，跳过mDNS注册")
        return None

    local_ip = get_local_ip()
    service_name = 'myjxc._http._tcp.local.'

    try:
        zc = Zeroconf()
        info = ServiceInfo(
            '_http._tcp.local.',
            service_name,
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties={
                'path': '/',
                'version': '1.0.0',
            },
            server='myjxc.local.',
        )
        zc.register_service(info)
        print(f"[mDNS] 已注册服务: http://myjxc.local:{port}")
        print(f"[mDNS] 局域网IP访问: http://{local_ip}:{port}")
        return zc
    except Exception as e:
        print(f"[mDNS] 注册失败: {e}")
        return None

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

    # 启动mDNS服务（需在启动Flask之前注册）
    zc = register_mdns(5000)

    port = int(os.environ.get('PORT', 5000))
    mode = os.environ.get('MODE', 'dev')  # dev / prod

    print("启动进销存管理系统...")
    print(f"访问地址: http://127.0.0.1:{port}")
    print("默认账号: admin / admin123")

    try:
        if mode == 'prod':
            from waitress import serve
            print(f"生产模式 (waitress)，端口 {port}")
            serve(app, host='0.0.0.0', port=port)
        else:
            debug = os.environ.get('FLASK_DEBUG', '0') == '1'
            print(f"开发模式 (Flask)，端口 {port}，debug={'开' if debug else '关'}")
            app.run(host='0.0.0.0', port=port, debug=debug)
    finally:
        if zc:
            zc.close()
            print("[mDNS] 服务已注销")
