from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app import db
from app.models import User, Practice

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/register', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard.home'))
        practice_name = request.form.get('practice_name')
        if practice_name:
            practice = Practice(name=practice_name)
            db.session.add(practice)
            db.session.flush()
            user = User(email=email, practice_id=practice.id,
                first_name=request.form.get('first_name',''),
                last_name=request.form.get('last_name',''), role='admin')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('dashboard.home'))
        flash('Invalid email or password', 'danger')
    return render_template('medbridge_ui.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    from flask import jsonify, request
    email = request.json.get('email')
    password = request.json.get('password')
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({'success': True, 'name': user.first_name or email.split('@')[0]})
    return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    from flask import jsonify, request
    data = request.json
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'success': False, 'error': 'Email already registered'}), 400
    practice = Practice(name=data.get('practice_name','My Practice'))
    db.session.add(practice)
    db.session.flush()
    user = User(email=data.get('email'), practice_id=practice.id,
        first_name=data.get('first_name',''), last_name=data.get('last_name',''), role='admin')
    user.set_password(data.get('password',''))
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({'success': True, 'name': user.first_name or data.get('email','').split('@')[0]})
