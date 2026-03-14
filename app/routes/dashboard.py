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

@dashboard_bp.route('/seed-demo-data-xyz123')
def seed_demo():
    from app.models import Patient, PriorAuth, Practice, User
    from datetime import datetime, timedelta
    import random
    if Practice.query.filter_by(name='Northside Orthopedics').first():
        return 'Demo data already exists! <a href="/login">Login</a> with demo@northside.com / Demo1234!'
    practice = Practice(name='Northside Orthopedics')
    db.session.add(practice)
    db.session.flush()
    user = User(email='demo@northside.com', practice_id=practice.id,
        first_name='Sarah', last_name='Mitchell', role='admin')
    user.set_password('Demo1234!')
    db.session.add(user)
    db.session.flush()
    patients_data = [
        ('Michael','Johnson','1965-03-15','UnitedHealthcare','UHC-4521890'),
        ('Patricia','Williams','1958-07-22','Aetna','AET-7823456'),
        ('Robert','Davis','1972-11-08','Blue Cross Blue Shield','BCBS-3341290'),
        ('Jennifer','Martinez','1980-04-30','Cigna','CIG-9087234'),
        ('William','Anderson','1955-09-14','Medicare','MED-1234567A'),
        ('Linda','Thompson','1968-01-25','Humana','HUM-5678901'),
        ('James','Garcia','1975-06-18','Aetna','AET-2345678'),
        ('Barbara','Wilson','1962-12-03','UnitedHealthcare','UHC-8901234'),
    ]
    patients = []
    for fn,ln,dob,payer,mid in patients_data:
        p = Patient(practice_id=practice.id, first_name=fn, last_name=ln,
            date_of_birth=datetime.strptime(dob,'%Y-%m-%d').date(),
            payer_name=payer, member_id=mid)
        db.session.add(p)
        patients.append(p)
    db.session.flush()
    auths = [
        (0,'27447','M17.11','approved','normal','Severe osteoarthritis, failed PT and injections for 6 months.'),
        (1,'70553','G43.909','approved','normal','Chronic migraines unresponsive to medication.'),
        (2,'29827','M75.121','pending','urgent','Full thickness rotator cuff tear on MRI. Failed conservative treatment.'),
        (3,'27130','M16.11','pending','normal','End-stage osteoarthritis, severe pain limiting daily activities.'),
        (4,'93306','I50.9','submitted','normal','Heart failure monitoring, ejection fraction 35%.'),
        (5,'29881','M23.201','denied','normal','Medial meniscus tear on MRI. Patient unable to walk without pain.'),
        (6,'22612','M51.16','pending','urgent','Severe lumbar stenosis. Failed 12 months conservative care.'),
        (7,'27486','T84.052A','approved','normal','Aseptic loosening of prior knee replacement.'),
        (2,'20610','M17.31','denied','normal','Moderate osteoarthritis, pain uncontrolled by oral medications.'),
        (4,'71046','J18.9','approved','normal','Pneumonia follow-up imaging required.'),
    ]
    for pat_idx,cpt,icd,status,priority,notes in auths:
        a = PriorAuth(practice_id=practice.id, patient_id=patients[pat_idx].id,
            cpt_code=cpt, icd10_code=icd, payer_name=patients[pat_idx].payer_name,
            status=status, priority=priority, clinical_notes=notes,
            created_at=datetime.utcnow()-timedelta(days=random.randint(1,45)))
        db.session.add(a)
    db.session.commit()
    return '''<h2>✅ Demo data created!</h2>
    <p><strong>Email:</strong> demo@northside.com</p>
    <p><strong>Password:</strong> Demo1234!</p>
    <p><a href="/login">Click here to login</a></p>'''
