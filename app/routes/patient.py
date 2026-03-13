from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import db, Patient, AuditLog
from datetime import datetime

patient_bp = Blueprint('patient', __name__)


@patient_bp.route('/patients')
@login_required
def list_patients():
    search = request.args.get('search', '').strip()
    query  = Patient.query.filter_by(practice_id=current_user.practice_id)

    if search:
        query = query.filter(
            (Patient.first_name.ilike(f'%{search}%')) |
            (Patient.last_name.ilike(f'%{search}%')) |
            (Patient.member_id.ilike(f'%{search}%'))
        )

    patients = query.order_by(Patient.last_name).all()
    return render_template('dashboard/patients.html', patients=patients, search=search)


@patient_bp.route('/patients/new', methods=['GET', 'POST'])
@login_required
def new_patient():
    if request.method == 'POST':
        dob_str = request.form.get('date_of_birth')
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Invalid date of birth format.', 'danger')
            return render_template('dashboard/patient_form.html')

        patient = Patient(
            practice_id   = current_user.practice_id,
            first_name    = request.form.get('first_name', '').strip(),
            last_name     = request.form.get('last_name', '').strip(),
            date_of_birth = dob,
            member_id     = request.form.get('member_id', '').strip(),
            group_number  = request.form.get('group_number', '').strip(),
            payer_name    = request.form.get('payer_name', '').strip(),
            phone         = request.form.get('phone', '').strip(),
        )
        db.session.add(patient)
        db.session.flush()

        log = AuditLog(
            practice_id=current_user.practice_id,
            user_id=current_user.id,
            action='PATIENT_CREATED',
            resource_type='patient',
            resource_id=patient.id,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        flash(f'Patient {patient.full_name} added successfully.', 'success')
        return redirect(url_for('patient.list_patients'))

    return render_template('dashboard/patient_form.html')
