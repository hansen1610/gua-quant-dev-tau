"""
╔══════════════════════════════════════════════════════════════╗
║  Machine Learning Engine - Training Pipeline                 ║
║  Trains Random Forest meta-filter to predict signal quality  ║
╚══════════════════════════════════════════════════════════════╝
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
import structlog
import uuid
import asyncpg

logger = structlog.get_logger()

class MetaFilterTrainer:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.model_dir = "/app/models"
        os.makedirs(self.model_dir, exist_ok=True)

    async def extract_features(self, trades_df: pd.DataFrame, candles_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts features (Volatility, Trend length, RSI at entry, Time of day).
        Target = 1 if trade was profitable (PnL > 0), else 0
        """
        logger.info("ml.extracting_features", trades=len(trades_df))
        
        # Simplified feature extraction
        df = trades_df.copy()
        df['target'] = (df['pnl_pct'] > 0).astype(int)
        
        # Feature: Hour of day
        df['hour'] = pd.to_datetime(df['executed_at']).dt.hour
        
        # In a real impl, we would join the candles_df on executed_at to get:
        # - ATR at entry
        # - RSI at entry
        # - Distance from MA
        # For this prototype we assume these are passed in trade metadata
        df['rsi_at_entry'] = df['metadata'].apply(lambda x: x.get('rsi', 50) if isinstance(x, dict) else 50)
        df['atr_ratio'] = df['metadata'].apply(lambda x: x.get('atr_ratio', 1.0) if isinstance(x, dict) else 1.0)
        
        # Drop NaNs
        features = ['hour', 'rsi_at_entry', 'atr_ratio']
        df = df.dropna(subset=features + ['target'])
        
        return df[['id', 'target'] + features]

    async def train_model(self, strategy_id: str, symbol: str) -> dict:
        """Fetch historical trades, extract features, train RF model, save to disk and DB."""
        try:
            async with self.db_pool.acquire() as conn:
                # Fetch trades
                trades_query = """
                    SELECT id, executed_at, pnl_pct, metadata 
                    FROM trades 
                    WHERE strategy_id = $1 AND asset_id = (SELECT id FROM assets WHERE symbol = $2)
                    ORDER BY executed_at ASC
                """
                trades_records = await conn.fetch(trades_query, strategy_id, symbol)
                
                if len(trades_records) < 100:
                    return {"success": False, "error": "Insufficient trades for training"}

            trades_df = pd.DataFrame([dict(r) for r in trades_records])
            
            # Prepare data
            data = await self.extract_features(trades_df, pd.DataFrame())
            
            X = data.drop(columns=['id', 'target'])
            y = data['target']

            # Time Series Cross Validation
            tscv = TimeSeriesSplit(n_splits=5)
            model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
            
            scores = []
            for train_index, test_index in tscv.split(X):
                X_train, X_test = X.iloc[train_index], X.iloc[test_index]
                y_train, y_test = y.iloc[train_index], y.iloc[test_index]
                
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                scores.append(accuracy_score(y_test, preds))

            # Train final model on all data
            model.fit(X, y)
            
            # Save Model
            model_id = str(uuid.uuid4())
            file_path = os.path.join(self.model_dir, f"rf_meta_{model_id}.pkl")
            joblib.dump(model, file_path)

            metrics = {
                "cv_accuracy_mean": float(np.mean(scores)),
                "cv_accuracy_std": float(np.std(scores)),
                "n_samples": len(X)
            }
            
            # Log to Database
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO ml_models (id, name, model_type, accuracy, training_metrics, file_path, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    model_id, f"MetaFilter_{symbol}_{strategy_id}", "RandomForest", 
                    metrics["cv_accuracy_mean"], str(metrics), file_path, True
                )

            logger.info("ml.model_trained", model_id=model_id, accuracy=metrics["cv_accuracy_mean"])
            return {"success": True, "model_id": model_id, "metrics": metrics}

        except Exception as e:
            logger.error("ml.training_failed", error=str(e))
            return {"success": False, "error": str(e)}
