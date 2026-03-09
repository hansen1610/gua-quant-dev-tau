"""
╔══════════════════════════════════════════════════════════════╗
║  Fibonacci Pullback Strategy                                 ║
║  Identifies swing highs/lows and trades the 0.618 golden zone║
╚══════════════════════════════════════════════════════════════╝
"""
import pandas as pd
from typing import List
from strategies.base_strategy import BaseStrategy
import structlog

logger = structlog.get_logger()

class FibonacciPullbackStrategy(BaseStrategy):
    def __init__(self, config: dict):
        super().__init__(config)
        params = config.get("parameters", {})
        if isinstance(params, str):
            import orjson
            params = orjson.loads(params)
            
        self.swing_lookback = params.get("swing_lookback", 50)
        self.fib_level = params.get("fib_level", 0.618)
        self.tolerance = params.get("tolerance", 0.002) # 0.2% tolerance zone

    async def evaluate(self) -> List[dict]:
        signals = []
        for symbol in self.symbols:
            try:
                signal = await self._evaluate_symbol(symbol)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error("fib_pullback.eval_error", symbol=symbol, error=str(e))
        return signals

    async def _evaluate_symbol(self, symbol: str) -> dict | None:
        if not self.candles[symbol].get("15m"):
            return None

        df = pd.DataFrame(self.candles[symbol]["15m"])
        if len(df) < self.swing_lookback:
            return None

        # Find recent swing high and low
        recent_df = df.iloc[-self.swing_lookback:]
        swing_high = recent_df['high'].max()
        swing_low = recent_df['low'].min()
        
        # Determine current trend direction using simple EMA
        ema_50 = self.calc_ema(df['close'], 50).iloc[-1]
        current_price = df['close'].iloc[-1]
        
        trend = "bullish" if current_price > ema_50 else "bearish"
        
        action = None
        stop_loss = 0
        take_profit = 0
        
        if trend == "bullish":
            # Retracement from high to low
            fib_price = swing_high - ((swing_high - swing_low) * self.fib_level)
            zone_upper = fib_price * (1 + self.tolerance)
            zone_lower = fib_price * (1 - self.tolerance)
            
            # Make sure price recently hit swing high (validating the swing)
            high_idx = recent_df['high'].idxmax()
            if high_idx < len(df) - 5: # high was at least 5 candles ago
                if zone_lower <= current_price <= zone_upper:
                    action = "buy"
                    stop_loss = swing_low * 0.998 # Just below swing low
                    take_profit = swing_high # Target the swing high
                    
        else: # bearish
            # Retracement from low to high
            fib_price = swing_low + ((swing_high - swing_low) * self.fib_level)
            zone_upper = fib_price * (1 + self.tolerance)
            zone_lower = fib_price * (1 - self.tolerance)
            
            low_idx = recent_df['low'].idxmin()
            if low_idx < len(df) - 5: # low was at least 5 candles ago
                if zone_lower <= current_price <= zone_upper:
                    action = "sell"
                    stop_loss = swing_high * 1.002 # Just above swing high
                    take_profit = swing_low # Target the swing low
        
        if action:
            return self.create_signal(
                symbol=symbol,
                action=action,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    "swing_high": swing_high,
                    "swing_low": swing_low,
                    "fib_price": fib_price
                }
            )
            
        return None
