import os
import resend

def send_email(to, subject, html_body):
    try:
        resend.api_key = os.environ.get('RESEND_API_KEY')
        if not resend.api_key:
            print("RESEND_API_KEY not set")
            return False
        resend.Emails.send({
            "from": "MedBridge RCM <onboarding@resend.dev>",
            "to": to,
            "subject": subject,
            "html": html_body
        })
        return True
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False
