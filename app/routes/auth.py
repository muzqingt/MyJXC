from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, Log
from app.forms import LoginForm, RegistrationForm
from datetime import datetime, timezone

# 创建蓝图
bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('账户尚未激活，请联系管理员。', 'warning')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.now()
        db.session.commit()
        
        # 记录登录日志
        log = Log(
            user_id=user.id,
            action='用户登录',
            details=f'用户 {user.username} 登录系统',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('登录成功！', 'success')
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='登录', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, is_active=False)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功！请等待管理员激活账户后登录。', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='注册', form=form)

@bp.route('/logout')
@login_required
def logout():
    # 记录登出日志
    log = Log(
        user_id=current_user.id,
        action='用户登出',
        details=f'用户 {current_user.username} 登出系统',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('您已成功登出。', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/profile')
@login_required
def profile():
    from datetime import datetime, timezone
    return render_template('auth/profile.html', title='个人资料', now=datetime.now())

@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not current_user.check_password(old_password):
        flash('当前密码错误', 'danger')
        return redirect(url_for('auth.profile'))
    
    if len(new_password) < 6:
        flash('新密码长度至少6位', 'danger')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('两次输入的密码不一致', 'danger')
        return redirect(url_for('auth.profile'))
    
    current_user.set_password(new_password)
    db.session.commit()
    
    # 记录日志
    log = Log(
        user_id=current_user.id,
        action='修改密码',
        details=f'用户 {current_user.username} 修改了密码',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    flash('密码修改成功', 'success')
    return redirect(url_for('auth.profile'))

@bp.route('/change-email', methods=['POST'])
@login_required
def change_email():
    new_email = request.form.get('new_email', '').strip()
    
    if not new_email:
        flash('邮箱地址不能为空', 'danger')
        return redirect(url_for('auth.profile'))
    
    if '@' not in new_email:
        flash('请输入有效的邮箱地址', 'danger')
        return redirect(url_for('auth.profile'))
    
    # 检查邮箱是否已被使用
    existing = User.query.filter(User.email == new_email, User.id != current_user.id).first()
    if existing:
        flash('该邮箱已被其他用户使用', 'danger')
        return redirect(url_for('auth.profile'))
    
    current_user.email = new_email
    db.session.commit()
    
    # 记录日志
    log = Log(
        user_id=current_user.id,
        action='修改邮箱',
        details=f'用户 {current_user.username} 修改邮箱为 {new_email}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    flash('邮箱修改成功', 'success')
    return redirect(url_for('auth.profile'))
