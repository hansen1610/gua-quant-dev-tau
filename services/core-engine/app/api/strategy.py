from fastapi import APIRouter, Request, HTTPException
import structlog

logger = structlog.get_logger()
router = APIRouter()

# Mock data for when DB is unavailable
MOCK_STRATEGIES = [
    { 
        "id": "1", "name": "EMA Trend Following", "type": "trend", "is_enabled": True, 
        "risk_per_trade": 0.015, "max_daily_drawdown": 0.05, 
        "parameters": { "take_profit_pct": 0.025, "stop_loss_pct": 0.015 },
        "pnl_daily": 450.20, "win_rate": 64, "trades_count": 12, "volume_24h": 35000 
    },
    { 
        "id": "2", "name": "Fibonacci Pullback", "type": "mean_reversion", "is_enabled": True, 
        "risk_per_trade": 0.020, "max_daily_drawdown": 0.05,
        "parameters": { "take_profit_pct": 0.025, "stop_loss_pct": 0.015 },
        "pnl_daily": -120.50, "win_rate": 45, "trades_count": 8, "volume_24h": 52000 
    },
    { 
        "id": "3", "name": "ML Meta Filter", "type": "ml_ensemble", "is_enabled": False, 
        "risk_per_trade": 0.010, "max_daily_drawdown": 0.05,
        "parameters": { "take_profit_pct": 0.020, "stop_loss_pct": 0.010 },
        "pnl_daily": 0, "win_rate": 78, "trades_count": 0, "volume_24h": 0 
    },
    { 
        "id": "4", "name": "Volatility Sizing", "type": "risk_management", "is_enabled": True, 
        "risk_per_trade": 0.018, "max_daily_drawdown": 0.05,
        "parameters": { "take_profit_pct": 0.030, "stop_loss_pct": 0.015 },
        "pnl_daily": 85.00, "win_rate": 92, "trades_count": 24, "volume_24h": 125000 
    },
    { 
        "id": "5", "name": "Multi-Timeframe Confluence", "type": "multi_tf", "is_enabled": False, 
        "risk_per_trade": 0.025, "max_daily_drawdown": 0.05,
        "parameters": { "take_profit_pct": 0.025, "stop_loss_pct": 0.015 },
        "pnl_daily": 0, "win_rate": 55, "trades_count": 0, "volume_24h": 0 
    },
]

@router.get("/")
async def list_strategies(request: Request):
    """List all deployed strategies and their statuses."""
    db = request.app.state.db_pool
    if not db:
        return {"strategies": MOCK_STRATEGIES}
        
    try:
        async with db.acquire() as conn:
            records = await conn.fetch("SELECT id, name, type, is_enabled, risk_per_trade, max_daily_drawdown, parameters FROM strategies")
            return {"strategies": [dict(r) for r in records]}
    except Exception as e:
        logger.error("api.strategy_list_error", error=str(e))
        return {"strategies": MOCK_STRATEGIES}

@router.patch("/{strategy_id}/parameters")
async def update_strategy_parameters(strategy_id: str, data: dict, request: Request):
    """Update strategy risk/reward parameters (Risk, TP, SL, MaxDD)."""
    db = request.app.state.db_pool
    redis = request.app.state.redis_client_client
    
    # Extract values
    risk = data.get("risk_per_trade")
    max_dd = data.get("max_daily_drawdown")
    tp = data.get("take_profit_pct")
    sl = data.get("stop_loss_pct")

    if not db:
        # Update mock data
        for s in MOCK_STRATEGIES:
            if s["id"] == strategy_id:
                if risk is not None: s["risk_per_trade"] = risk
                if max_dd is not None: s["max_daily_drawdown"] = max_dd
                if tp is not None: s["parameters"]["take_profit_pct"] = tp
                if sl is not None: s["parameters"]["stop_loss_pct"] = sl
                return {"status": "success", "strategy": s}
        raise HTTPException(status_code=404, detail="Strategy not found")

    try:
        async with db.acquire() as conn:
            # 1. Update primitive columns and parameters JSONB
            # We use jsonb_set to update specific keys in the parameters JSON
            await conn.execute(
                """
                UPDATE strategies 
                SET risk_per_trade = COALESCE($2, risk_per_trade),
                    max_daily_drawdown = COALESCE($3, max_daily_drawdown),
                    parameters = parameters || $4::jsonb,
                    updated_at = NOW()
                WHERE id = $1
                """,
                strategy_id, risk, max_dd, 
                '{"take_profit_pct": %s, "stop_loss_pct": %s}' % (tp if tp else 'null', sl if sl else 'null')
            )
            
            # 2. Notify execution engine via Redis
            if redis:
                await redis.publish("settings:strategy_updates", '{"reload": true, "strategy_id": "%s"}' % strategy_id)
            
            return {"status": "success", "message": "Parameters synchronized with cluster."}
    except Exception as e:
        logger.error("api.strategy_update_error", error=str(e))
        raise HTTPException(status_code=500, detail="Database update failed")

@router.post("/{strategy_id}/toggle")
async def toggle_strategy(strategy_id: str, request: Request):
    """Enable or disable a specific algorithm module."""
    db = request.app.state.db_pool
    redis = request.app.state.redis_client_client
    
    if not db:
        # Simulate toggle for mock data
        for s in MOCK_STRATEGIES:
            if s["id"] == strategy_id:
                s["is_enabled"] = not s["is_enabled"]
                return {"status": "success", "is_enabled": s["is_enabled"]}
        raise HTTPException(status_code=404, detail="Strategy not found")

    try:
        async with db.acquire() as conn:
            # Flip boolean status
            new_status = await conn.fetchval(
                """UPDATE strategies SET is_enabled = NOT is_enabled, updated_at = NOW() 
                   WHERE id = $1 RETURNING is_enabled""", 
                strategy_id
            )
            
            if new_status is None:
                raise HTTPException(status_code=404, detail="Strategy not found")
                
            # Broadcast state change so Strategy Engine container reloads it
            if redis:
                await redis.publish("settings:strategy_updates", '{"reload": true, "strategy_id": "%s"}' % strategy_id)
            
            return {"status": "success", "is_enabled": new_status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("api.strategy_toggle_error", error=str(e))
        return {"status": "error", "message": "Simulated failover: DB Error"}
