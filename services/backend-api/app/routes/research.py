from fastapi import APIRouter, Request, HTTPException
import structlog
from typing import Dict

logger = structlog.get_logger()
router = APIRouter()

@router.get("/metrics/{symbol}")
async def get_symbol_metrics(symbol: str, request: Request):
    """Retrieve robust analytics for a trading algorithm / market symbol via caching."""
    redis = request.app.state.redis
    import os
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    try:
        # Fetch pre-calculated rolling logic metrics
        cached_result = await redis.hgetall(f"research:metrics:{symbol}")
        
        if not cached_result and demo_mode:
            import random
            # Generate a realistic equity curve for demo
            base = 10000
            curve = []
            for _ in range(30):
                base = base * (1 + random.uniform(-0.02, 0.05))
                curve.append(round(base, 2))
            
            return {"symbol": symbol, "data": {
                "sharpe_ratio": 2.1 + random.uniform(-0.3, 0.5),
                "max_drawdown": 4.5 + random.uniform(0.5, 2.0),
                "win_rate": 62.5 + random.uniform(-5, 10),
                "wfa_efficiency": 82.4,
                "monte_carlo_prio": 88.0,
                "equity_curve": ",".join(map(str, curve))
            }}

        if(cached_result):
            return {"symbol": symbol, "data": cached_result}
            
        return {"symbol": symbol, "data": {
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "wfa_efficiency": 0.0,
            "monte_carlo_prio": 0.0,
            "equity_curve": ""
        }}
    except Exception as e:
        logger.error("api.research_metrics_err", error=str(e))
        raise HTTPException(status_code=500, detail="Data fetch failed")

@router.post("/run_backtest")
async def queue_backtest(params: dict, request: Request):
    """Queue a heavy simulated backtest on Quant Research Lab queue via Redis."""
    redis = request.app.state.redis
    try:
        import json
        await redis.lpush("jobs:quant-research:backtest", json.dumps(params))
        return {"status": "queued", "message": "Backtest added to computation queue."}
    except Exception as e:
        logger.error("api.research_bt_err", error=str(e))
        raise HTTPException(status_code=500, detail="Job Queue failure")
