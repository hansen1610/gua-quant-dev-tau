"""
╔══════════════════════════════════════════════════════════════╗
║  EMA Trend Alignment Strategy                                ║
║  Confluence of 21/34/90 EMA on multiple timeframes           ║
╚══════════════════════════════════════════════════════════════╝
"""
import pandas as pd
from typing import List
from strategies.base_strategy import BaseStrategy
import structlog

logger = structlog.get_logger()

class EMATrendStrategy(BaseStrategy):
    def __init__(self, config: dict):
        super().__init__(config)
        # Parameters already handled in BaseStrategy, but local access is fine
        params = config.get("parameters", {})
        if isinstance(params, str):
            import orjson
            params = orjson.loads(params)
            
        self.ema_fast = params.get("ema_fast", 21)
        self.ema_medium = params.get("ema_medium", 34)
        self.ema_slow = params.get("ema_slow", 90)
        self.atr_period = params.get("atr_period", 14)

    async def evaluate(self) -> List[dict]:
        signals = []
        for symbol in self.symbols:
            try:
                signal = await self._evaluate_symbol(symbol)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error("ema_trend.eval_error", symbol=symbol, error=str(e))
        return signals

    async def _evaluate_symbol(self, symbol: str) -> dict | None:
        # Require both 1h and 15m timeframes
        if not self.candles[symbol].get("1h") or not self.candles[symbol].get("15m"):
            return None

        df_1h = pd.DataFrame(self.candles[symbol]["1h"])
        df_15m = pd.DataFrame(self.candles[symbol]["15m"])

        if len(df_1h) < self.ema_slow or len(df_15m) < self.ema_slow:
            return None

        # 1. Macro Trend (1h)
        closes_1h = df_1h['close']
        ema_slow_1h = self.calc_ema(closes_1h, self.ema_slow).iloc[-1]
        current_price_1h = closes_1h.iloc[-1]

        macro_trend = "bullish" if current_price_1h > ema_slow_1h else "bearish"

        # 2. Micro Alignment (15m)
        closes_15m = df_15m['close']
        fast_15m = self.calc_ema(closes_15m, self.ema_fast).iloc[-1]
        med_15m = self.calc_ema(closes_15m, self.ema_medium).iloc[-1]
        slow_15m = self.calc_ema(closes_15m, self.ema_slow).iloc[-1]

        current_price = closes_15m.iloc[-1]
        atr = self.calc_atr(df_15m, self.atr_period).iloc[-1]

        # 3. Validation Rules
        is_bullish_alignment = (fast_15m > med_15m > slow_15m) and (current_price > fast_15m)
        is_bearish_alignment = (fast_15m < med_15m < slow_15m) and (current_price < fast_15m)

        action = None
        if macro_trend == "bullish" and is_bullish_alignment:
            # Look for pullback to fast EMA
            if current_price <= (fast_15m + (atr * 0.1)):
                action = "buy"
        elif macro_trend == "bearish" and is_bearish_alignment:
            if current_price >= (fast_15m - (atr * 0.1)):
                action = "sell"

        if action:
            # Calculate dynamic Risk via ATR
            sl_distance = atr * 1.5
            stop_loss = current_price - sl_distance if action == "buy" else current_price + sl_distance
            
            # Target 1:2 Risk/Reward
            take_profit = current_price + (sl_distance * 2) if action == "buy" else current_price - (sl_distance * 2)

            return self.create_signal(
                symbol=symbol,
                action=action,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    "macro_trend": macro_trend,
                    "ema_fast": fast_15m,
                    "ema_slow": slow_15m,
                    "atr": atr
                }
            )
            
        return None
