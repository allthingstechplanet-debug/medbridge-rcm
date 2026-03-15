from flask import current_app, render_template_string
from flask_mail import Mail, Message
from app import db

mail = Mail()

def init_mail(app):
    mail.init_app(app)

def send_email(to, subject, html_body):
    try:
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            html=html_body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Email failed: {str(e)}")
        return False

def send_status_update_email(user_email, user_name, patient_name, 
                              cpt_code, payer, old_status, new_status):
    status_colors = {
        'approved': '#059669',
        'denied': '#DC2626',
        'pending': '#D97706',
        'submitted': '#2563EB'
    }
    color = status_colors.get(new_status, '#4F46E5')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family:'DM Sans',Arial,sans-serif;background:#F8FAFC;margin:0;padding:40px 20px;">
      <div style="max-width:560px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
        
        <!-- Header -->
        <div style="background:linear-gradient(135deg,#3730A3,#4F46E5);padding:32px;text-align:center;">
          <div style="display:inline-flex;align-items:center;gap:10px;">
            <div style="width:36px;height:36px;background:rgba(255,255,255,0.2);border-radius:10px;display:inline-flex;align-items:center;justify-content:center;">
              <span style="color:white;font-size:18px;">+</span>
            </div>
            <span style="color:white;font-size:20px;font-weight:700;">MedBridge RCM</span>
          </div>
        </div>

        <!-- Body -->
        <div style="padding:32px;">
          <h2 style="font-size:22px;font-weight:700;margin-bottom:8px;color:#0F172A;">
            Authorization Status Updated
          </h2>
          <p style="color:#64748B;font-size:15px;margin-bottom:24px;">
            Hi {user_name}, a prior authorization has been updated.
          </p>

          <!-- Status badge -->
          <div style="background:#F8FAFC;border-radius:12px;padding:20px;margin-bottom:24px;border:1px solid #E2E8F0;">
            <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
              <span style="color:#64748B;font-size:13px;">Patient</span>
              <span style="font-weight:600;font-size:14px;">{patient_name}</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
              <span style="color:#64748B;font-size:13px;">CPT Code</span>
              <span style="font-weight:600;font-size:14px;font-family:monospace;">{cpt_code}</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
              <span style="color:#64748B;font-size:13px;">Payer</span>
              <span style="font-weight:600;font-size:14px;">{payer}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <span style="color:#64748B;font-size:13px;">New Status</span>
              <span style="background:{color};color:white;padding:4px 14px;border-radius:999px;font-size:13px;font-weight:600;text-transform:uppercase;">
                {new_status}
              </span>
            </div>
          </div>

          <!-- CTA -->
          <a href="https://medbridge-rcm-production.up.railway.app/login" 
             style="display:block;background:#4F46E5;color:white;text-align:center;padding:14px;border-radius:10px;font-weight:600;font-size:15px;text-decoration:none;">
            View in MedBridge →
          </a>
        </div>

        <!-- Footer -->
        <div style="background:#F8FAFC;padding:20px 32px;border-top:1px solid #E2E8F0;">
          <p style="color:#94A3B8;font-size:12px;margin:0;text-align:center;">
            © 2026 MedBridge RCM Inc. · You're receiving this because you have an account at MedBridge.
          </p>
        </div>
      </div>
    </body>
    </html>
    """
    
    subject = f"Prior Auth {new_status.upper()}: {patient_name} — {cpt_code}"
    return send_email(user_email, subject, html)


def send_deadline_warning_email(user_email, user_name, patient_name,
                                 cpt_code, payer, days_remaining):
    urgency_color = '#DC2626' if days_remaining <= 3 else '#D97706'
    urgency_text = 'URGENT' if days_remaining <= 3 else 'WARNING'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:Arial,sans-serif;background:#F8FAFC;margin:0;padding:40px 20px;">
      <div style="max-width:560px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
        
        <div style="background:linear-gradient(135deg,#3730A3,#4F46E5);padding:32px;text-align:center;">
          <span style="color:white;font-size:20px;font-weight:700;">MedBridge RCM</span>
        </div>

        <div style="padding:32px;">
          <!-- Urgency banner -->
          <div style="background:{urgency_color};border-radius:10px;padding:14px 20px;margin-bottom:24px;display:flex;align-items:center;gap:12px;">
            <span style="font-size:20px;">⚠️</span>
            <div>
              <div style="color:white;font-weight:700;font-size:15px;">{urgency_text}: Appeal Deadline Approaching</div>
              <div style="color:rgba(255,255,255,0.85);font-size:13px;">{days_remaining} day{'s' if days_remaining != 1 else ''} remaining to file appeal</div>
            </div>
          </div>

          <p style="color:#64748B;font-size:15px;margin-bottom:24px;">
            Hi {user_name}, a denied authorization needs your attention.
          </p>

          <div style="background:#F8FAFC;border-radius:12px;padding:20px;margin-bottom:24px;border:1px solid #E2E8F0;">
            <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
              <span style="color:#64748B;font-size:13px;">Patient</span>
              <span style="font-weight:600;font-size:14px;">{patient_name}</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
              <span style="color:#64748B;font-size:13px;">CPT Code</span>
              <span style="font-weight:600;font-size:14px;font-family:monospace;">{cpt_code}</span>
            </div>
            <div style="display:flex;justify-content:space-between;">
              <span style="color:#64748B;font-size:13px;">Payer</span>
              <span style="font-weight:600;font-size:14px;">{payer}</span>
            </div>
          </div>

          <a href="https://medbridge-rcm-production.up.railway.app/login"
             style="display:block;background:#DC2626;color:white;text-align:center;padding:14px;border-radius:10px;font-weight:600;font-size:15px;text-decoration:none;">
            File Appeal Now →
          </a>
        </div>

        <div style="background:#F8FAFC;padding:20px 32px;border-top:1px solid #E2E8F0;">
          <p style="color:#94A3B8;font-size:12px;margin:0;text-align:center;">
            © 2026 MedBridge RCM Inc.
          </p>
        </div>
      </div>
    </body>
    </html>
    """
    
    subject = f"⚠️ Appeal Deadline in {days_remaining} Days: {patient_name} — {cpt_code}"
    return send_email(user_email, subject, html)
