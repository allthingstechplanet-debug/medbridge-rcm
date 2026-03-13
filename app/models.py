from app import db
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash



# ─────────────────────────────────────────────
# PRACTICE (your customer — a medical practice)
# ─────────────────────────────────────────────
class Practice(db.Model):
    __tablename__ = 'practices'

    id                = db.Column(db.Integer, primary_key=True)
    name              = db.Column(db.String(150), nullable=False)
    npi               = db.Column(db.String(20))
    specialty         = db.Column(db.String(100))
    phone             = db.Column(db.String(20))
    address           = db.Column(db.String(250))
    subscription_tier = db.Column(db.String(20), default='trial')  # trial | starter | growth | enterprise
    stripe_customer_id= db.Column(db.String(100))
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    users       = db.relationship('User', backref='practice', lazy=True)
    patients    = db.relationship('Patient', backref='practice', lazy=True)
    prior_auths = db.relationship('PriorAuth', backref='practice', lazy=True)

    def __repr__(self):
        return f'<Practice {self.name}>'


# ─────────────────────────────────────────────
# USER (staff member at a practice)
# ─────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    practice_id   = db.Column(db.Integer, db.ForeignKey('practices.id'), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name    = db.Column(db.String(50), nullable=False)
    last_name     = db.Column(db.String(50), nullable=False)
    role          = db.Column(db.String(20), default='staff')  # admin | staff
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<User {self.email}>'


# ─────────────────────────────────────────────
# PATIENT
# ─────────────────────────────────────────────
class Patient(db.Model):
    __tablename__ = 'patients'

    id           = db.Column(db.Integer, primary_key=True)
    practice_id  = db.Column(db.Integer, db.ForeignKey('practices.id'), nullable=False)
    first_name   = db.Column(db.String(50), nullable=False)
    last_name    = db.Column(db.String(50), nullable=False)
    date_of_birth= db.Column(db.Date, nullable=False)
    member_id    = db.Column(db.String(50))     # Insurance member ID
    group_number = db.Column(db.String(50))
    payer_name   = db.Column(db.String(100))    # Insurance company name
    phone        = db.Column(db.String(20))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    prior_auths  = db.relationship('PriorAuth', backref='patient', lazy=True)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<Patient {self.full_name}>'


# ─────────────────────────────────────────────
# PRIOR AUTH REQUEST (core of the product)
# ─────────────────────────────────────────────
class PriorAuth(db.Model):
    __tablename__ = 'prior_auths'

    id             = db.Column(db.Integer, primary_key=True)
    practice_id    = db.Column(db.Integer, db.ForeignKey('practices.id'), nullable=False)
    patient_id     = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    submitted_by   = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Clinical info
    cpt_code       = db.Column(db.String(20), nullable=False)
    cpt_description= db.Column(db.String(200))
    icd10_code     = db.Column(db.String(20), nullable=False)
    icd10_description = db.Column(db.String(200))
    provider_name  = db.Column(db.String(100))
    provider_npi   = db.Column(db.String(20))
    facility_name  = db.Column(db.String(150))
    procedure_date = db.Column(db.Date)
    clinical_notes = db.Column(db.Text)

    # Payer info
    payer_name     = db.Column(db.String(100), nullable=False)
    payer_phone    = db.Column(db.String(20))
    auth_number    = db.Column(db.String(50))   # Returned when approved

    # Status tracking
    # pending | submitted | approved | denied | cancelled | info_needed
    status         = db.Column(db.String(30), default='pending')
    priority       = db.Column(db.String(10), default='normal')  # urgent | normal

    # Timestamps
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at   = db.Column(db.DateTime)
    decision_at    = db.Column(db.DateTime)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # AI scoring
    ai_approval_score = db.Column(db.Float)   # 0.0 – 1.0 probability of approval

    # Relationships
    denial        = db.relationship('Denial', backref='prior_auth', uselist=False)
    audit_logs    = db.relationship('AuditLog', backref='prior_auth', lazy=True)

    @property
    def days_pending(self):
        if self.submitted_at:
            return (datetime.utcnow() - self.submitted_at).days
        return 0

    @property
    def status_badge_class(self):
        mapping = {
            'pending':      'badge-warning',
            'submitted':    'badge-info',
            'approved':     'badge-success',
            'denied':       'badge-danger',
            'cancelled':    'badge-secondary',
            'info_needed':  'badge-warning',
        }
        return mapping.get(self.status, 'badge-secondary')

    def __repr__(self):
        return f'<PriorAuth {self.id} – {self.status}>'


# ─────────────────────────────────────────────
# DENIAL (linked to a prior auth)
# ─────────────────────────────────────────────
class Denial(db.Model):
    __tablename__ = 'denials'

    id              = db.Column(db.Integer, primary_key=True)
    prior_auth_id   = db.Column(db.Integer, db.ForeignKey('prior_auths.id'), nullable=False)
    denial_date     = db.Column(db.Date, nullable=False)
    denial_reason   = db.Column(db.String(100))   # e.g. "Not medically necessary"
    denial_code     = db.Column(db.String(20))
    appeal_deadline = db.Column(db.Date)
    appeal_status   = db.Column(db.String(30), default='not_started')
    # not_started | in_progress | submitted | won | lost
    appeal_letter   = db.Column(db.Text)          # AI-generated letter stored here
    recovery_amount = db.Column(db.Float)
    outcome_notes   = db.Column(db.Text)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def days_until_deadline(self):
        if self.appeal_deadline:
            return (self.appeal_deadline - datetime.utcnow().date()).days
        return None

    @property
    def deadline_urgency(self):
        days = self.days_until_deadline
        if days is None:
            return 'none'
        if days <= 7:
            return 'critical'
        if days <= 14:
            return 'warning'
        return 'ok'

    def __repr__(self):
        return f'<Denial {self.id} – {self.appeal_status}>'


# ─────────────────────────────────────────────
# AUDIT LOG (HIPAA requirement — never delete these)
# ─────────────────────────────────────────────
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id            = db.Column(db.Integer, primary_key=True)
    practice_id   = db.Column(db.Integer, db.ForeignKey('practices.id'))
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'))
    prior_auth_id = db.Column(db.Integer, db.ForeignKey('prior_auths.id'))
    action        = db.Column(db.String(100), nullable=False)
    # e.g. AUTH_CREATED | AUTH_SUBMITTED | DENIAL_RECORDED | APPEAL_GENERATED
    resource_type = db.Column(db.String(50))
    resource_id   = db.Column(db.Integer)
    ip_address    = db.Column(db.String(45))
    notes         = db.Column(db.Text)
    timestamp     = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AuditLog {self.action} at {self.timestamp}>'
