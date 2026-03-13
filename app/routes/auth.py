from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from ..models import db, User, Practice, AuditLog

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Log the login event
            log = AuditLog(
                practice_id=user.practice_id,
                user_id=user.id,
                action='USER_LOGIN',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()

            next_page = request.args.get('next')
            flash(f'Welcome back, {user.first_name}!', 'success')
            return redirect(next_page or url_for('dashboard.home'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        practice_name = request.form.get('practice_name', '').strip()
        first_name    = request.form.get('first_name', '').strip()
        last_name     = request.form.get('last_name', '').strip()
        email         = request.form.get('email', '').strip().lower()
        password      = request.form.get('password', '')
        confirm_pw    = request.form.get('confirm_password', '')
        specialty     = request.form.get('specialty', '').strip()

        # Basic validations
        if not all([practice_name, first_name, last_name, email, password]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_pw:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return render_template('auth/register.html')

        # Create practice first
        practice = Practice(
            name=practice_name,
            specialty=specialty,
            subscription_tier='trial'
        )
        db.session.add(practice)
        db.session.flush()  # Get practice.id before committing

        # Create admin user
        user = User(
            practice_id=practice.id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role='admin'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Log registration
        log = AuditLog(
            practice_id=practice.id,
            user_id=user.id,
            action='USER_REGISTERED',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        login_user(user)
        flash(f'Welcome to MedBridge, {first_name}! Your account is ready.', 'success')
        return redirect(url_for('dashboard.home'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    log = AuditLog(
        practice_id=current_user.practice_id,
        user_id=current_user.id,
        action='USER_LOGOUT',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
