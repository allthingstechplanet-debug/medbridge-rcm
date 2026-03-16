import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(to, subject, html_body):
    try:
        api_key = os.environ.get('SENDGRID_API_KEY')
        sender = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@medbridge.com')
        if not api_key:
            print("SENDGRID_API_KEY not set")
            return False
        message = Mail(
            from_email=sender,
            to_emails=to,
            subject=subject,
            html_content=html_body
        )
        sg = SendGridAPIClient(api_key)
        sg.send(message)
        return True
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False

def send_status_update_email(user_email, user_name, patient_name,
                              cpt_code, payer, old_status, new_status):
    colors = {'approved':'#059669','denied':'#DC2626',
              'pending':'#D97706','submitted':'#2563EB'}
    color = colors.get(new_status, '#4F46E5')
    html = f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background:#F8FAFC;margin:0;padding:40px 20px;">
  <div style="max-width:560px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
    <div style="background:linear-gradient(135deg,#3730A3,#4F46E5);padding:32px;text-align:center;">
      <span style="color:white;font-size:22px;font-weight:700;">MedBridge RCM</span>
    </div>
    <div style="padding:32px;">
      <h2 style="font-size:22px;font-weight:700;margin-bottom:8px;color:#0F172A;">Authorization Status Updated</h2>
      <p style="color:#64748B;font-size:15px;margin-bottom:24px;">Hi {user_name}, a prior authorization has been updated.</p>
      <div style="background:#F8FAFC;border-radius:12px;padding:20px;margin-bottom:24px;border:1px solid #E2E8F0;">
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="color:#64748B;font-size:13px;padding:6px 0;">Patient</td><td style="font-weight:600;font-size:14px;text-align:right;">{patient_name}</td></tr>
          <tr><td style="color:#64748B;font-size:13px;padding:6px 0;">CPT Code</td><td style="font-weight:600;font-size:14px;text-align:right;font-family:monospace;">{cpt_code}</td></tr>
          <tr><td style="color:#64748B;font-size:13px;padding:6px 0;">Payer</td><td style="font-weight:600;font-size:14px;text-align:right;">{payer}</td></tr>
          <tr><td style="color:#64748B;font-size:13px;padding:6px 0;">New Status</td><td style="text-align:right;"><span style="background:{color};color:white;padding:4px 14px;border-radius:999px;font-size:13px;font-weight:600;">{new_status.upper()}</span></td></tr>
        </table>
      </div>
      <a href="https://medbridge-rcm-production.up.railway.app/login"
         style="display:block;background:#4F46E5;color:white;text-align:center;padding:14px;border-radius:10px;font-weight:600;font-size:15px;text-decoration:none;">
        View in MedBridge
      </a>
    </div>
    <div style="background:#F8FAFC;padding:20px;border-top:1px solid #E2E8F0;text-align:center;">
      <p style="color:#94A3B8;font-size:12px;margin:0;">2026 MedBridge RCM Inc.</p>
    </div>
  </div>
</body>
</html>"""
    return send_email(user_email, f"Prior Auth {new_status.upper()}: {patient_name} - {cpt_code}", html)

def send_deadline_warning_email(user_email, user_name, patient_name,
                                 cpt_code, payer, days_remaining):
    color = '#DC2626' if days_remaining <= 3 else '#D97706'
    html = f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background:#F8FAFC;margin:0;padding:40px 20px;">
  <div style="max-width:560px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;">
    <div style="background:linear-gradient(135deg,#3730A3,#4F46E5);padding:32px;text-align:center;">
      <span style="color:white;font-size:22px;font-weight:700;">MedBridge RCM</span>
    </div>
    <div style="padding:32px;">
      <div style="background:{color};border-radius:10px;padding:16px;margin-bottom:24px;">
        <div style="color:white;font-weight:700;font-size:16px;">Appeal Deadline in {days_remaining} Day{'s' if days_remaining!=1 else ''}</div>
        <div style="color:rgba(255,255,255,0.85);font-size:13px;margin-top:4px;">Immediate action required</div>
      </div>
      <p style="color:#64748B;font-size:15px;margin-bottom:24px;">Hi {user_name}, a denied authorization needs your attention.</p>
      <div style="background:#F8FAFC;border-radius:12px;padding:20px;margin-bottom:24px;border:1px solid #E2E8F0;">
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="color:#64748B;font-size:13px;padding:6px 0;">Patient</td><td style="font-weight:600;text-align:right;">{patient_name}</td></tr>
          <tr><td style="color:#64748B;font-size:13px;padding:6px 0;">CPT Code</td><td style="font-weight:600;text-align:right;font-family:monospace;">{cpt_code}</td></tr>
          <tr><td style="color:#64748B;font-size:13px;padding:6px 0;">Payer</td><td style="font-weight:600;text-align:right;">{payer}</td></tr>
          <tr><td style="color:#64748B;font-size:13px;padding:6px 0;">Days Left</td><td style="font-weight:700;text-align:right;color:{color};">{days_remaining}</td></tr>
        </table>
      </div>
      <a href="https://medbridge-rcm-production.up.railway.app/login"
         style="display:block;background:{color};color:white;text-align:center;padding:14px;border-radius:10px;font-weight:600;text-decoration:none;">
        File Appeal Now
      </a>
    </div>
  </div>
</body>
</html>"""
    return send_email(user_email, f"Appeal Deadline in {days_remaining} Days: {patient_name}", html)
