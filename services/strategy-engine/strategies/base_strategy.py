"""
╔══════════════════════════════════════════════════════════════╗
║  Base Strategy Class                                         ║
║  Defines the standard interface for all quantified strategies║
╚══════════════════════════════════════════════════════════════╝
"""
from typing import Dict, List, Optional
import asyncio
import pandas as pd
import numpy as np

class BaseStrategy:
    def __init__(self, config: dict):
        self.strategy_id = config.get("id")
        self.name = config.get("name")
        self.type = config.get("type", "unknown")
        
        # Risk settings
        self.risk_per_trade = float(config.get("risk_per_trade", 0.02))
        self.max_daily_drawdown = float(config.get("max_daily_drawdown", 0.05))
        self.max_exposure = float(config.get("max_exposure", 0.30))
        
        # State
        # Parameters (handle potential stringified JSON)
        params = config.get("parameters", {})
        if isinstance(params, str):
            import orjson
            params = orjson.loads(params)
        
        self.symbols = params.get("symbols", ["BTC-USD"])
        self.timeframes = params.get("timeframes", ["15m", "1h"])
        self.active_positions = {}
        
        # Data buffering
        self.market_data = {symbol: {} for symbol in self.symbols}
        self.candles = {symbol: {tf: [] for tf in self.timeframes} for symbol in self.symbols}

    async def on_tick(self, tick_data: dict):
        """Handle real-time tick/orderbook updates"""
        symbol = tick_data.get("symbol")
        if symbol in self.symbols:
            self.market_data[symbol] = tick_data

    async def update_candles(self, symbol: str, timeframe: str, new_candles: List[dict]):
        """Update historical/live candles"""
        if symbol in self.candles and timeframe in self.candles[symbol]:
            # Simple append (in real impl, we'd handle overlap/merging)
            self.candles[symbol][timeframe].extend(new_candles)
            # Keep array size manageable
            max_candles = 1000
            if len(self.candles[symbol][timeframe]) > max_candles:
                self.candles[symbol][timeframe] = self.candles[symbol][timeframe][-max_candles:]

    async def evaluate(self) -> List[dict]:
        """
        Main evaluation loop. To be overridden by specific strategies.
        Returns a list of signal dictionaries.
        """
        raise NotImplementedError("Strategies must implement the evaluate() method")

    def create_signal(self, symbol: str, action: str, price: float, stop_loss: float, take_profit: float, metadata: dict = None) -> dict:
        """Helper to format a standard signal object"""
        return {
            "strategy_id": str(self.strategy_id),
            "strategy_name": self.name,
            "symbol": symbol,
            "action": action, # 'buy', 'sell', 'close'
            "price": price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "metadata": metadata or {}
        }

    # ── Shared Common Indicators ─────────────────────────────────────────

    def calc_ema(self, series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    def calc_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()

    def calc_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
