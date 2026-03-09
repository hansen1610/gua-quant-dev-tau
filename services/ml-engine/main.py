from fastapi import FastAPI, Request, HTTPException
import uvicorn
import structlog
import asyncpg
import os
from contextlib import asynccontextmanager
from inference import MetaFilterInference
from training import MetaFilterTrainer

logger = structlog.get_logger()

db_pool = None
inference_engine = None
trainer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool, inference_engine, trainer
    
    db_pool = await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "quantbot"),
        user=os.getenv("POSTGRES_USER", "quantbot_user"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        min_size=1,
        max_size=5
    )
    
    inference_engine = MetaFilterInference(db_pool)
    await inference_engine.load_active_models()
    
    trainer = MetaFilterTrainer(db_pool)
    
    yield
    
    if db_pool:
        await db_pool.close()

app = FastAPI(title="ML Engine API", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok", "models_loaded": len(inference_engine.models) if inference_engine else 0}

@app.post("/train/{strategy_id}/{symbol}")
async def trigger_training(strategy_id: str, symbol: str):
    """Trigger background training for a strategy on a specific symbol."""
    if not trainer:
        raise HTTPException(status_code=500, detail="Trainer not initialized")
    
    # In a real system, use BackgroundTasks. For now, await directly.
    result = await trainer.train_model(strategy_id, symbol)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
        
    # Reload active models after new one was trained
    await inference_engine.load_active_models()
    return result

@app.post("/predict/{model_id}")
async def predict_trade_success(model_id: str, payload: dict):
    """
    Get probability score for a trade signal.
    Payload: {"features": {"hour": 14, "rsi_at_entry": 45, "atr_ratio": 1.2}}
    """
    if not inference_engine:
         raise HTTPException(status_code=500, detail="Inference engine not ready")
         
    features = payload.get("features", {})
    prob = await inference_engine.predict_signal_quality(model_id, features)
    
    return {
        "model_id": model_id,
        "probability_success": prob,
        "is_approved": prob > 0.55  # Requires 55% statistical edge
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
