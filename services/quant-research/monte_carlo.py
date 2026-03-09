"""
╔══════════════════════════════════════════════════════════════╗
║  Quant Research Lab - Monte Carlo Simulation                 ║
║  10,000 randomized simulations to test robustness            ║
╚══════════════════════════════════════════════════════════════╝
"""
import numpy as np
import pandas as pd
from typing import Dict, Any

class MonteCarloSimulator:
    def __init__(self, num_simulations: int = 10000):
        self.num_simulations = num_simulations

    def run_simulation(self, trade_returns: pd.Series, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """
        Runs Monte Carlo simulation by randomly sampling historical trade returns
        with replacement.
        """
        if len(trade_returns) < 10:
            return {"error": "Not enough trade history for Monte Carlo"}
            
        n_trades = len(trade_returns)
        
        # Create simulation matrix (num_simulations x n_trades)
        # Randomly sample returns with replacement
        sim_returns = np.random.choice(trade_returns.values, size=(self.num_simulations, n_trades), replace=True)
        
        # Calculate equity paths for all simulations
        # +1 to returns, then cumulative product, then multiply by initial capital
        sim_equity_paths = initial_capital * np.cumprod(1 + sim_returns, axis=1)
        
        # Calculate final equities
        final_equities = sim_equity_paths[:, -1]
        
        # Calculate drawdowns for all paths
        running_max = np.maximum.accumulate(sim_equity_paths, axis=1)
        drawdowns = (sim_equity_paths - running_max) / running_max
        max_drawdowns = np.min(drawdowns, axis=1)
        
        # Metrics
        confidence_intervals = np.percentile(final_equities, [1, 5, 25, 50, 75, 95, 99])
        worst_case_dd = np.percentile(max_drawdowns, 1) # 99% confident drawdown won't exceed this
        risk_of_ruin = np.mean(max_drawdowns < -0.50) # Probability of losing 50%
        prob_profit = np.mean(final_equities > initial_capital)
        
        return {
            "num_simulations": self.num_simulations,
            "median_final_capital": float(np.median(final_equities)),
            "5th_percentile_capital": float(confidence_intervals[1]),
            "95th_percentile_capital": float(confidence_intervals[5]),
            "worst_case_drawdown_99pct": float(worst_case_dd),
            "risk_of_ruin_50pct": float(risk_of_ruin),
            "probability_of_profit": float(prob_profit)
        }
