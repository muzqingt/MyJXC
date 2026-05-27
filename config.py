import os
import secrets


class Config:
    """基础配置"""
    BASEDIR = os.path.abspath(os.path.dirname(__file__))

    # SECRET_KEY: 优先从环境变量读取，否则从文件读取/生成
    _secret_key_file = os.path.join(BASEDIR, 'instance', '.flask_secret_key')
    if os.environ.get('SECRET_KEY'):
        SECRET_KEY = os.environ['SECRET_KEY']
    elif os.path.exists(_secret_key_file):
        with open(_secret_key_file, 'r') as f:
            SECRET_KEY = f.read().strip()
    else:
        os.makedirs(os.path.dirname(_secret_key_file), exist_ok=True)
        SECRET_KEY = secrets.token_hex(32)
        with open(_secret_key_file, 'w') as f:
            f.write(SECRET_KEY)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASEDIR, 'instance', 'store.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASEDIR, 'app', 'static', 'uploads')

    # CSRF settings - allow token from header
    WTF_CSRF_HEADERS = ['X-CSRFToken', 'X-CSRF-Token']

    # Bootstrap theme
    BOOTSTRAP_BOOTSWATCH_THEME = 'flatly'

    REMEMBER_COOKIE_DURATION = 30 * 24 * 60 * 60
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_PROTECTION = 'strong'

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
