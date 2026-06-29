# Card Fraud Intelligence

A production-grade card transaction fraud detection and investigation system combining **XGBoost + SHAP** for real-time ML scoring with **Google Gemini AI** for analyst-facing explanations and conversational case investigation.

Built to demonstrate end-to-end banking AI/ML engineering — from raw transaction data to a deployable REST API with a full fraud investigation workflow.

---

## Architecture

```
Transaction Input
      │
      ▼
Feature Engineering ──────────────────────────────────────────────┐
(velocity, location delta, amount z-score, MCC risk, ...)         │
      │                                                            │
      ▼                                                            │
XGBoost Fraud Scorer                                              │
(fraud probability + SHAP values)                                 │
      │                                                            │
      ├── Below threshold ──► Store transaction, return LOW risk  │
      │                                                            │
      └── Above threshold ──► Create Fraud Case ─────────────────┘
                                      │
                                      ▼
                              Gemini AI Layer
                        ┌─────────────────────────┐
                        │  Plain-English Explanation│
                        │  Case Summary (RAG)       │
                        │  Analyst Chat Assistant   │
                        └─────────────────────────┘
                                      │
                                      ▼
                              FastAPI REST API
                        (Auth · Cases · Analytics)
                                      │
                                      ▼
                                  MongoDB
                    (transactions · cases · audit_log)
```

---

## Features

### ML Layer (XGBoost + SHAP)
- Real-time fraud scoring on 21 engineered features
- Behavioral features: transaction velocity (1h/24h/7d), amount z-score vs personal baseline
- Geo features: location delta from last transaction, impossible travel detection
- Risk signals: high-risk MCC codes, new merchant detection, international transactions
- SHAP explainability: every prediction returns top risk factors with directional impact

### AI Layer (Gemini)
- **Fraud Explanation**: Translates SHAP values into plain-English analyst-ready summaries
- **Investigation Chat**: Conversational assistant with full case context — ask anything about a fraud case
- **Case Summary**: AI-generated executive summary with red flags and recommended action
- **Similar Cases**: RAG-based retrieval of historical cases matching MCC/cardholder/risk pattern

### API (FastAPI)
- JWT authentication with role-based access (analyst / senior_analyst / manager)
- Transaction scoring endpoint with sub-100ms response
- Full fraud case lifecycle: OPEN → UNDER_INVESTIGATION → CONFIRMED_FRAUD / FALSE_POSITIVE
- Investigation notes, case assignment, complete audit trail
- Analytics: dashboard KPIs, daily trends, fraud by channel/MCC

---

## Quickstart

### 1. Clone and install
```bash
git clone https://github.com/yourusername/card-fraud-intelligence
cd card-fraud-intelligence
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — set MONGODB_URI and GEMINI_API_KEY
```

### 3. Train the model
```bash
# Generate 50,000 synthetic transactions (2% fraud rate)
python -m training.generate_synthetic_data

# Train XGBoost model with 5-fold CV + SMOTE
python -m training.train

# Evaluate and generate plots
python -m training.evaluate
```

### 4. Start the API
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Explore the API
Open [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive Swagger UI.

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register analyst account |
| POST | `/api/v1/auth/login` | Get JWT token |
| GET | `/api/v1/auth/me` | Current user profile |

### Transactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/transactions/score` | Score a transaction in real-time |
| GET | `/api/v1/transactions/{id}` | Get transaction details |
| GET | `/api/v1/transactions/` | List transactions (filterable) |

### Fraud Cases
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cases/` | List cases (filter by status/risk) |
| GET | `/api/v1/cases/{id}` | Full case detail with explanation |
| PATCH | `/api/v1/cases/{id}/status` | Update case status |
| POST | `/api/v1/cases/{id}/notes` | Add investigation note |
| PATCH | `/api/v1/cases/{id}/assign` | Assign to analyst |

### Investigation (AI)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/investigation/chat` | Chat with AI about a case |
| GET | `/api/v1/investigation/cases/{id}/summary` | AI executive summary |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/dashboard` | KPI dashboard |
| GET | `/api/v1/analytics/trends` | Daily fraud trends |
| GET | `/api/v1/analytics/by-merchant-category` | Fraud by MCC |
| GET | `/api/v1/analytics/by-channel` | Fraud by channel |

---

## Score a Transaction (Example)

```bash
curl -X POST http://localhost:8000/api/v1/transactions/score \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TXN-001",
    "cardholder_id": "CH-0042",
    "card_last4": "7823",
    "card_type": "VISA",
    "amount": 45000.00,
    "merchant_id": "M-9912",
    "merchant_name": "CryptoXchange India",
    "merchant_category_code": "6051",
    "channel": "ONLINE",
    "location_city": "Lagos",
    "location_country": "NG",
    "timestamp": "2025-06-29T02:34:00Z"
  }'
```

**Response:**
```json
{
  "transaction_id": "TXN-001",
  "fraud_probability": 0.9312,
  "is_flagged": true,
  "risk_level": "CRITICAL",
  "fraud_explanation": "This transaction is highly suspicious: a ₹45,000 transfer to a crypto exchange in Nigeria at 2 AM is far outside this cardholder's typical spend pattern, and the merchant category carries the highest fraud risk in our portfolio.",
  "top_risk_factors": [
    {"feature": "is_high_risk_country", "impact": 0.24, "direction": "increases_risk"},
    {"feature": "is_high_risk_mcc", "impact": 0.21, "direction": "increases_risk"},
    {"feature": "amount_zscore", "impact": 0.18, "direction": "increases_risk"},
    {"feature": "is_night", "impact": 0.12, "direction": "increases_risk"}
  ],
  "case_id": "a1b2c3d4-..."
}
```

---

## ML Model Performance

Trained on 50,000 synthetic transactions (IEEE-CIS compatible feature set):

| Metric | Score |
|--------|-------|
| AUC-ROC | ~0.97 |
| Average Precision | ~0.85 |
| Precision @ 0.5 threshold | ~0.88 |
| Recall @ 0.5 threshold | ~0.79 |

> For production use, train on the [IEEE-CIS Fraud Detection](https://www.kaggle.com/c/ieee-fraud-detection) dataset from Kaggle for real-world performance benchmarks.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI + Uvicorn |
| ML Model | XGBoost |
| Explainability | SHAP (TreeExplainer) |
| Class Imbalance | SMOTE (imbalanced-learn) |
| AI / LLM | Google Gemini 2.0 Flash |
| Database | MongoDB (async via Motor) |
| Authentication | JWT (python-jose + passlib bcrypt) |
| Data Processing | Pandas + NumPy |

---

## Domain Context

This system mirrors real-world card fraud operations at banks and NBFCs:

- **MCC-based risk profiling**: Merchant Category Codes 7995 (Gambling), 6051 (Crypto/Wire), 4829 (Money Transfer) carry the highest fraud risk — reflected in feature engineering
- **Velocity rules**: Industry standard — high transaction count in short windows is a primary fraud signal
- **Impossible travel**: A flagged transaction where the cardholder's card was physically swiped in two cities 2000km apart within minutes
- **STR threshold**: Suspicious Transaction Reports under PMLA are mandatory for confirmed fraud above ₹10 lakhs — referenced in AI investigation suggestions
- **Case lifecycle**: Mirrors the actual fraud ops workflow at card-issuing banks (open → investigate → confirm/reject)

---

## Project Structure

```
card-fraud-intelligence/
├── app/
│   ├── api/v1/endpoints/   # FastAPI route handlers
│   ├── core/               # ML scoring, SHAP, Gemini AI
│   ├── db/                 # MongoDB async connection
│   ├── schemas/            # Pydantic request/response models
│   └── services/           # Business logic layer
├── config/                 # Environment settings
├── training/               # Data generation, feature engineering, training
├── data/                   # Raw data (gitignored)
├── models/                 # Trained model files (gitignored)
└── requirements.txt
```
