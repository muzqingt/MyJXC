import os

basedir = os.path.abspath(os.path.dirname(__file__))

def _load_secret_key():
    """Load SECRET_KEY from instance folder, generate if not exists."""
    instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    key_file = os.path.join(instance_dir, '.flask_secret_key')
    if os.path.exists(key_file):
        with open(key_file, 'r') as f:
            return f.read().strip()
    import secrets
    key = secrets.token_hex(32)
    with open(key_file, 'w') as f:
        f.write(key)
    return key

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or _load_secret_key()
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///store.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # CSRF settings - allow token from header
    WTF_CSRF_HEADERS = ['X-CSRFToken', 'X-CSRF-Token']
    
    # Bootstrap theme
    BOOTSTRAP_BOOTSWATCH_THEME = 'flatly'  # 可选: cerulean, cosmo, flatly, journal, litera, lumen, lux, materia, minty, pulse, sandstone, simplex, sketchy, slate, solar, spacelab, superhero, united, yeti

    # Flask-Login remember me settings
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = 86400 * 7  # 7天

    # Session security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_PROTECTION = 'strong'
