from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from ..models import db, PriorAuth, Patient, AuditLog
from ..services.ai_service import score_prior_auth

prior_auth_bp = Blueprint('prior_auth', __name__)

PAYER_LIST = [
    'UnitedHealthcare', 'Aetna', 'Blue Cross Blue Shield',
    'Cigna', 'Humana', 'Medicare', 'Medicaid',
    'Anthem', 'Centene', 'Molina Healthcare', 'Other'
]


@prior_auth_bp.route('/prior-auths')
@login_required
def list_auths():
    status_filter = request.args.get('status', '')
    search        = request.args.get('search', '').strip()

    query = (PriorAuth.query
        .filter_by(practice_id=current_user.practice_id)
        .join(Patient))

    if status_filter:
        query = query.filter(PriorAuth.status == status_filter)

    if search:
        query = query.filter(
            (Patient.first_name.ilike(f'%{search}%')) |
            (Patient.last_name.ilike(f'%{search}%')) |
            (PriorAuth.cpt_code.ilike(f'%{search}%')) |
            (PriorAuth.payer_name.ilike(f'%{search}%'))
        )

    auths = query.order_by(PriorAuth.created_at.desc()).all()

    status_counts = {
        'all':       PriorAuth.query.filter_by(practice_id=current_user.practice_id).count(),
        'pending':   PriorAuth.query.filter_by(practice_id=current_user.practice_id, status='pending').count(),
        'submitted': PriorAuth.query.filter_by(practice_id=current_user.practice_id, status='submitted').count(),
        'approved':  PriorAuth.query.filter_by(practice_id=current_user.practice_id, status='approved').count(),
        'denied':    PriorAuth.query.filter_by(practice_id=current_user.practice_id, status='denied').count(),
    }

    return render_template('prior_auth/list.html',
        auths=auths,
        status_filter=status_filter,
        search=search,
        status_counts=status_counts,
        payers=PAYER_LIST,
    )


@prior_auth_bp.route('/prior-auths/new', methods=['GET', 'POST'])
@login_required
def new_auth():
    patients = Patient.query.filter_by(practice_id=current_user.practice_id).order_by(Patient.last_name).all()

    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        if not patient_id:
            flash('Please select a patient.', 'danger')
            return render_template('prior_auth/new.html', patients=patients, payers=PAYER_LIST)

        proc_date_str = request.form.get('procedure_date')
        proc_date = None
        if proc_date_str:
            try:
                proc_date = datetime.strptime(proc_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        auth = PriorAuth(
            practice_id      = current_user.practice_id,
            patient_id       = int(patient_id),
            submitted_by     = current_user.id,
            cpt_code         = request.form.get('cpt_code', '').strip(),
            cpt_description  = request.form.get('cpt_description', '').strip(),
            icd10_code       = request.form.get('icd10_code', '').strip(),
            icd10_description= request.form.get('icd10_description', '').strip(),
            provider_name    = request.form.get('provider_name', '').strip(),
            provider_npi     = request.form.get('provider_npi', '').strip(),
            payer_name       = request.form.get('payer_name', '').strip(),
            payer_phone      = request.form.get('payer_phone', '').strip(),
            clinical_notes   = request.form.get('clinical_notes', '').strip(),
            procedure_date   = proc_date,
            priority         = request.form.get('priority', 'normal'),
            status           = 'pending',
        )
        db.session.add(auth)
        db.session.flush()

        # Log it
        log = AuditLog(
            practice_id=current_user.practice_id,
            user_id=current_user.id,
            prior_auth_id=auth.id,
            action='AUTH_CREATED',
            resource_type='prior_auth',
            resource_id=auth.id,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        flash('Prior authorization request created successfully.', 'success')
        return redirect(url_for('prior_auth.view_auth', auth_id=auth.id))

    return render_template('prior_auth/new.html', patients=patients, payers=PAYER_LIST)


@prior_auth_bp.route('/prior-auths/<int:auth_id>')
@login_required
def view_auth(auth_id):
    auth = PriorAuth.query.filter_by(
        id=auth_id,
        practice_id=current_user.practice_id
    ).first_or_404()

    return render_template('prior_auth/view.html', auth=auth)


@prior_auth_bp.route('/prior-auths/<int:auth_id>/update-status', methods=['POST'])
@login_required
def update_status(auth_id):
    auth = PriorAuth.query.filter_by(
        id=auth_id,
        practice_id=current_user.practice_id
    ).first_or_404()

    new_status  = request.form.get('status')
    auth_number = request.form.get('auth_number', '').strip()
    valid = ['pending', 'submitted', 'approved', 'denied', 'cancelled', 'info_needed']

    if new_status not in valid:
        flash('Invalid status.', 'danger')
        return redirect(url_for('prior_auth.view_auth', auth_id=auth_id))

    old_status  = auth.status
    auth.status = new_status

    if new_status == 'submitted' and not auth.submitted_at:
        auth.submitted_at = datetime.utcnow()
    if new_status in ['approved', 'denied']:
        auth.decision_at = datetime.utcnow()
    if auth_number:
        auth.auth_number = auth_number

    log = AuditLog(
        practice_id=current_user.practice_id,
        user_id=current_user.id,
        prior_auth_id=auth.id,
        action='AUTH_STATUS_UPDATED',
        resource_type='prior_auth',
        resource_id=auth.id,
        notes=f'Status changed from {old_status} to {new_status}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    flash(f'Status updated to {new_status.replace("_", " ").title()}.', 'success')
    return redirect(url_for('prior_auth.view_auth', auth_id=auth_id))

from flask import jsonify

@prior_auth_bp.route('/api/prior-auths')
@login_required
def api_list_auths():
    auths = PriorAuth.query.filter_by(practice_id=current_user.practice_id).all()
    return jsonify({'auths': [{'id': a.id, 'patient_name': f'{a.patient.first_name} {a.patient.last_name}' if a.patient else '', 'cpt_code': a.cpt_code, 'payer_name': a.payer_name, 'status': a.status, 'priority': a.priority} for a in auths]})

@prior_auth_bp.route('/api/prior-auths/<int:auth_id>/status', methods=['POST'])
@login_required
def api_update_status(auth_id):
    from flask import request
    from app.services.email_service import send_status_update_email
    auth = PriorAuth.query.filter_by(id=auth_id, practice_id=current_user.practice_id).first()
    if not auth:
        return jsonify({'error': 'Not found'}), 404
    old_status = auth.status
    new_status = data.get('status', auth.status) if (data := request.get_json()) else auth.status
    auth.status = new_status
    db.session.commit()
    
    # Send email notification if status changed
    if old_status != new_status:
        try:
            patient_name = f"{auth.patient.first_name} {auth.patient.last_name}" if auth.patient else "Patient"
            send_status_update_email(
                user_email=current_user.email,
                user_name=current_user.first_name or current_user.email.split("@")[0],
                patient_name=patient_name,
                cpt_code=auth.cpt_code or "",
                payer=auth.payer_name or "",
                old_status=old_status,
                new_status=new_status
            )
        except Exception as e:
            pass  # Don't fail the request if email fails
    
    return jsonify({'success': True})
