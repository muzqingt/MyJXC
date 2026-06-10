from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from datetime import datetime
import os

from config import config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
bootstrap = Bootstrap()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录以访问此页面。'
login_manager.login_message_category = 'warning'

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    bootstrap.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # 注册蓝图
    from app.routes import auth, product, partner, purchase, sales, inventory, finance, report, system, main
    from app.routes import ai
    app.register_blueprint(auth.bp)
    app.register_blueprint(product.bp)
    app.register_blueprint(partner.bp)
    app.register_blueprint(purchase.bp)
    app.register_blueprint(sales.bp)
    app.register_blueprint(inventory.bp)
    app.register_blueprint(finance.bp)
    app.register_blueprint(report.bp)
    app.register_blueprint(system.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(ai.bp)

    # 注册模板上下文处理器
    @app.context_processor
    def inject_template_functions():
        from app.utils import format_local_dt
        return {
            'now': datetime.now,
            'format_local_dt': format_local_dt
        }

    # 注册 Jinja2 过滤器
    from app.utils import localize_dt
    @app.template_filter('localize')
    def localize_filter(dt):
        return localize_dt(dt)

    @app.template_filter('payment_method')
    def payment_method_filter(method):
        from app.constants import PaymentMethod
        return PaymentMethod.label(method or '')

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    # 自定义错误页面
    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('error.html',
                               error_code=403,
                               error_message='访问被拒绝',
                               error_detail='您没有权限执行此操作。'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('error.html',
                               error_code=404,
                               error_message='页面未找到',
                               error_detail='您访问的页面不存在或已被移除。'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        from flask import render_template
        return render_template('error.html',
                               error_code=500,
                               error_message='服务器内部错误',
                               error_detail='系统遇到了一个意外错误，请稍后重试。'), 500

    return app
