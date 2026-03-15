from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging

def check_appeal_deadlines(app):
    with app.app_context():
        try:
            from app.models import PriorAuth, User
            from app.services.email_service import send_deadline_warning_email
            
            # Find denied auths with deadlines in 7 days or less
            deadline_threshold = datetime.utcnow() + timedelta(days=7)
            
            denied_auths = PriorAuth.query.filter_by(status='denied').all()
            
            for auth in denied_auths:
                if not auth.created_at:
                    continue
                
                # Appeal window is typically 30 days from denial
                appeal_deadline = auth.created_at + timedelta(days=30)
                days_remaining = (appeal_deadline - datetime.utcnow()).days
                
                if 0 < days_remaining <= 7:
                    # Get practice admin user
                    user = User.query.filter_by(
                        practice_id=auth.practice_id, 
                        role='admin'
                    ).first()
                    
                    if user:
                        patient_name = f"{auth.patient.first_name} {auth.patient.last_name}" if auth.patient else "Patient"
                        send_deadline_warning_email(
                            user_email=user.email,
                            user_name=user.first_name or user.email.split('@')[0],
                            patient_name=patient_name,
                            cpt_code=auth.cpt_code or "",
                            payer=auth.payer_name or "",
                            days_remaining=days_remaining
                        )
        except Exception as e:
            logging.error(f"Deadline check failed: {str(e)}")

def start_scheduler(app):
    scheduler = BackgroundScheduler()
    # Run deadline check every morning at 8am
    scheduler.add_job(
        func=lambda: check_appeal_deadlines(app),
        trigger='cron',
        hour=8,
        minute=0
    )
    scheduler.start()
    return scheduler
