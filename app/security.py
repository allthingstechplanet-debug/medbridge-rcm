from datetime import datetime, timedelta
from collections import defaultdict
import re

# In-memory rate limiter
login_attempts = defaultdict(list)
blocked_ips = {}

def check_rate_limit(ip, max_attempts=5, window_minutes=15):
    now = datetime.utcnow()
    window = timedelta(minutes=window_minutes)
    
    # Check if IP is blocked
    if ip in blocked_ips:
        if datetime.utcnow() < blocked_ips[ip]:
            remaining = (blocked_ips[ip] - datetime.utcnow()).seconds // 60
            return False, f"Too many failed attempts. Try again in {remaining} minutes."
        else:
            del blocked_ips[ip]
    
    # Clean old attempts
    login_attempts[ip] = [t for t in login_attempts[ip] if now - t < window]
    
    # Check attempts
    if len(login_attempts[ip]) >= max_attempts:
        blocked_ips[ip] = now + timedelta(minutes=30)
        login_attempts[ip] = []
        return False, "Too many failed attempts. Account locked for 30 minutes."
    
    return True, None

def record_failed_attempt(ip):
    login_attempts[ip].append(datetime.utcnow())

def clear_attempts(ip):
    if ip in login_attempts:
        del login_attempts[ip]

def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number."
    return True, None

def sanitize_input(text, max_length=500):
    if not text:
        return text
    # Remove any HTML/script tags
    text = re.sub(r'<[^>]+>', '', str(text))
    # Trim whitespace
    text = text.strip()
    # Enforce max length
    return text[:max_length]

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
