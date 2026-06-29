# Deployment Guide — Making It Publicly Accessible

This guide makes the project fully public:
- **Frontend** → Vercel (free, auto-deploys from GitHub)
- **Backend**  → Railway (free tier)
- **Database** → MongoDB Atlas (free M0 cluster)

---

## Step 1 — Push to GitHub

```bash
cd /Users/amitojsinghkohli/Documents/Self_Projects/card-fraud-intelligence
git init
git add .
git commit -m "Initial commit: Card Fraud Intelligence"
# Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/card-fraud-intelligence.git
git push -u origin main
```

---

## Step 2 — MongoDB Atlas (Cloud Database)

1. Go to https://cloud.mongodb.com → Create a free account
2. Click **Build a Cluster** → choose **M0 Free**
3. Choose a cloud provider (AWS) and region closest to you
4. Set a username + password → **Create User**
5. Under **Network Access** → Add IP Address → **Allow Access from Anywhere** (0.0.0.0/0)
6. Click **Connect** → **Drivers** → copy the connection string:
   ```
   mongodb+srv://USERNAME:PASSWORD@cluster0.xxxxx.mongodb.net/
   ```
7. Replace `<password>` with your actual password — save this string

---

## Step 3 — Deploy Backend on Railway

1. Go to https://railway.app → sign in with GitHub
2. Click **New Project** → **Deploy from GitHub repo** → select `card-fraud-intelligence`
3. Railway auto-detects the `Dockerfile` and starts building
4. Go to **Variables** tab and add these environment variables:

   | Key | Value |
   |-----|-------|
   | `MONGODB_URI` | your Atlas connection string from Step 2 |
   | `DB_NAME` | `card_fraud_intelligence` |
   | `GEMINI_API_KEY` | your Gemini API key |
   | `SECRET_KEY` | any long random string |
   | `ALGORITHM` | `HS256` |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
   | `MODEL_PATH` | `models/fraud_detector.pkl` |
   | `SHAP_EXPLAINER_PATH` | `models/shap_explainer.pkl` |
   | `FRAUD_THRESHOLD` | `0.5` |

5. Go to **Settings** → **Networking** → **Generate Domain**
   - You'll get a URL like: `https://card-fraud-intelligence-production.up.railway.app`
   - Save this — it's your **API URL**

6. Test it: visit `https://your-railway-url/health` → should return `{"status":"ok"}`

> **Note on model files:** Railway doesn't persist local files between deploys.
> To use the trained model, either:
> - Upload `fraud_detector.pkl` and `shap_explainer.pkl` to a public S3/GCS bucket and add a startup script to download them
> - Or leave it — the API works in demo mode without the model (returns realistic scores)

---

## Step 4 — Deploy Frontend on Vercel

1. Go to https://vercel.com → sign in with GitHub
2. Click **Add New Project** → import `card-fraud-intelligence`
3. Set **Root Directory** to `frontend`
4. Framework preset: **Vite**
5. Add environment variable:

   | Key | Value |
   |-----|-------|
   | `VITE_API_URL` | your Railway URL (e.g. `https://card-fraud-intelligence-production.up.railway.app`) |

6. Click **Deploy**
7. You'll get a URL like: `https://card-fraud-intelligence.vercel.app` ← **your public portfolio URL**

---

## Step 5 — Create Demo User

Once deployed, register the demo analyst account by hitting your Railway API:

```bash
curl -X POST https://YOUR-RAILWAY-URL/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst1",
    "email": "analyst1@bank.com",
    "full_name": "Demo Analyst",
    "password": "securepass123",
    "role": "senior_analyst"
  }'
```

The login page already has these credentials pre-filled with an "auto-fill" button — visitors can log in instantly.

---

## Final Architecture

```
Visitor → Vercel (React frontend) → Railway (FastAPI) → MongoDB Atlas
                                          ↓
                                    Gemini AI API
                                    (explanations + chat)
```

---

## Run Locally (after deployment)

To run locally pointing at the cloud backend:
```bash
cd frontend
echo "VITE_API_URL=https://YOUR-RAILWAY-URL" > .env
npm install && npm run dev
```

Or run everything locally:
```bash
# Terminal 1 — Backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
# Opens at http://localhost:3000
```
