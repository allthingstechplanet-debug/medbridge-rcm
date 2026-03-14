from app import create_app, db
from app.models import User, Practice, Patient, PriorAuth
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    # Check if demo already exists
    if Practice.query.filter_by(name='Northside Orthopedics').first():
        print("Demo data already exists!")
        exit()

    # Create demo practice
    practice = Practice(name='Northside Orthopedics', specialty='Orthopedics')
    db.session.add(practice)
    db.session.flush()

    # Create demo admin user
    user = User(
        email='demo@northside.com',
        practice_id=practice.id,
        first_name='Sarah',
        last_name='Mitchell',
        role='admin'
    )
    user.set_password('Demo1234!') if hasattr(user, 'set_password') else None
    db.session.add(user)
    db.session.flush()

    # Create demo patients
    patients_data = [
        ('Michael', 'Johnson', '1965-03-15', 'UnitedHealthcare', 'UHC-4521890'),
        ('Patricia', 'Williams', '1958-07-22', 'Aetna', 'AET-7823456'),
        ('Robert', 'Davis', '1972-11-08', 'Blue Cross Blue Shield', 'BCBS-3341290'),
        ('Jennifer', 'Martinez', '1980-04-30', 'Cigna', 'CIG-9087234'),
        ('William', 'Anderson', '1955-09-14', 'Medicare', 'MED-1234567A'),
        ('Linda', 'Thompson', '1968-01-25', 'Humana', 'HUM-5678901'),
        ('James', 'Garcia', '1975-06-18', 'Aetna', 'AET-2345678'),
        ('Barbara', 'Wilson', '1962-12-03', 'UnitedHealthcare', 'UHC-8901234'),
    ]

    patients = []
    for fn, ln, dob, payer, mid in patients_data:
        p = Patient(
            practice_id=practice.id,
            first_name=fn, last_name=ln,
            date_of_birth=datetime.strptime(dob, '%Y-%m-%d').date(),
            payer_name=payer, member_id=mid
        )
        db.session.add(p)
        patients.append(p)
    db.session.flush()

    # Create demo prior auths
    auths_data = [
        (0, '27447', 'Total Knee Replacement', 'M17.11', 'approved', 'normal', 'Patient has severe osteoarthritis, failed 6 months PT and injections.'),
        (1, '70553', 'MRI Brain with contrast', 'G43.909', 'approved', 'normal', 'Chronic migraines unresponsive to medication for 8 months.'),
        (2, '29827', 'Arthroscopic Rotator Cuff Repair', 'M75.121', 'pending', 'urgent', 'Full thickness rotator cuff tear confirmed on MRI. Failed conservative treatment.'),
        (3, '27130', 'Total Hip Arthroplasty', 'M16.11', 'pending', 'normal', 'End-stage osteoarthritis, severe pain limiting all daily activities.'),
        (4, '93306', 'Echocardiogram', 'I50.9', 'submitted', 'normal', 'Heart failure monitoring, ejection fraction 35%.'),
        (5, '29881', 'Arthroscopic Knee Meniscectomy', 'M23.201', 'denied', 'normal', 'Medial meniscus tear confirmed on MRI. Patient unable to walk without pain.'),
        (6, '22612', 'Lumbar Spinal Fusion', 'M51.16', 'pending', 'urgent', 'Severe lumbar stenosis with neurogenic claudication. Failed 12 months conservative care.'),
        (7, '27486', 'Revision Total Knee Replacement', 'T84.052A', 'approved', 'normal', 'Aseptic loosening of prior knee replacement confirmed on imaging.'),
        (2, '20610', 'Joint Injection - Knee', 'M17.31', 'denied', 'normal', 'Moderate osteoarthritis with pain uncontrolled by oral medications.'),
        (4, '71046', 'Chest X-Ray 2 views', 'J18.9', 'approved', 'normal', 'Pneumonia follow-up imaging required.'),
    ]

    statuses = ['approved', 'pending', 'submitted', 'denied']
    for i, (pat_idx, cpt, cpt_desc, icd, status, priority, notes) in enumerate(auths_data):
        days_ago = random.randint(1, 45)
        a = PriorAuth(
            practice_id=practice.id,
            patient_id=patients[pat_idx].id,
            cpt_code=cpt,
            cpt_description=cpt_desc,
            icd10_code=icd,
            payer_name=patients[pat_idx].payer_name,
            status=status,
            priority=priority,
            clinical_notes=notes,
            created_at=datetime.utcnow() - timedelta(days=days_ago)
        )
        if status == 'approved':
            a.ai_approval_score = round(random.uniform(0.72, 0.95), 2)
        elif status == 'denied':
            a.ai_approval_score = round(random.uniform(0.15, 0.40), 2)
        db.session.add(a)

    db.session.commit()
    print("✅ Demo data created successfully!")
    print("")
    print("Demo login credentials:")
    print("  Email:    demo@northside.com")
    print("  Password: Demo1234!")
    print("")
    print("Created:")
    print(f"  - 1 practice: Northside Orthopedics")
    print(f"  - 8 patients")
    print(f"  - 10 prior authorizations (mix of approved/pending/denied)")
