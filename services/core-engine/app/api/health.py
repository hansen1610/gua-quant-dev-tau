from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Request

from app.utils.health_monitor import MONITORED_SERVICES, check_service_health

logger = structlog.get_logger()
router = APIRouter()

@router.get("/api/monitoring/services")
async def get_all_service_health(request: Request):
    """Get health status of all monitored services."""
    results = {}
    redis = request.app.state.redis_client_client
    for service_name, config in MONITORED_SERVICES.items():
        results[service_name] = await check_service_health(redis_client, service_name, config)
    return {"services": results, "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/api/monitoring/system")
async def get_system_metrics(request: Request):
    """Get aggregated system metrics from Redis cache."""
    redis = request.app.state.redis_client_client
    try:
        # Account data
        account = await redis_client.hgetall("account:balance") or {}
        # Risk state
        kill_switch = await redis_client.get("risk:kill_switch") or "false"
        daily_dd = await redis_client.get("risk:daily_drawdown") or "0"

        return {
            "equity": float(account.get("equity", 0)),
            "available_balance": float(account.get("available", 0)),
            "margin_used": float(account.get("margin_used", 0)),
            "positions_count": int(account.get("positions_count", 0)),
            "kill_switch_active": kill_switch == "true",
            "daily_drawdown_pct": float(daily_dd),
        }
    except Exception as e:
        logger.error("monitoring.system_metrics_error", error=str(e))
        return {"error": str(e)}


@router.get("/api/monitoring/health_history")
async def get_health_history(request: Request, limit: int = 100):
    """Get recent health log entries from database."""
    db_pool = request.app.state.db_pool
    if not db_pool:
        return {"logs": []}
    try:
        async with db_pool.acquire() as conn:
            records = await conn.fetch(
                "SELECT * FROM health_logs ORDER BY checked_at DESC LIMIT $1", limit
            )
            return {"logs": [dict(r) for r in records]}
    except Exception as e:
        logger.error("monitoring.history_error", error=str(e))
        return {"logs": [], "error": str(e)}


@router.get("/api/monitoring/risk_events")
async def get_risk_events(request: Request, limit: int = 50):
    """Get recent risk events."""
    db_pool = request.app.state.db_pool
    if not db_pool:
        return {"events": []}
    try:
        async with db_pool.acquire() as conn:
            records = await conn.fetch(
                "SELECT * FROM risk_events ORDER BY created_at DESC LIMIT $1", limit
            )
            return {"events": [dict(r) for r in records]}
    except Exception as e:
        logger.error("monitoring.risk_events_error", error=str(e))
        return {"events": [], "error": str(e)}
