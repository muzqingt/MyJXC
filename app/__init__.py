from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from datetime import datetime
import os

# 初始化扩展
db = SQLAlchemy()
bootstrap = Bootstrap()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录以访问此页面。'
login_manager.login_message_category = 'warning'

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 初始化扩展
    db.init_app(app)
    bootstrap.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    
    # 注册蓝图
    from app.routes import auth, product, purchase, sales, inventory, finance, report, system, main
    app.register_blueprint(auth.bp)
    app.register_blueprint(product.bp)
    app.register_blueprint(purchase.bp)
    app.register_blueprint(sales.bp)
    app.register_blueprint(inventory.bp)
    app.register_blueprint(finance.bp)
    app.register_blueprint(report.bp)
    app.register_blueprint(system.bp)
    app.register_blueprint(main.bp)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 注册模板上下文处理器
    @app.context_processor
    def inject_template_functions():
        return {
            'now': datetime.now
        }
    
    return app
