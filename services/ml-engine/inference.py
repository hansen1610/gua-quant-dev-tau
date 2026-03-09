"""
╔══════════════════════════════════════════════════════════════╗
║  Machine Learning Engine - Inference Engine                  ║
║  Provides real-time probabilities for signal success         ║
╚══════════════════════════════════════════════════════════════╝
"""
import joblib
import pandas as pd
import structlog
import os
import asyncpg
from typing import Dict, Any

logger = structlog.get_logger()

class MetaFilterInference:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.models = {}  # In-memory cache
        self.model_dir = "/app/models"

    async def load_active_models(self):
        """Loads all active models from DB into memory."""
        try:
            async with self.db_pool.acquire() as conn:
                records = await conn.fetch("SELECT id, name, file_path FROM ml_models WHERE is_active = true")
                
                for r in records:
                    if os.path.exists(r['file_path']):
                        self.models[r['id']] = joblib.load(r['file_path'])
                        logger.info("ml.model_loaded", name=r['name'])
                    else:
                        logger.warning("ml.model_file_missing", path=r['file_path'])
        except Exception as e:
            logger.error("ml.model_load_error", error=str(e))

    async def predict_signal_quality(self, model_id: str, features: Dict[str, Any]) -> float:
        """
        Given a set of features for a new trade signal, returns the probability
        that the trade will be profitable.
        """
        if model_id not in self.models:
            # Fallback if model not loaded
            await self.load_active_models()
            if model_id not in self.models:
                logger.warning("ml.model_not_found", model_id=model_id)
                return 0.5 # Neutral fallback

        model = self.models[model_id]
        
        # Structure features exactly as trained
        # Features: ['hour', 'rsi_at_entry', 'atr_ratio']
        df = pd.DataFrame([{
            'hour': features.get('hour', 12),
            'rsi_at_entry': features.get('rsi_at_entry', 50),
            'atr_ratio': features.get('atr_ratio', 1.0)
        }])
        
        # model.predict_proba returns [[P(class 0), P(class 1)]]
        prob_profitable = model.predict_proba(df)[0][1]
        
        return float(prob_profitable)
