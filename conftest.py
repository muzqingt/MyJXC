"""
测试 fixtures — app、client、db_session
"""
import os
import sys
import tempfile
import pytest

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope='session')
def app():
    """创建测试用 Flask 应用（整个测试会话共享）"""
    from app import create_app, db

    # 使用临时目录存放测试数据库
    db_dir = tempfile.mkdtemp()
    db_path = os.path.join(db_dir, 'test.db')

    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SERVER_NAME'] = 'localhost.localdomain'
    app.config['REMEMBER_COOKIE_DURATION'] = 0

    with app.app_context():
        db.create_all()

        # 创建默认数据（检查是否已存在）
        from app.models import User, Warehouse, Category
        from app import db as _db

        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            _db.session.add(admin)

        if not Warehouse.query.filter_by(code='WH001').first():
            warehouse = Warehouse(code='WH001', name='默认仓库')
            _db.session.add(warehouse)

        if not Category.query.filter_by(name='默认分类').first():
            category = Category(name='默认分类')
            _db.session.add(category)

        _db.session.commit()

    yield app

    # 清理临时文件
    import shutil
    shutil.rmtree(db_dir, ignore_errors=True)


@pytest.fixture(scope='function')
def client(app):
    """Flask 测试客户端，每个测试函数独立"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """数据库会话，每个测试后自动回滚"""
    from app import db
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture(scope='function')
def authenticated_client(app, client):
    """已登录 admin 的测试客户端"""
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123',
    }, follow_redirects=True)
    return client
