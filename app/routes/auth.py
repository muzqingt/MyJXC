from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, Log
from app.forms import LoginForm, RegistrationForm
from datetime import datetime

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
        user.last_login = datetime.utcnow()
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
    from datetime import datetime
    return render_template('auth/profile.html', title='个人资料', now=datetime.utcnow())
