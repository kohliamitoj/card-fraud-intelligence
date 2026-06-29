import logging
import google.generativeai as genai
from config.settings import settings

logger = logging.getLogger(__name__)

_model = None


def init_gemini() -> None:
    global _model
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set. AI explanations will be unavailable.")
        return
    genai.configure(api_key=settings.GEMINI_API_KEY)
    _model = genai.GenerativeModel("gemini-2.0-flash")
    logger.info("Gemini AI assistant initialised.")


def generate_fraud_explanation(txn: dict, features: dict, risk_factors: list[dict], fraud_prob: float) -> str:
    if _model is None:
        return _fallback_explanation(risk_factors, fraud_prob)

    risk_factor_text = "\n".join(
        f"- {r['feature'].replace('_', ' ').title()}: {r['direction'].replace('_', ' ')} (impact: {r['impact']})"
        for r in risk_factors
    )

    prompt = f"""You are a senior fraud analyst at a bank. A transaction has been flagged by the ML model.

Transaction Details:
- Amount: {txn.get('currency', 'USD')} {txn.get('amount', 0):,.2f}
- Merchant: {txn.get('merchant_name', 'Unknown')} (MCC: {txn.get('merchant_category_code', 'N/A')})
- Channel: {txn.get('channel', 'N/A')}
- Location: {txn.get('location_city', 'N/A')}, {txn.get('location_country', 'N/A')}
- Fraud Probability: {fraud_prob:.1%}

Key Risk Factors identified by the ML model:
{risk_factor_text}

Write a concise, professional 2-3 sentence explanation of why this transaction is suspicious.
Use plain language that a bank operations team can understand. Do not mention SHAP or ML terms."""

    try:
        response = _model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error("Gemini explanation failed: %s", e)
        return _fallback_explanation(risk_factors, fraud_prob)


def answer_investigation_query(case: dict, question: str, history: list[dict]) -> tuple[str, list[str]]:
    if _model is None:
        return "AI assistant is unavailable. Please configure GEMINI_API_KEY.", []

    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in history[-6:]
    )

    prompt = f"""You are an expert fraud investigation assistant at a card-issuing bank.

Case Context:
- Case ID: {case.get('case_id')}
- Transaction Amount: {case.get('currency', 'USD')} {case.get('amount', 0):,.2f}
- Merchant: {case.get('merchant_name')} (MCC: {case.get('merchant_category_code')})
- Fraud Probability: {case.get('fraud_probability', 0):.1%}
- Risk Level: {case.get('risk_level')}
- Current Status: {case.get('status')}
- ML Explanation: {case.get('fraud_explanation', 'N/A')}
- Analyst Notes: {'; '.join(n.get('content', '') for n in case.get('notes', []))}

Conversation History:
{history_text}

Analyst Question: {question}

Answer the question professionally. If suggesting next steps, be specific to card fraud investigation procedures (CBR filing, card blocking, FinCEN/SAR reporting thresholds, etc.)."""

    suggested_actions = []
    try:
        response = _model.generate_content(prompt)
        answer = response.text.strip()

        if case.get("fraud_probability", 0) > 0.8 and case.get("status") == "OPEN":
            suggested_actions = [
                "Block the card immediately to prevent further losses.",
                "Initiate Chargeback Request (CBR) if merchant dispute is applicable.",
                "File SAR if transaction amount exceeds $10,000.",
                "Notify cardholder via SMS/email.",
            ]
        elif case.get("risk_level") in ("HIGH", "CRITICAL"):
            suggested_actions = [
                "Place a temporary hold on the card pending investigation.",
                "Review last 30 days of transaction history for patterns.",
            ]

        return answer, suggested_actions
    except Exception as e:
        logger.error("Gemini investigation query failed: %s", e)
        return "Unable to process query at this time.", []


def generate_case_summary(case: dict, similar_cases: list[dict]) -> str:
    if _model is None:
        return f"Case {case.get('case_id')} flagged at {case.get('fraud_probability', 0):.1%} fraud probability. Manual review required."

    similar_text = ""
    if similar_cases:
        similar_text = "Similar historical cases:\n" + "\n".join(
            f"- Case {c.get('case_id')}: {c.get('similarity_reason')} (Status: {c.get('status')})"
            for c in similar_cases[:3]
        )

    prompt = f"""You are a senior fraud analyst. Generate an executive summary for the following fraud case.

Case Details:
- Transaction: {case.get('currency', 'USD')} {case.get('amount', 0):,.2f} at {case.get('merchant_name')}
- Fraud Probability: {case.get('fraud_probability', 0):.1%}
- Risk Level: {case.get('risk_level')}
- Risk Factors: {case.get('fraud_explanation')}
- Status: {case.get('status')}
{similar_text}

Write an executive summary in 3-4 sentences covering: what happened, why it's suspicious, and recommended action.
Also list 3-5 specific red flags as bullet points."""

    try:
        response = _model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error("Gemini summary failed: %s", e)
        return f"Fraud probability: {case.get('fraud_probability', 0):.1%}. Risk level: {case.get('risk_level')}. Manual review required."


def _fallback_explanation(risk_factors: list[dict], prob: float) -> str:
    if not risk_factors:
        return f"Transaction flagged with {prob:.1%} fraud probability based on behavioural anomalies."
    top = [r["feature"].replace("_", " ") for r in risk_factors[:3] if r["direction"] == "increases_risk"]
    factors_str = ", ".join(top) if top else "multiple risk signals"
    return f"Transaction flagged at {prob:.1%} fraud probability. Key risk indicators: {factors_str}."
