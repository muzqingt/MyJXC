"""
测试 fixtures — app、client、db_session
"""
import os
import sys
import tempfile

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 必须在 import app 之前设置 DATABASE_URL，否则引擎缓存生产数据库
_test_db_dir = tempfile.mkdtemp()
_test_db_path = os.path.join(_test_db_dir, 'test.db')
os.environ['DATABASE_URL'] = f'sqlite:///{_test_db_path}'

import pytest


@pytest.fixture(scope='session')
def app():
    """创建测试用 Flask 应用（整个测试会话共享）"""
    import shutil
    from app import create_app, db

    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost.localdomain'
    app.config['REMEMBER_COOKIE_DURATION'] = 0

    with app.app_context():
        db.create_all()

        # 创建默认数据
        from app.models import User, Warehouse, Category
        from app import db as _db

        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        _db.session.add(admin)

        warehouse = Warehouse(code='WH001', name='默认仓库')
        _db.session.add(warehouse)

        category = Category(name='默认分类')
        _db.session.add(category)

        _db.session.commit()

    yield app

    # 清理临时文件
    shutil.rmtree(_test_db_dir, ignore_errors=True)


@pytest.fixture(scope='function')
def client(app):
    """Flask 测试客户端，每个测试函数独立"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """数据库会话，每个测试后清理"""
    from app import db
    with app.app_context():
        yield db.session
        # 回滚未提交的更改
        db.session.rollback()
        # 清除所有表数据（保留表结构）
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        # 重新创建默认数据
        from app.models import User, Warehouse, Category
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        warehouse = Warehouse(code='WH001', name='默认仓库')
        db.session.add(warehouse)
        category = Category(name='默认分类')
        db.session.add(category)
        db.session.commit()


@pytest.fixture(scope='function')
def authenticated_client(app, client, db_session):
    """已登录 admin 的测试客户端"""
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123',
    }, follow_redirects=True)
    return client
