"""
╔══════════════════════════════════════════════════════════════╗
║  Regime Detection Strategy                                   ║
║  Identifies Ranging vs Trending environments using ADX       ║
╚══════════════════════════════════════════════════════════════╝
"""
import pandas as pd
import numpy as np
from typing import List
from strategies.base_strategy import BaseStrategy

class RegimeDetectionStrategy(BaseStrategy):
    def __init__(self, config: dict):
        super().__init__(config)
        self.adx_period = 14
        self.trend_threshold = 25

    def calc_adx(self, df: pd.DataFrame, period: int) -> pd.Series:
        # Simplified ADX calculation approximation for demonstration
        atr = self.calc_atr(df, period)
        up_move = df['high'] - df['high'].shift(1)
        down_move = df['low'].shift(1) - df['low']
        
        pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        pos_dm_ser = pd.Series(pos_dm).ewm(alpha=1/period).mean()
        neg_dm_ser = pd.Series(neg_dm).ewm(alpha=1/period).mean()
        
        di_plus = 100 * (pos_dm_ser / atr)
        di_minus = 100 * (neg_dm_ser / atr)
        
        dx = 100 * np.abs(di_plus - di_minus) / (di_plus + di_minus).replace(0, 1)
        adx = dx.ewm(alpha=1/period).mean()
        return adx

    async def evaluate(self) -> List[dict]:
        signals = []
        for symbol in self.symbols:
            if "1h" not in self.candles[symbol]:
                continue
                
            df = pd.DataFrame(self.candles[symbol]["1h"])
            if len(df) < self.adx_period + 10:
                continue
                
            adx = self.calc_adx(df, self.adx_period).iloc[-1]
            price = df['close'].iloc[-1]
            atr = self.calc_atr(df).iloc[-1]
            
            # Action only when crossing into strong trend
            if adx > self.trend_threshold and self.calc_adx(df, self.adx_period).iloc[-2] <= self.trend_threshold:
                # Determine direction via simple MA crossover
                ma_fast = self.calc_ema(df['close'], 10).iloc[-1]
                ma_slow = self.calc_ema(df['close'], 30).iloc[-1]
                
                action = "buy" if ma_fast > ma_slow else "sell"
                
                signals.append(self.create_signal(
                    symbol=symbol,
                    action=action,
                    price=price,
                    stop_loss=price - (atr * 2) if action == "buy" else price + (atr * 2),
                    take_profit=price + (atr * 3) if action == "buy" else price - (atr * 3),
                    metadata={"regime": "trending", "adx": float(adx)}
                ))
        return signals
