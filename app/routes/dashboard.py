from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from ..models import PriorAuth, Denial, Patient

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def home():
    pid = current_user.practice_id

    # Summary counts
    total_auths    = PriorAuth.query.filter_by(practice_id=pid).count()
    pending_auths  = PriorAuth.query.filter_by(practice_id=pid, status='pending').count()
    approved_auths = PriorAuth.query.filter_by(practice_id=pid, status='approved').count()
    denied_auths   = PriorAuth.query.filter_by(practice_id=pid, status='denied').count()

    # Approval rate
    decided = approved_auths + denied_auths
    approval_rate = round((approved_auths / decided * 100), 1) if decided > 0 else 0

    # Recent activity (last 10 auths)
    recent_auths = (PriorAuth.query
        .filter_by(practice_id=pid)
        .order_by(PriorAuth.created_at.desc())
        .limit(10)
        .all())

    # Urgent denials — appeals due within 7 days
    urgent_denials = (Denial.query
        .join(PriorAuth)
        .filter(
            PriorAuth.practice_id == pid,
            Denial.appeal_deadline <= datetime.utcnow().date() + timedelta(days=7),
            Denial.appeal_status.in_(['not_started', 'in_progress'])
        )
        .order_by(Denial.appeal_deadline.asc())
        .limit(5)
        .all())

    # Total patients
    total_patients = Patient.query.filter_by(practice_id=pid).count()

    return render_template('dashboard/home.html',
        total_auths=total_auths,
        pending_auths=pending_auths,
        approved_auths=approved_auths,
        denied_auths=denied_auths,
        approval_rate=approval_rate,
        recent_auths=recent_auths,
        urgent_denials=urgent_denials,
        total_patients=total_patients,
    )

@dashboard_bp.route('/')
def landing():
    from flask import render_template
    return render_template('index.html')

@dashboard_bp.route('/')
def index():
    from flask import render_template
    return render_template('medbridge_ui.html')

import json
from flask import jsonify

@dashboard_bp.route('/api/dashboard')
@login_required
def api_dashboard():
    from app.models import PriorAuth, Patient
    practice_id = current_user.practice_id
    auths = PriorAuth.query.filter_by(practice_id=practice_id).all()
    patients = Patient.query.filter_by(practice_id=practice_id).all()
    total = len(auths)
    pending = len([a for a in auths if a.status == 'pending'])
    approved = len([a for a in auths if a.status == 'approved'])
    denied = len([a for a in auths if a.status == 'denied'])
    rate = round((approved / total * 100)) if total > 0 else 0
    return jsonify({
        'total_auths': total,
        'pending_auths': pending,
        'approved_auths': approved,
        'denied_auths': denied,
        'total_patients': len(patients),
        'approval_rate': rate,
        'recent_auths': [{'patient_name': f'{a.patient.first_name} {a.patient.last_name}' if a.patient else '', 'cpt_code': a.cpt_code, 'payer_name': a.payer_name, 'status': a.status, 'priority': a.priority} for a in auths[:10]]
    })

@dashboard_bp.route('/api/patients')
@login_required
def api_patients():
    from app.models import Patient
    patients = Patient.query.filter_by(practice_id=current_user.practice_id).all()
    return jsonify({'patients': [{'id': p.id, 'first_name': p.first_name, 'last_name': p.last_name, 'date_of_birth': str(p.date_of_birth or ''), 'payer_name': p.payer_name, 'member_id': p.member_id} for p in patients]})
