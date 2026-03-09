# Strategy Precision Analysis

This document outlines the precision parameters and logic for 4 core quantitative trading strategies to be seeded into QuantBot.

## 1. EMA Trend Cluster
**Logic**: Identifies and follows strong momentum trends.
- **Fast EMA**: 21
- **Slow EMA**: 90 (Institutional standard for medium-term)
- **Signal**: Entry when Price > EMA21 AND EMA21 > EMA90.
- **Precision Guard**: Volume must be above 20-period average on the signal candle.

## 2. Fibonacci Pullback Cluster
**Logic**: High-probability entries during trend corrections.
- **Primary Levels**: 0.382, 0.5, 0.618
- **Golden Ratio Focus**: 0.618 (The most critical level for institutional bounces)
- **Stop Loss**: 0.786 (If price breaks this, the thesis is invalidated)
- **Precision Guard**: Bullish/Bearish engulfing candle pattern must form at the level.

## 3. Multi-Timeframe (MTF) Cluster
**Logic**: Triple barrier trend alignment.
- **HTF (Higher Timeframe)**: 1 Hour (Determines structural direction)
- **LTF (Lower Timeframe)**: 15 Minute (Determines entry precision)
- **Alignment**: Long only if both HTF and LTF show bullish structure.

## 4. Regime Detection Cluster
**Logic**: Adapt strategy to market conditions (Trending vs Ranging).
- **Trend Detection**: ADX > 25 (Active Trend Stage)
- **Volatility Sizing**: Adjusted via ATR (Average True Range).
- **Precision Guard**: Auto-switches to Mean Reversion logic if ADX < 20.
