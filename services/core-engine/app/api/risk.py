from fastapi import APIRouter, Request, HTTPException
import structlog
import os

logger = structlog.get_logger()
router = APIRouter()

@router.get("/metrics")
async def get_dashboard_metrics(request: Request):
    """Get Top Bar KPIs (Equity, Daily PnL, Drawdown, Exposure)"""
    redis = request.app.state.redis
    db = request.app.state.pool
    
    # ── Fallback Values (Simulation/Demo Mode) ──
    demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true" # Default to true for better UX if no data
    
    try:
        # If Redis is unavailable, immediately return demo data
        if not redis:
            import random
            return {
                "equity": 100000.0 + random.uniform(-100, 500),
                "daily_pnl": 150.0 + random.uniform(-10, 50),
                "drawdown_pct": 0.45,
                "exposure_pct": 12.5
            }

        # Fetch high-speed account data from Redis
        account_data = await redis.hgetall("account:balance")
        daily_dd = await redis.get("risk:daily_drawdown")
        
        # Injection for Demo/Simulation mode when no actual trading data exists
        if not account_data or demo_mode:
            import random
            return {
                "equity": 100000.0 + random.uniform(-500, 1500),
                "daily_pnl": 1250.75 + random.uniform(-50, 200),
                "drawdown_pct": 0.45,
                "exposure_pct": 12.5
            }

        equity = float(account_data.get("equity", 0))
        used = float(account_data.get("margin_used", 0))
        exposure = (used / equity * 100) if equity > 0 else 0
        
        return {
            "equity": equity,
            "daily_pnl": float(account_data.get("daily_pnl", 0)),
            "drawdown_pct": float(daily_dd or 0) * 100,
            "exposure_pct": exposure
        }
    except Exception as e:
        logger.error("api.metrics_error", error=str(e))
        raise HTTPException(status_code=500, detail="Data fetch failed")

@router.post("/settings")
async def update_risk_settings(request: Request):
    """Update risk management parameters (e.g. kill switches, limits)"""
    data = await request.json()
    redis = request.app.state.redis
    
    try:
        # 1. Update individual key-value pairs for quick access
        if "risk_limit_pct" in data:
            await redis.set("risk:max_leverage", data["risk_limit_pct"])
        
        if "kill_switch" in data:
            await redis.set("risk:kill_switch", "true" if data["kill_switch"] else "false")

        # 2. Store all settings in a single JSON for the Risk Engine's monitor_loop
        import orjson
        current = await redis.get("risk:settings")
        settings = orjson.loads(current) if current else {}
        settings.update(data)
        await redis.set("risk:settings", orjson.dumps(settings).decode())
            
        logger.info("api.risk_settings_updated", settings=settings)
        return {"status": "success", "message": "Risk settings synchronized with execution engine."}
    except Exception as e:
        logger.error("api.risk_update_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update settings")
