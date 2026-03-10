import asyncio
import os
import time
from datetime import datetime, timezone

import structlog

logger = structlog.get_logger()

# Services to monitor with their Redis health keys
MONITORED_SERVICES = {
    "hummingbot": {"redis_key": "health:hummingbot", "critical": True},
    "ml-engine": {"url": "http://ml-engine:8003/health", "critical": False},
    "quant-research": {"url": "http://quant-research:8002/health", "critical": False},
}

async def health_monitor_loop(db_pool, redis_client):
    """Periodically check all services and record health in DB."""
    interval = int(os.getenv("HEALTH_CHECK_INTERVAL_SEC", "30"))
    logger.info("monitoring.loop_started", interval_sec=interval)

    while True:
        try:
            for service_name, config in MONITORED_SERVICES.items():
                result = await check_service_health(redis_client, service_name, config)

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
                if redis_client:
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
        except asyncio.CancelledError:
            logger.info("monitoring.loop_cancelled")
            break
        except Exception as e:
            logger.error("monitoring.loop_error", error=str(e))

        await asyncio.sleep(interval)


async def check_service_health(redis_client, service_name: str, config: dict) -> dict:
    """Check health of a single service via Redis heartbeat or HTTP probe."""
    start = time.monotonic()

    # Method 1: Check Redis heartbeat
    redis_key = config.get("redis_key")
    if redis_key and redis_client:
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
