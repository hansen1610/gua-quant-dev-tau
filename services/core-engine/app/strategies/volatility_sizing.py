"""
╔══════════════════════════════════════════════════════════════╗
║  Volatility Breakout (ATR Sizing) Strategy                   ║
║  Trades breakouts scaling position inversely to volatility   ║
╚══════════════════════════════════════════════════════════════╝
"""
import pandas as pd
from typing import List
from app.strategies.base_strategy import BaseStrategy

class VolatilityBreakoutStrategy(BaseStrategy):
    def __init__(self, config: dict):
        super().__init__(config)
        self.lookback = 20
        self.atr_multiplier = 2.0

    async def evaluate(self) -> List[dict]:
        signals = []
        for symbol in self.symbols:
            if "1h" not in self.candles[symbol]:
                continue
                
            df = pd.DataFrame(self.candles[symbol]["1h"])
            if len(df) < self.lookback:
                continue
                
            recent_high = df['high'].iloc[-self.lookback:-1].max()
            recent_low = df['low'].iloc[-self.lookback:-1].min()
            price = df['close'].iloc[-1]
            atr = self.calc_atr(df).iloc[-1]
            
            action = None
            if price > recent_high + (atr * 0.1):
                action = "buy"
            elif price < recent_low - (atr * 0.1):
                action = "sell"
                
            if action:
                signals.append(self.create_signal(
                    symbol=symbol,
                    action=action,
                    price=price,
                    stop_loss=price - (atr * self.atr_multiplier) if action == "buy" else price + (atr * self.atr_multiplier),
                    take_profit=price + (atr * self.atr_multiplier * 3) if action == "buy" else price - (atr * self.atr_multiplier * 3),
                    metadata={"volatility_target": float(atr / price)}
                ))
        return signals
