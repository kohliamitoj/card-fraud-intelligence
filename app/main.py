import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongodb import connect_db, close_db
from app.core.fraud_detector import load_model
from app.core.ai_assistant import init_gemini
from app.api.v1.router import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    load_model()
    init_gemini()
    logger.info("Card Fraud Intelligence API started.")
    yield
    await close_db()
    logger.info("API shutdown complete.")


app = FastAPI(
    title="Card Fraud Intelligence API",
    description=(
        "Real-time card transaction fraud detection powered by XGBoost + SHAP + Gemini AI. "
        "Scores transactions, creates investigation cases, and provides an AI-driven analyst assistant."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "card-fraud-intelligence"}
