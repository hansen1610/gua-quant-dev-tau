"""
╔══════════════════════════════════════════════════════════════╗
║  Quant Research Lab - Backtesting Engine                     ║
║  Vectorized backtesting with slippage and funding simulation ║
╚══════════════════════════════════════════════════════════════╝
"""
import pandas as pd
import numpy as np
import decimal
import json
import structlog
from typing import Dict, Any

logger = structlog.get_logger()

class VectorizedBacktester:
    def __init__(self, initial_capital: float = 10000.0, commission_pct: float = 0.0005, slippage_pct: float = 0.0005):
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        
    def run_backtest(self, df: pd.DataFrame, signals: pd.Series, take_profits: pd.Series, stop_losses: pd.Series) -> Dict[str, Any]:
        """
        Calculates PnL vectorized.
        Signals: 1 for Buy, -1 for Sell
        """
        logger.info("backtester.running_vector", length=len(df))
        
        # Track positions
        # This is a simplified vectorized logic for demonstration
        positions = signals.ffill() 
        daily_returns = df['close'].pct_change() * positions.shift(1)
        
        # Apply costs for trades
        trades_mask = signals.diff().ne(0) & signals.notna()
        transaction_costs = trades_mask.astype(int) * (self.commission_pct + self.slippage_pct)
        
        net_returns = daily_returns - transaction_costs
        
        # Create equity curve
        equity_curve = (1 + net_returns).cumprod() * self.initial_capital
        
        # Calculate metrics
        total_return = (equity_curve.iloc[-1] / self.initial_capital) - 1 if len(equity_curve)>0 else 0
        drawdown = (equity_curve / equity_curve.cummax()) - 1
        max_drawdown = drawdown.min()
        
        annualization_factor = 365 * 24 # assuming hourly data
        volatility = net_returns.std() * np.sqrt(annualization_factor)
        sharpe = (net_returns.mean() * annualization_factor) / volatility if volatility > 0 else 0
        
        # Simulated trades counting
        total_trades = trades_mask.sum()
        win_mask = net_returns > 0
        win_rate = win_mask.sum() / total_trades if total_trades > 0 else 0
        
        # Profit factor
        gross_profit = net_returns[net_returns > 0].sum()
        gross_loss = abs(net_returns[net_returns < 0].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            "initial_capital": self.initial_capital,
            "final_capital": float(equity_curve.iloc[-1]) if len(equity_curve)>0 else self.initial_capital,
            "total_return": float(total_return),
            "max_drawdown": float(max_drawdown),
            "sharpe_ratio": float(sharpe),
            "win_rate": float(win_rate),
            "profit_factor": float(profit_factor),
            "total_trades": int(total_trades)
        }
