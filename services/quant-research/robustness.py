"""
╔══════════════════════════════════════════════════════════════╗
║  Quant Research Lab - Robustness Profiler                    ║
║  Tests strategy degradation over synthetic noisy data        ║
╚══════════════════════════════════════════════════════════════╝
"""
import numpy as np
import pandas as pd
from backtester import VectorizedBacktester

class RobustnessProfiler:
    def __init__(self, backtester: VectorizedBacktester):
        self.backtester = backtester

    def add_noise(self, df: pd.DataFrame, noise_level: float = 0.001) -> pd.DataFrame:
        """Adds random walks of noise to OHLC data to test overfitting"""
        noisy_df = df.copy()
        
        for col in ['open', 'high', 'low', 'close']:
            if col in noisy_df.columns:
                noise = np.random.normal(0, noise_level, len(noisy_df))
                noisy_df[col] = noisy_df[col] * (1 + noise)
                
        # Ensure high >= low etc.
        noisy_df['high'] = noisy_df[['open', 'high', 'low', 'close']].max(axis=1)
        noisy_df['low'] = noisy_df[['open', 'high', 'low', 'close']].min(axis=1)
        
        return noisy_df

    def test_parameter_stability(self, df: pd.DataFrame, signals_func, param_range: list) -> dict:
        """
        Tests how sensitive the strategy is to slight parameter changes.
        signals_func: A lambda or function that takes a parameter and returns pd.Series of signals
        """
        results = {}
        for param in param_range:
            signals = signals_func(df, param)
            # Create dummy take_profits and stop_losses for the backtest
            tp = pd.Series(0, index=df.index)
            sl = pd.Series(0, index=df.index)
            
            metrics = self.backtester.run_backtest(df, signals, tp, sl)
            results[param] = metrics.get('sharpe_ratio', 0)
            
        # Calculate stability score (variance of sharpe across parameters)
        sharpes = list(results.values())
        stability = 1 / (np.std(sharpes) + 1e-6) if len(sharpes) > 1 else 0
        
        return {
            "parameter_sharpes": results,
            "stability_score": float(stability),
            "is_robust": stability > 5.0 # Arbitrary threshold for prototype
        }

    def test_noise_degradation(self, df: pd.DataFrame, signals_func, iterations: int = 10) -> dict:
        """Tests how the strategy performs under artificially degraded data"""
        base_signals = signals_func(df)
        base_metrics = self.backtester.run_backtest(df, base_signals, pd.Series(0, index=df.index), pd.Series(0, index=df.index))
        base_return = base_metrics.get('total_return', 0)
        
        noisy_returns = []
        for _ in range(iterations):
            noisy_df = self.add_noise(df, noise_level=0.005) # 0.5% noise
            noisy_signals = signals_func(noisy_df)
            metrics = self.backtester.run_backtest(noisy_df, noisy_signals, pd.Series(0, index=df.index), pd.Series(0, index=df.index))
            noisy_returns.append(metrics.get('total_return', 0))
            
        mean_noisy_return = np.mean(noisy_returns)
        degradation = (base_return - mean_noisy_return) / base_return if base_return > 0 else 1.0
        
        return {
            "base_return": float(base_return),
            "mean_noisy_return": float(mean_noisy_return),
            "degradation_pct": float(degradation * 100),
            "is_robust": degradation < 0.25 # Less than 25% performance drop under noise
        }
