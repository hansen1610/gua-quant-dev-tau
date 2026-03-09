"""
╔══════════════════════════════════════════════════════════════╗
║  Quant Research Lab - Walk Forward Analysis                  ║
║  Validates strategy robustness over rolling time windows     ║
╚══════════════════════════════════════════════════════════════╝
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import structlog

logger = structlog.get_logger()

class WalkForwardAnalyzer:
    def __init__(self, train_window_days: int = 180, test_window_days: int = 30):
        self.train_window = train_window_days
        self.test_window = test_window_days

    def split_data(self, df: pd.DataFrame) -> List[Dict[str, pd.DataFrame]]:
        """Split data into rolling Train/Test sets based on time windows"""
        df = df.sort_index()
        start = df.index.min()
        end = df.index.max()
        
        splits = []
        current_train_end = start + pd.Timedelta(days=self.train_window)
        
        while current_train_end + pd.Timedelta(days=self.test_window) <= end:
            train_start = current_train_end - pd.Timedelta(days=self.train_window)
            test_end = current_train_end + pd.Timedelta(days=self.test_window)
            
            train_mask = (df.index >= train_start) & (df.index < current_train_end)
            test_mask = (df.index >= current_train_end) & (df.index < test_end)
            
            splits.append({
                "train": df.loc[train_mask].copy(),
                "test": df.loc[test_mask].copy(),
                "test_period": (current_train_end.strftime('%Y-%m-%d'), test_end.strftime('%Y-%m-%d'))
            })
            
            current_train_end += pd.Timedelta(days=self.test_window)
            
        return splits

    def calculate_wfa_efficiency(self, train_metrics: List[dict], test_metrics: List[dict]) -> float:
        """Calculate Walk-Forward Efficiency (WFE) = Annualized Test Return / Annualized Train Return"""
        train_returns = np.array([m.get("annualized_return", 0) for m in train_metrics])
        test_returns = np.array([m.get("annualized_return", 0) for m in test_metrics])
        
        mean_train = np.mean(train_returns)
        mean_test = np.mean(test_returns)
        
        if mean_train <= 0:
            return 0.0
            
        wfe = mean_test / mean_train
        logger.info("wfa.efficiency_calculated", wfe=float(wfe))
        return float(wfe)
