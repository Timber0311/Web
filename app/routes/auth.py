from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db
from urllib.parse import urlparse
from config import Config

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not all([email, username, password]):
            flash('请填写所有必填字段')
            return redirect(url_for('auth.register'))
            
        if len(password) < 8:
            flash('密码长度必须至少为8位')
            return redirect(url_for('auth.register'))
            
        if len(username) < 2:
            flash('用户名长度必须至少为2位')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(username=username).first():
            flash('该用户名已被使用')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('该邮箱已被注册')
            return redirect(url_for('auth.register'))
            
        try:
            user = User(email=email, username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('注册成功！请登录')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('注册失败，请稍后重试')
            return redirect(url_for('auth.register'))
        
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.is_administrator():
            flash('管理员请从管理员登录入口登录')
            return redirect(url_for('auth.admin_login'))
        
        if user and user.check_password(password):
            login_user(user, remember=remember, duration=Config.REMEMBER_COOKIE_DURATION)
            
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('main.index')
                
            flash('登录成功')
            return redirect(next_page)
        else:
            flash('邮箱或密码错误')
            
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录')
    return redirect(url_for('main.index'))

@bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if current_user.is_administrator():
            return redirect(url_for('admin.index'))
        else:
            logout_user()
            flash('请使用管理员账号登录')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.is_administrator():
                login_user(user)
                next_page = request.args.get('next')
                if not next_page or urlparse(next_page).netloc != '':
                    next_page = url_for('admin.index')
                flash('管理员登录成功')
                return redirect(next_page)
            else:
                flash('该账号不是管理员账号，请从用户登录入口登录')
                return redirect(url_for('auth.login'))
        else:
            flash('邮箱或密码错误')
            
    return render_template('auth/admin_login.html') 