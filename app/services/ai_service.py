import os
import anthropic

def generate_appeal_letter(
    patient_name: str,
    payer_name: str,
    cpt_code: str,
    cpt_description: str,
    icd10_code: str,
    denial_reason: str,
    clinical_notes: str,
    provider_name: str,
) -> str:
    """
    Call Claude API to generate a professional prior auth appeal letter.
    Falls back to a template if API key is missing (for testing without a key).
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key or api_key == 'sk-ant-your-key-here':
        # Return a template for testing without an API key
        return _fallback_letter(patient_name, payer_name, cpt_code, denial_reason, provider_name)

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are a medical billing specialist with 15 years of experience 
writing successful prior authorization appeal letters.

Write a professional, persuasive appeal letter for the following denied claim:

Patient: {patient_name}
Insurance company: {payer_name}
Procedure CPT code: {cpt_code} — {cpt_description}
Diagnosis ICD-10: {icd10_code}
Denial reason: {denial_reason}
Clinical notes from provider: {clinical_notes if clinical_notes else 'Not provided'}
Requesting provider/practice: {provider_name}

Write the letter with:
1. A formal opening addressing the appeals department
2. Patient and claim identification
3. A direct, factual response to the denial reason
4. A clear medical necessity argument citing standard of care
5. A closing requesting expedited review with a 14-day response deadline

Tone: Professional, clinical, and assertive — not emotional.
Length: 400–550 words. Use formal letter format with today's date placeholder [DATE].
Do not add any commentary outside the letter itself."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def _fallback_letter(patient_name, payer_name, cpt_code, denial_reason, provider_name):
    """Template letter used when no API key is configured."""
    return f"""[DATE]

Appeals Department
{payer_name}

RE: Prior Authorization Appeal — Patient: {patient_name}
Procedure: CPT {cpt_code}

To Whom It May Concern,

We are writing to formally appeal the denial of the above-referenced prior 
authorization request. The denial was issued with the stated reason: "{denial_reason}."

We respectfully disagree with this determination and submit the following 
medical necessity documentation for your reconsideration.

[CLINICAL JUSTIFICATION — Edit this section with patient-specific details]

The requested procedure (CPT {cpt_code}) is medically necessary based on 
the patient's documented clinical history, current symptoms, and the treating 
physician's professional judgment. This treatment aligns with established 
clinical guidelines and represents the most appropriate course of care.

We request that your medical director review this appeal and issue a decision 
within 14 business days. If a peer-to-peer review would be helpful, please 
contact our office to schedule.

Sincerely,

{provider_name}

[Note: This is a template. Add the API key in .env to generate AI-powered letters.]"""


def score_prior_auth(cpt_code: str, icd10_code: str, payer_name: str, clinical_notes: str) -> float:
    """
    Returns a 0.0–1.0 probability score for approval.
    Currently rule-based; swap for ML model in Month 4.
    """
    score = 0.5  # baseline

    # Common high-approval CPTs
    high_approval = ['99213', '99214', '71046', '93000', '80053']
    if cpt_code in high_approval:
        score += 0.2

    # Clinical notes provided = better odds
    if clinical_notes and len(clinical_notes) > 100:
        score += 0.15

    # Known stricter payers
    strict_payers = ['united', 'aetna', 'cigna']
    if any(p in payer_name.lower() for p in strict_payers):
        score -= 0.1

    return min(max(round(score, 2), 0.0), 1.0)
