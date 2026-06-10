from flask import render_template, redirect, url_for, flash, request, jsonify, Blueprint, send_file, abort, current_app
from flask_login import login_required, current_user
import os
import shutil
from datetime import datetime
from app import db
from app.models import Log, User
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.utils import validate_csrf_token

# 创建蓝图
bp = Blueprint('system', __name__, url_prefix='/system')

def _require_admin():
    if current_user.role != 'admin':
        abort(403)

def _safe_filename(filename):
    """确保文件名不包含路径遍历字符"""
    filename = os.path.basename(filename)
    if not filename or filename.startswith('.'):
        return None
    return filename

@bp.route('/')
@login_required
def index():
    """系统功能首页"""
    return render_template('system/index.html', title='系统功能')

@bp.route('/logs')
@login_required
def logs():
    """操作日志"""
    _require_admin()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs_query = Log.query.order_by(Log.created_at.desc())
    logs_list = logs_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('system/logs.html',
                         title='操作日志',
                         logs=logs_list)

@bp.route('/backup')
@login_required
def backup():
    """数据备份"""
    return render_template('system/backup.html', title='数据备份')

@bp.route('/backup/create', methods=['POST'])
@login_required
def create_backup():
    """创建数据备份"""
    _require_admin()

    # 创建备份目录
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../backups')
    os.makedirs(backup_dir, exist_ok=True)

    # 备份数据库文件
    db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    description = request.form.get('description', '').strip()
    # 清理描述用于文件名：只保留安全字符
    safe_desc = ''.join(c for c in description if c.isalnum() or c in ' _-').strip()
    if safe_desc:
        backup_filename = f'backup_{timestamp}_{safe_desc}.db'
    else:
        backup_filename = f'backup_{timestamp}.db'
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        shutil.copy2(db_path, backup_path)
        
        # 记录操作日志
        log = Log(
            user_id=current_user.id,
            action='创建数据备份',
            details=f'备份文件: {backup_filename}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        msg = f'备份创建成功: {backup_filename}'
        if description:
            msg += f'（{description}）'
        flash(msg, 'success')
    except (OSError, SQLAlchemyError):
        db.session.rollback()
        flash('备份创建失败，请稍后重试！', 'danger')

    return redirect(url_for('system.backup'))

@bp.route('/backup/list')
@login_required
def list_backups():
    """列出所有备份文件"""
    _require_admin()

    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    backups = []
    for filename in os.listdir(backup_dir):
        if filename.endswith('.db'):
            filepath = os.path.join(backup_dir, filename)
            stat = os.stat(filepath)
            backups.append({
                'filename': filename,
                'size': stat.st_size,
                'modified_at': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })

    backups.sort(key=lambda x: x['modified_at'], reverse=True)
    return jsonify(backups)

@bp.route('/backup/download/<filename>')
@login_required
def download_backup(filename):
    """下载备份文件"""
    _require_admin()

    filename = _safe_filename(filename)
    if not filename:
        flash('无效的文件名！', 'danger')
        return redirect(url_for('system.backup'))

    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../backups')
    filepath = os.path.realpath(os.path.join(backup_dir, filename))
    if not filepath.startswith(os.path.realpath(backup_dir)):
        flash('非法文件路径！', 'danger')
        return redirect(url_for('system.backup'))

    if not os.path.exists(filepath):
        flash('备份文件不存在！', 'danger')
        return redirect(url_for('system.backup'))

    return send_file(filepath, as_attachment=True)

@bp.route('/backup/restore', methods=['POST'])
@login_required
def restore_backup():
    """恢复数据备份"""
    _require_admin()

    filename = request.form.get('filename')
    if not filename:
        flash('请选择要恢复的备份文件！', 'danger')
        return redirect(url_for('system.backup'))

    filename = _safe_filename(filename)
    if not filename:
        flash('无效的文件名！', 'danger')
        return redirect(url_for('system.backup'))

    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../backups')
    backup_path = os.path.realpath(os.path.join(backup_dir, filename))
    if not backup_path.startswith(os.path.realpath(backup_dir)):
        flash('非法文件路径！', 'danger')
        return redirect(url_for('system.backup'))

    db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

    if not os.path.exists(backup_path):
        flash('备份文件不存在！', 'danger')
        return redirect(url_for('system.backup'))
    
    try:
        current_backup = f'current_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2(db_path, os.path.join(backup_dir, current_backup))
    except OSError:
        flash('数据恢复失败，请稍后重试！', 'danger')
        return redirect(url_for('system.backup'))

    db.session.remove()
    try:
        shutil.copy2(backup_path, db_path)
    except OSError:
        db.session.rollback()
        flash('数据恢复失败，请稍后重试！', 'danger')
        return redirect(url_for('system.backup'))

    flash(f'数据恢复成功，当前数据库已备份为: {current_backup}', 'success')
    return redirect(url_for('system.backup'))

@bp.route('/backup/delete', methods=['POST'])
@login_required
def delete_backup():
    """删除备份文件"""
    _require_admin()

    filename = request.form.get('filename')
    if not filename:
        flash('请选择要删除的备份文件！', 'danger')
        return redirect(url_for('system.backup'))

    filename = _safe_filename(filename)
    if not filename:
        flash('无效的文件名！', 'danger')
        return redirect(url_for('system.backup'))

    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../backups')
    backup_path = os.path.realpath(os.path.join(backup_dir, filename))
    if not backup_path.startswith(os.path.realpath(backup_dir)):
        flash('非法文件路径！', 'danger')
        return redirect(url_for('system.backup'))

    if not os.path.exists(backup_path):
        flash('备份文件不存在！', 'danger')
        return redirect(url_for('system.backup'))

    # 不允许删除当前备份文件
    if filename.startswith('current_'):
        flash('不能删除当前备份文件！', 'danger')
        return redirect(url_for('system.backup'))
    
    try:
        os.remove(backup_path)
        
        # 记录操作日志
        log = Log(
            user_id=current_user.id,
            action='删除数据备份',
            details=f'删除备份文件: {filename}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'备份文件已删除: {filename}', 'success')
    except (OSError, SQLAlchemyError):
        db.session.rollback()
        flash('删除备份失败，请稍后重试！', 'danger')
    
    return redirect(url_for('system.backup'))

@bp.route('/settings')
@login_required
def settings():
    """系统设置"""
    _require_admin()

    from app.models import SystemSetting
    # 从数据库加载设置
    from app.models import Warehouse
    warehouses = Warehouse.query.all()
    config = {
        'COMPANY_NAME': SystemSetting.get_value('COMPANY_NAME', ''),
        'COMPANY_ADDRESS': SystemSetting.get_value('COMPANY_ADDRESS', ''),
        'COMPANY_PHONE': SystemSetting.get_value('COMPANY_PHONE', ''),
        'DEFAULT_CURRENCY': SystemSetting.get_value('DEFAULT_CURRENCY', 'CNY'),
        'ITEMS_PER_PAGE': SystemSetting.get_value('ITEMS_PER_PAGE', '20'),
        'ENABLE_BACKUP': SystemSetting.get_value('ENABLE_BACKUP', '1') == '1',
        'ENABLE_LOGGING': SystemSetting.get_value('ENABLE_LOGGING', '1') == '1',
        'DEFAULT_WAREHOUSE': SystemSetting.get_value('DEFAULT_WAREHOUSE', ''),
        # AI 配置
        'AI_API_URL': SystemSetting.get_value('AI_API_URL', ''),
        'AI_API_KEY': SystemSetting.get_value('AI_API_KEY', ''),
        'AI_MODEL_NAME': SystemSetting.get_value('AI_MODEL_NAME', ''),
    }
    # 密钥脱敏
    ai_key = config.get('AI_API_KEY', '')
    config['AI_API_KEY_MASKED'] = (ai_key[:4] + '****') if len(ai_key) > 4 else ai_key

    return render_template('system/settings.html', title='系统设置', config=config, warehouses=warehouses)

@bp.route('/users')
@login_required
def user_management():
    """用户管理"""
    _require_admin()

    users = User.query.all()
    return render_template('system/users.html',
                         title='用户管理',
                         users=users)

@bp.route('/user/add', methods=['POST'])
@login_required
def add_user():
    """添加用户"""
    _require_admin()
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('请求无效，请重试。', 'danger')
        return redirect(url_for('system.user_management'))

    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    role = request.form.get('role', 'user')
    if role not in ('admin', 'user'):
        role = 'user'

    if not username or not password:
        flash('用户名和密码不能为空！', 'danger')
        return redirect(url_for('system.user_management'))
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        flash('用户名已存在！', 'danger')
        return redirect(url_for('system.user_management'))
    
    # 创建新用户
    user = User(username=username, email=email, role=role)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
        flash('用户添加成功！', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('用户名或邮箱已存在！', 'danger')
    except SQLAlchemyError:
        db.session.rollback()
        flash('添加用户失败，请稍后重试！', 'danger')

    return redirect(url_for('system.user_management'))

@bp.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """编辑用户"""
    _require_admin()

    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    if request.method == 'POST':
        if not validate_csrf_token(request.form.get('csrf_token')):
            flash('请求无效，请重试。', 'danger')
            return redirect(url_for('system.user_management'))

        email = request.form.get('email', '').strip()
        if email and ('@' not in email or '.' not in email.split('@')[1]):
            flash('请输入有效的邮箱地址！', 'danger')
            return redirect(url_for('system.edit_user', user_id=user_id))
        user.email = email
        role = request.form.get('role')
        if role not in ('admin', 'user'):
            role = 'user'
        user.role = role
        user.is_active = request.form.get('is_active') == '1'

        password = request.form.get('password')
        if password:
            if len(password) < 6 or len(password) > 128:
                flash('密码长度必须在6到128个字符之间！', 'danger')
                return redirect(url_for('system.edit_user', user_id=user_id))
            user.set_password(password)

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash('用户信息更新失败，请稍后重试！', 'danger')
            return redirect(url_for('system.edit_user', user_id=user_id))
        flash('用户信息已更新！', 'success')
        return redirect(url_for('system.user_management'))
    
    return render_template('system/user_edit.html', title='编辑用户', user=user)

@bp.route('/user/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """删除用户"""
    _require_admin()
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('请求无效，请重试。', 'danger')
        return redirect(url_for('system.user_management'))

    if user_id == current_user.id:
        flash('不能删除当前登录用户！', 'danger')
        return redirect(url_for('system.user_management'))
    
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    # 先删除该用户的所有日志
    Log.query.filter_by(user_id=user_id).delete()
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('用户已删除！', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        flash('删除用户失败，请稍后重试！', 'danger')
    return redirect(url_for('system.user_management'))

@bp.route('/api/system-info')
@login_required
def system_info_api():
    """系统信息API"""
    _require_admin()

    # 获取数据库大小
    db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    
    # 获取用户数量
    user_count = User.query.count()
    
    # 获取日志数量
    log_count = Log.query.count()
    
    return jsonify({
        'database_size': db_size,
        'user_count': user_count,
        'log_count': log_count,
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@bp.route('/api/system/recent-logs')
@login_required
def recent_logs():
    """获取最近系统日志"""
    _require_admin()

    logs = Log.query.order_by(Log.created_at.desc()).limit(10).all()
    return jsonify([{
        'id': log.id,
        'username': log.user.username if log.user else '系统',
        'action': log.action,
        'details': log.details,
        'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else ''
    } for log in logs])

@bp.route('/api/system/optimize-db', methods=['POST'])
@login_required
def optimize_db():
    """优化数据库"""
    _require_admin()

    try:
        # VACUUM 命令优化 SQLite 数据库
        db.session.execute(db.text('COMMIT'))
        db.session.execute(db.text('VACUUM'))
        return jsonify({'success': True, 'message': '数据库优化完成'})
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({'success': False, 'message': '数据库优化失败，请稍后重试'}), 500

@bp.route('/api/system/clean-logs', methods=['POST'])
@login_required
def clean_logs():
    """清理旧日志"""
    _require_admin()

    try:
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=90)
        old_logs = Log.query.filter(Log.created_at < cutoff_date).limit(1000).all()
        deleted = len(old_logs)
        for log in old_logs:
            db.session.delete(log)
        db.session.commit()
        return jsonify({'success': True, 'deleted_count': deleted})
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({'success': False, 'message': '日志清理失败，请稍后重试'}), 500

@bp.route('/api/system/export-db')
@login_required
def export_db():
    """导出数据库"""
    _require_admin()

    db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    export_filename = f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    if not os.path.exists(db_path):
        flash('数据库文件不存在！', 'danger')
        return redirect(url_for('system.settings'))

    db.session.remove()
    return send_file(db_path, as_attachment=True, download_name=export_filename)

@bp.route('/api/system/settings', methods=['POST'])
@login_required
def save_settings():
    """保存系统设置"""
    _require_admin()
    if not validate_csrf_token(request.form.get('csrf_token')):
        return jsonify({'success': False, 'message': '请求无效，请重试。'}), 400

    from app.models import SystemSetting
    
    # 保存所有设置项
    settings_keys = [
        'COMPANY_NAME', 'COMPANY_ADDRESS', 'COMPANY_PHONE',
        'DEFAULT_CURRENCY', 'ITEMS_PER_PAGE', 'ENABLE_BACKUP', 'ENABLE_LOGGING',
        'DEFAULT_WAREHOUSE',
        'AI_API_URL', 'AI_API_KEY', 'AI_MODEL_NAME',
    ]
    
    try:
        for key in settings_keys:
            value = request.form.get(key, '')
            setting = SystemSetting.query.filter_by(setting_key=key).first()
            if setting:
                setting.value = value
            else:
                setting = SystemSetting(setting_key=key, value=value)
                db.session.add(setting)
        db.session.commit()
        return jsonify({'success': True, 'message': '设置已保存'})
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({'success': False, 'message': '设置保存失败，请稍后重试'}), 500
