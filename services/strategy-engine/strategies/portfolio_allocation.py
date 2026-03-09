"""
╔══════════════════════════════════════════════════════════════╗
║  Portfolio Allocation Strategy                               ║
║  Dynamically allocates capital across uncorrelated assets    ║
╚══════════════════════════════════════════════════════════════╝
"""
import pandas as pd
import numpy as np
from typing import List
from strategies.base_strategy import BaseStrategy

class PortfolioAllocationStrategy(BaseStrategy):
    def __init__(self, config: dict):
        super().__init__(config)
        self.lookback = 30
        self.rebalance_threshold = 0.05 # 5% drift from target

    def calculate_correlation(self, returns_df: pd.DataFrame) -> pd.DataFrame:
        return returns_df.corr()

    def get_inverse_volatility_weights(self, returns_df: pd.DataFrame) -> pd.Series:
        # Calculate annualized volatility
        volatilities = returns_df.std() * np.sqrt(365) # Assuming daily returns for crypto
        
        # Inverse volatility
        inv_vol = 1.0 / volatilities
        
        # Normalize weights
        weights = inv_vol / inv_vol.sum()
        return weights

    async def evaluate(self) -> List[dict]:
        signals = []
        
        # We need data for all symbols to do portfolio math
        returns_dict = {}
        for symbol in self.symbols:
            if "1d" not in self.candles[symbol]:
                return []
            df = pd.DataFrame(self.candles[symbol]["1d"])
            if len(df) < self.lookback:
                return []
            returns_dict[symbol] = df['close'].pct_change().dropna()
            
        returns_df = pd.DataFrame(returns_dict)
        
        # Target weights based on inverse volatility (Risk Parity approach)
        target_weights = self.get_inverse_volatility_weights(returns_df)
        
        # In a full logic we'd compare target_weights against current active_positions
        # and generate buy/sell signals to close the drift if it exceeds self.rebalance_threshold
        # Here we mock the generation for the architecture flow
        for symbol, target_weight in target_weights.items():
            current_weight = 0.0 # Mock: fetch from risk engine/account
            
            if target_weight - current_weight > self.rebalance_threshold:
                 signals.append(self.create_signal(
                     symbol=symbol,
                     action="buy",
                     price=self.candles[symbol]["1d"][-1]["close"],
                     stop_loss=0, # Handled by portfolio risk, not individual stops
                     take_profit=0,
                     metadata={"target_weight": float(target_weight), "current_weight": current_weight}
                 ))
            elif current_weight - target_weight > self.rebalance_threshold:
                 signals.append(self.create_signal(
                     symbol=symbol,
                     action="sell",
                     price=self.candles[symbol]["1d"][-1]["close"],
                     stop_loss=0,
                     take_profit=0,
                     metadata={"target_weight": float(target_weight), "current_weight": current_weight}
                 ))
                 
        return signals
