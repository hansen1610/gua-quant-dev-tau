"""
╔══════════════════════════════════════════════════════════════╗
║  Multi-Timeframe Confluence Strategy                         ║
║  Requires alignment across 4h, 1h, and 15m timeframes        ║
╚══════════════════════════════════════════════════════════════╝
"""
from typing import List
import pandas as pd
from app.strategies.base_strategy import BaseStrategy

class MultiTimeframeStrategy(BaseStrategy):
    def __init__(self, config: dict):
        super().__init__(config)
        self.ma_period = 50

    async def evaluate(self) -> List[dict]:
        signals = []
        for symbol in self.symbols:
            if not all(tf in self.candles[symbol] for tf in ["4h", "1h", "15m"]):
                continue
                
            df_4h = pd.DataFrame(self.candles[symbol]["4h"])
            df_1h = pd.DataFrame(self.candles[symbol]["1h"])
            df_15m = pd.DataFrame(self.candles[symbol]["15m"])
            
            if len(df_4h) < self.ma_period or len(df_15m) < self.ma_period:
                continue
                
            ma_4h = self.calc_ema(df_4h['close'], self.ma_period).iloc[-1]
            ma_1h = self.calc_ema(df_1h['close'], self.ma_period).iloc[-1]
            ma_15m = self.calc_ema(df_15m['close'], self.ma_period).iloc[-1]
            
            price = df_15m['close'].iloc[-1]
            atr = self.calc_atr(df_15m).iloc[-1]
            
            trend_4h = price > ma_4h
            trend_1h = price > ma_1h
            trend_15m = price > ma_15m
            
            action = None
            if trend_4h and trend_1h and trend_15m:
                action = "buy"
            elif not trend_4h and not trend_1h and not trend_15m:
                action = "sell"
                
            if action:
                signals.append(self.create_signal(
                    symbol=symbol,
                    action=action,
                    price=price,
                    stop_loss=price - (atr * 2) if action == "buy" else price + (atr * 2),
                    take_profit=price + (atr * 4) if action == "buy" else price - (atr * 4)
                ))
        return signals
