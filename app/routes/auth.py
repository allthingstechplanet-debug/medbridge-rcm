from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Practice
from app.security import (check_rate_limit, record_failed_attempt, 
                          clear_attempts, is_strong_password, 
                          sanitize_input, is_valid_email)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/register', methods=['GET', 'POST'])
def login():
    return render_template('medbridge_ui.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    ip = request.remote_addr or 'unknown'
    
    # Rate limit check
    allowed, error_msg = check_rate_limit(ip)
    if not allowed:
        return jsonify({'success': False, 'error': error_msg}), 429
    
    data = request.json or {}
    email = sanitize_input(data.get('email', ''), 255)
    password = data.get('password', '')
    
    # Validate inputs
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required.'}), 400
    
    if not is_valid_email(email):
        return jsonify({'success': False, 'error': 'Invalid email format.'}), 400
    
    # Check credentials
    user = User.query.filter_by(email=email.lower()).first()
    
    if not user or not user.check_password(password):
        record_failed_attempt(ip)
        attempts_left = 5 - len([a for a in __import__('app.security', fromlist=['login_attempts']).login_attempts[ip]])
        return jsonify({
            'success': False, 
            'error': f'Invalid email or password. {max(0,attempts_left)} attempts remaining.'
        }), 401
    
    # Success
    clear_attempts(ip)
    login_user(user, remember=False)
    
    return jsonify({
        'success': True, 
        'name': user.first_name or email.split('@')[0],
        'email': user.email,
        'role': user.role
    })

@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    ip = request.remote_addr or 'unknown'
    
    # Rate limit registrations too
    allowed, error_msg = check_rate_limit(ip, max_attempts=3, window_minutes=60)
    if not allowed:
        return jsonify({'success': False, 'error': 'Too many registration attempts. Try again later.'}), 429
    
    data = request.json or {}
    email = sanitize_input(data.get('email', ''), 255)
    password = data.get('password', '')
    first_name = sanitize_input(data.get('first_name', ''), 100)
    last_name = sanitize_input(data.get('last_name', ''), 100)
    practice_name = sanitize_input(data.get('practice_name', ''), 255)
    
    # Validate all fields
    if not all([email, password, practice_name]):
        return jsonify({'success': False, 'error': 'All fields are required.'}), 400
    
    if not is_valid_email(email):
        return jsonify({'success': False, 'error': 'Invalid email format.'}), 400
    
    # Password strength check
    strong, pwd_error = is_strong_password(password)
    if not strong:
        return jsonify({'success': False, 'error': pwd_error}), 400
    
    # Check duplicate email
    if User.query.filter_by(email=email.lower()).first():
        return jsonify({'success': False, 'error': 'An account with this email already exists.'}), 400
    
    # Create practice and user
    practice = Practice(name=practice_name)
    db.session.add(practice)
    db.session.flush()
    
    user = User(
        email=email.lower(),
        practice_id=practice.id,
        first_name=first_name,
        last_name=last_name,
        role='admin'
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user, remember=False)
    
    return jsonify({
        'success': True,
        'name': first_name or email.split('@')[0]
    })
