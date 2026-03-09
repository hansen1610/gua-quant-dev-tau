"""
╔══════════════════════════════════════════════════════════════╗
║  Quant Research Lab — Main Service                           ║
║  Backtesting, Monte Carlo, Walk-Forward Analysis             ║
╚══════════════════════════════════════════════════════════════╝
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager

import asyncpg
import redis.asyncio as aioredis
import structlog
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from backtester import VectorizedBacktester
from monte_carlo import MonteCarloSimulator
from robustness import RobustnessProfiler
from walk_forward import WalkForwardAnalyzer

load_dotenv()
logger = structlog.get_logger()

db_pool = None
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool, redis_client
    logger.info("quant_research.starting")

    db_pool = await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "quantbot"),
        user=os.getenv("POSTGRES_USER", "quantbot_user"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        min_size=1,
        max_size=5,
    )

    redis_client = aioredis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD", ""),
        decode_responses=True,
    )

    # Start background job consumer
    consumer_task = asyncio.create_task(_job_consumer_loop())

    yield

    consumer_task.cancel()
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()
    logger.info("quant_research.stopped")


app = FastAPI(title="Quant Research API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "service": "quant-research"}


@app.post("/run_backtest")
async def run_backtest(params: dict):
    """Queue a backtest job for async processing."""
    try:
        await redis_client.lpush("jobs:quant-research:backtest", json.dumps(params))
        return {"status": "queued", "message": "Backtest added to computation queue."}
    except Exception as e:
        logger.error("quant_research.queue_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to queue backtest job")


@app.get("/results/{backtest_id}")
async def get_backtest_result(backtest_id: str):
    """Fetch a completed backtest result by ID."""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not ready")
    try:
        async with db_pool.acquire() as conn:
            record = await conn.fetchrow(
                "SELECT * FROM backtest_results WHERE id = $1", backtest_id
            )
            if not record:
                raise HTTPException(status_code=404, detail="Backtest result not found")
            return dict(record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("quant_research.result_error", error=str(e))
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/results")
async def list_backtest_results(limit: int = 20):
    """List recent backtest results."""
    if not db_pool:
        return {"results": []}
    try:
        async with db_pool.acquire() as conn:
            records = await conn.fetch(
                "SELECT id, strategy_id, asset_symbol, timeframe, total_return, sharpe_ratio, "
                "max_drawdown, win_rate, total_trades, created_at "
                "FROM backtest_results ORDER BY created_at DESC LIMIT $1",
                limit,
            )
            return {"results": [dict(r) for r in records]}
    except Exception as e:
        logger.error("quant_research.list_error", error=str(e))
        return {"results": [], "error": str(e)}


# ── Background Job Consumer ──────────────────────────────
async def _job_consumer_loop():
    """Consume backtest jobs from Redis queue and process them."""
    logger.info("quant_research.job_consumer_started")

    while True:
        try:
            # Blocking pop from Redis queue (timeout 5s)
            job_data = await redis_client.brpop("jobs:quant-research:backtest", timeout=5)

            if job_data:
                _, raw = job_data
                params = json.loads(raw)
                logger.info("quant_research.processing_job", params=params)
                await _process_backtest_job(params)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("quant_research.consumer_error", error=str(e))
            await asyncio.sleep(2)


async def _process_backtest_job(params: dict):
    """Execute a full backtest pipeline: backtest → monte carlo → store results."""
    import pandas as pd
    import numpy as np

    strategy_id = params.get("strategy_id")
    symbol = params.get("symbol", "BTC-USD")
    timeframe = params.get("timeframe", "1h")
    initial_capital = params.get("initial_capital", 10000.0)

    try:
        # Step 1: Generate or fetch historical data
        # In production, candle data comes from Hyperliquid connector or DB
        # For now, generate synthetic data for testing
        np.random.seed(42)
        n = params.get("num_candles", 2000)
        price = 50000.0
        data = []
        for i in range(n):
            change = np.random.normal(0, 0.01)
            o = price
            c = price * (1 + change)
            h = max(o, c) * (1 + abs(np.random.normal(0, 0.003)))
            l = min(o, c) * (1 - abs(np.random.normal(0, 0.003)))
            data.append({"open": o, "high": h, "low": l, "close": c, "volume": np.random.uniform(100, 1000)})
            price = c

        df = pd.DataFrame(data)

        # Step 2: Generate signals based on simple EMA crossover
        ema_fast = df["close"].ewm(span=21, adjust=False).mean()
        ema_slow = df["close"].ewm(span=90, adjust=False).mean()
        signals = pd.Series(0, index=df.index)
        signals[ema_fast > ema_slow] = 1
        signals[ema_fast < ema_slow] = -1

        # Step 3: Run backtest
        bt = VectorizedBacktester(initial_capital=initial_capital)
        results = bt.run_backtest(
            df,
            signals,
            take_profits=pd.Series(0, index=df.index),
            stop_losses=pd.Series(0, index=df.index),
        )

        # Step 4: Store results in database
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO backtest_results
                        (strategy_id, asset_symbol, timeframe, start_date, end_date,
                         initial_capital, final_capital, total_return, sharpe_ratio,
                         max_drawdown, win_rate, profit_factor, total_trades)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """,
                    strategy_id,
                    symbol,
                    timeframe,
                    pd.Timestamp.now().date(),
                    pd.Timestamp.now().date(),
                    initial_capital,
                    results["final_capital"],
                    results["total_return"],
                    results["sharpe_ratio"],
                    results["max_drawdown"],
                    results["win_rate"],
                    results["profit_factor"],
                    results["total_trades"],
                )

        # Step 5: Publish metrics to Redis for dashboard
        await redis_client.hset(
            f"research:metrics:{symbol}",
            mapping={
                "sharpe_ratio": str(results["sharpe_ratio"]),
                "max_drawdown": str(results["max_drawdown"]),
                "win_rate": str(results["win_rate"]),
                "profit_factor": str(results["profit_factor"]),
                "total_trades": str(results["total_trades"]),
            },
        )

        logger.info(
            "quant_research.job_complete",
            symbol=symbol,
            sharpe=results["sharpe_ratio"],
            return_pct=results["total_return"],
        )

    except Exception as e:
        logger.error("quant_research.job_failed", error=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
