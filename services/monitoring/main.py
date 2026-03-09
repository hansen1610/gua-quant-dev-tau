"""
╔══════════════════════════════════════════════════════════════╗
║  Monitoring & Health Service                                 ║
║  Container health polling, metrics aggregation, alerting     ║
╚══════════════════════════════════════════════════════════════╝
"""
import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import asyncpg
import redis.asyncio as aioredis
import structlog
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()
logger = structlog.get_logger()

db_pool = None
redis_client = None

# Services to monitor with their Redis health keys
MONITORED_SERVICES = {
    "hummingbot": {"redis_key": "health:hummingbot", "critical": True},
    "strategy-engine": {"redis_key": "health:strategy_engine", "critical": True},
    "backend-api": {"url": "http://backend-api:8000/health", "critical": True},
    "ml-engine": {"url": "http://ml-engine:8003/health", "critical": False},
    "quant-research": {"url": "http://quant-research:8002/health", "critical": False},
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool, redis_client
    logger.info("monitoring.starting")

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

    # Start background health monitor
    monitor_task = asyncio.create_task(_health_monitor_loop())

    yield

    monitor_task.cancel()
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()
    logger.info("monitoring.stopped")


app = FastAPI(title="Monitoring & Health API", lifespan=lifespan)


# ── Health Check Endpoints ────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "monitoring"}


@app.get("/api/monitoring/services")
async def get_all_service_health():
    """Get health status of all monitored services."""
    results = {}
    for service_name, config in MONITORED_SERVICES.items():
        results[service_name] = await _check_service_health(service_name, config)
    return {"services": results, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/monitoring/system")
async def get_system_metrics():
    """Get aggregated system metrics from Redis cache."""
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


@app.get("/api/monitoring/health_history")
async def get_health_history(limit: int = 100):
    """Get recent health log entries from database."""
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


@app.get("/api/monitoring/risk_events")
async def get_risk_events(limit: int = 50):
    """Get recent risk events."""
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


# ── Background Health Monitor Loop ───────────────────────
async def _health_monitor_loop():
    """Periodically check all services and record health in DB."""
    interval = int(os.getenv("HEALTH_CHECK_INTERVAL_SEC", "30"))
    logger.info("monitoring.loop_started", interval_sec=interval)

    while True:
        try:
            for service_name, config in MONITORED_SERVICES.items():
                result = await _check_service_health(service_name, config)

                # Record to database
                if db_pool:
                    try:
                        async with db_pool.acquire() as conn:
                            await conn.execute(
                                """
                                INSERT INTO health_logs
                                    (service_name, status, latency_ms, details)
                                VALUES ($1, $2, $3, $4)
                                """,
                                service_name,
                                result["status"],
                                result.get("latency_ms"),
                                str(result.get("details", {})),
                            )
                    except Exception as e:
                        logger.error("monitoring.db_write_error", error=str(e))

                # Publish health status to Redis for dashboard consumption
                await redis_client.hset(
                    f"health:{service_name}",
                    mapping={
                        "status": result["status"],
                        "last_check": datetime.now(timezone.utc).isoformat(),
                    },
                )

                # Alert on critical service failure
                if result["status"] == "unhealthy" and config.get("critical"):
                    logger.critical(
                        "monitoring.critical_service_down", service=service_name
                    )
        except Exception as e:
            logger.error("monitoring.loop_error", error=str(e))

        await asyncio.sleep(interval)


async def _check_service_health(service_name: str, config: dict) -> dict:
    """Check health of a single service via Redis heartbeat or HTTP probe."""
    import time

    start = time.monotonic()

    # Method 1: Check Redis heartbeat
    redis_key = config.get("redis_key")
    if redis_key:
        try:
            data = await redis_client.hgetall(redis_key)
            if data and data.get("status") == "running":
                latency = int((time.monotonic() - start) * 1000)
                return {
                    "status": "healthy",
                    "latency_ms": latency,
                    "details": data,
                }
            return {"status": "unhealthy", "details": {"reason": "no heartbeat"}}
        except Exception as e:
            return {"status": "unhealthy", "details": {"error": str(e)}}

    # Method 2: HTTP health probe
    url = config.get("url")
    if url:
        try:
            import aiohttp

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                async with session.get(url) as resp:
                    latency = int((time.monotonic() - start) * 1000)
                    if resp.status == 200:
                        return {"status": "healthy", "latency_ms": latency}
                    return {
                        "status": "degraded",
                        "latency_ms": latency,
                        "details": {"http_status": resp.status},
                    }
        except Exception as e:
            return {"status": "unhealthy", "details": {"error": str(e)}}

    return {"status": "unknown"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
