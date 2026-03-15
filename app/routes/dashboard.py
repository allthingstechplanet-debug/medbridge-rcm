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
    from app import db
    from app.models import Practice, User, Patient, PriorAuth
    from datetime import datetime
    try:
        if User.query.filter_by(email='demo@northside.com').first():
            return 'Demo user exists! Login: demo@northside.com / Demo1234! <a href="/login">Go</a>'
        p = Practice(name='Demo Practice')
        db.session.add(p)
        db.session.flush()
        u = User(email='demo@northside.com', practice_id=p.id,
            first_name='Sarah', last_name='Mitchell', role='admin')
        u.set_password('Demo1234!')
        db.session.add(u)
        db.session.flush()
        pats = []
        for fn,ln,payer,mid in [
            ('Michael','Johnson','UnitedHealthcare','UHC-452189'),
            ('Patricia','Williams','Aetna','AET-782345'),
            ('Robert','Davis','Blue Cross','BCBS-334129'),
            ('Jennifer','Martinez','Cigna','CIG-908723'),
            ('William','Anderson','Medicare','MED-123456'),
            ('Linda','Thompson','Humana','HUM-567890'),
        ]:
            pt = Patient(practice_id=p.id, first_name=fn,
                last_name=ln, payer_name=payer, member_id=mid)
            db.session.add(pt)
            pats.append(pt)
        db.session.flush()
        for pi,cpt,icd,status,priority in [
            (0,'27447','M17.11','approved','normal'),
            (1,'70553','G43.909','approved','normal'),
            (2,'29827','M75.121','pending','urgent'),
            (3,'27130','M16.11','pending','normal'),
            (4,'93306','I50.9','submitted','normal'),
            (5,'29881','M23.201','denied','normal'),
            (0,'22612','M51.16','pending','urgent'),
            (1,'20610','M17.31','denied','normal'),
        ]:
            a = PriorAuth(practice_id=p.id,
                patient_id=pats[pi].id,
                cpt_code=cpt, icd10_code=icd,
                payer_name=pats[pi].payer_name,
                status=status, priority=priority)
            db.session.add(a)
        db.session.commit()
        return '<h2>✅ Done!</h2><p>Email: demo@northside.com</p><p>Password: Demo1234!</p><a href="/login">Login now</a>'
    except Exception as e:
        db.session.rollback()
        return 'Error: ' + str(e)
