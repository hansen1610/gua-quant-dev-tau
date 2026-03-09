import asyncio
import os
import time
import orjson
import redis.asyncio as aioredis
import structlog
import random

logger = structlog.get_logger()

async def stress_test():
    """Injects high-frequency ticks to test system limits."""
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_pass = os.getenv("REDIS_PASSWORD", "dev_redis_pass")

    redis = aioredis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_pass,
        decode_responses=True
    )

    symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "ARB-USD", "OP-USD"]
    
    # Burst parameters
    burst_count = 1000  # Total ticks per burst
    interval_ms = 10    # 10ms between ticks (100 ticks per second)
    
    logger.info("stress_test.starting", burst_count=burst_count, interval_ms=interval_ms)

    start_time = time.time()
    ticks_sent = 0

    try:
        for _ in range(burst_count):
            symbol = random.choice(symbols)
            tick = {
                "symbol": symbol,
                "price": round(random.uniform(100, 100000), 2),
                "timestamp": int(time.time() * 1000)
            }
            await redis.publish("market:ticks", orjson.dumps(tick).decode())
            ticks_sent += 1
            if ticks_sent % 100 == 0:
                logger.info("stress_test.progress", sent=ticks_sent)
            # await asyncio.sleep(interval_ms / 1000.0)
        
        duration = time.time() - start_time
        logger.info("stress_test.completed", 
                    total_sent=ticks_sent, 
                    duration=f"{duration:.2f}s", 
                    tps=f"{ticks_sent/duration:.2f}")

    except Exception as e:
        logger.error("stress_test.error", error=str(e))
    finally:
        await redis.close()

if __name__ == "__main__":
    asyncio.run(stress_test())
