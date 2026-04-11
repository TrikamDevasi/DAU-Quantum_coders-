from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from recommender import recommender as content_rec
from gru_model import session_recommender
from eval import evaluate_recommendations
from database import get_db
import os
import joblib

lr_pricing_scaler = None
if os.path.exists("lr_pricing_model.pkl"):
    model_obj = joblib.load("lr_pricing_model.pkl")
    # If using dictionary-based saved model
    if isinstance(model_obj, dict):
        lr_pricing_model = model_obj['model']
        lr_pricing_scaler = model_obj.get('scaler')
    else:
        lr_pricing_model = model_obj

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Training content recommender...")
    content_rec.train()
    print("Training GRU4Rec session model...")
    session_recommender.train(epochs=5)
    print("ML service ready.")
    yield

app = FastAPI(title="PriceIQ ML Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class SessionRequest(BaseModel):
    session_history: list[str]
    top_k: int = 5

@app.get("/health")
def health():
    return {"status": "ok", "content_rec_trained": content_rec.trained, "gru_trained": session_recommender.trained}

@app.get("/recommend/{product_id}")
def recommend_by_product(product_id: str, top_k: int = 5):
    recs = content_rec.recommend(product_id, top_k)
    return {"product_id": product_id, "recommendations": recs, "model": "tfidf-content"}

@app.post("/recommend/session")
def recommend_by_session(req: SessionRequest):
    recs = session_recommender.recommend(req.session_history, req.top_k)
    if not recs:
        # fallback to content-based on last viewed
        if req.session_history:
            recs = content_rec.recommend(req.session_history[-1], req.top_k)
    return {"recommendations": recs, "model": "gru4rec" if session_recommender.trained else "tfidf-fallback"}

@app.get("/price-predict")
def price_predict(product_id: str, demand_score: float = 0, stock: int = 100, user_segment: str = "standard"):
    if lr_pricing_model is not None:
        # Approximate values for missing payload
        willingness = 1.0
        if user_segment == "value_seeker":
            willingness = 0.8
        elif user_segment == "premium_buyer":
            willingness = 1.2
            
        competitor_ratio = 1.0 # default ratio
        
        # Ensure demand_score is clamped cleanly between 0 and 1
        clamped_demand = max(0.0, min(float(demand_score), 1.0))
        
        # We need [demand_score, inventory_count, competitor_ratio, willingness_to_pay_multiplier]
        X_input = [[clamped_demand, stock, competitor_ratio, willingness]]
        
        # Apply scaling if trained with one
        if lr_pricing_scaler is not None:
            X_input = lr_pricing_scaler.transform(X_input)
            
        uplift = float(lr_pricing_model.predict(X_input)[0])
        
        # Clip uplift to sensible bounds to avoid outrageous prices
        uplift = max(-0.25, min(uplift, 0.35))
        reason = "ai_dynamic_pricing"
        confidence = 0.95
        model_name = "linear_regression_v2"
    else:
        # Fallback to rule-based logic
        uplift = 0.0
        reason = "regular_pricing"
        if demand_velocity >= 30:
            uplift += 0.15
            reason = "high_demand"
        elif demand_velocity >= 15:
            uplift += 0.08
            reason = "moderate_demand"
        if stock <= 3:
            uplift += 0.22
            reason = "critical_stock"
        elif stock <= 5:
            uplift += 0.12
            reason = "low_stock"
        if user_segment == "value_seeker":
            uplift = max(0, uplift - 0.03)
        uplift = min(uplift, 0.35)
        confidence = 0.85
        model_name = "rule_based_v1"
        
    return {
        "product_id": product_id,
        "uplift_factor": round(uplift, 4),
        "price_reason": reason,
        "confidence": confidence,
        "model": model_name
    }

@app.get("/evaluate")
def get_evaluation_metrics():
    return evaluate_recommendations()

@app.post("/train")
def train_models():
    print("MAnual training triggered via API...")
    content_rec.train()
    session_recommender.train(epochs=3)
    return {"status": "success", "message": "Models retrained successfully"}
