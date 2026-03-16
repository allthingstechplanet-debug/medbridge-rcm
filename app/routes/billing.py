from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from app import db
import os

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/api/billing/create-checkout', methods=['POST'])
@login_required
def create_checkout():
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        price_id = os.environ.get('STRIPE_PRICE_ID')
        
        if not stripe.api_key:
            return jsonify({'error': 'Stripe not configured'}), 400
            
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=request.host_url + 'billing/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'login',
            metadata={'practice_id': current_user.practice_id}
        )
        return jsonify({'url': checkout_session.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@billing_bp.route('/billing/success')
@login_required
def billing_success():
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        session_id = request.args.get('session_id')
        if session_id:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                from app.models import Practice
                practice = Practice.query.get(current_user.practice_id)
                if practice:
                    practice.subscription_tier = 'starter'
                    db.session.commit()
    except Exception:
        pass
    return render_template('medbridge_ui.html')

@billing_bp.route('/api/billing/status')
@login_required
def billing_status():
    try:
        from app.models import Practice
        practice = Practice.query.get(current_user.practice_id)
        tier = practice.subscription_tier if practice and hasattr(practice, 'subscription_tier') else 'trial'
    except Exception:
        tier = 'trial'
    return jsonify({'tier': tier, 'is_paid': tier in ['starter', 'growth', 'enterprise']})

@billing_bp.route('/billing/webhook', methods=['POST'])
def webhook():
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            event = stripe.Event.construct_from(request.json, stripe.api_key)
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            practice_id = session.get('metadata', {}).get('practice_id')
            if practice_id:
                from app.models import Practice
                practice = Practice.query.get(int(practice_id))
                if practice:
                    practice.subscription_tier = 'starter'
                    db.session.commit()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
