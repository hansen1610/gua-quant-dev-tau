import asyncio
import os
import random
import time
import orjson
import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger()

async def simulate_market():
    """Publishes mock price ticks to Redis to drive strategies."""
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_pass = os.getenv("REDIS_PASSWORD", "")

    redis = aioredis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_pass,
        decode_responses=True
    )

    symbols = ["BTC-USD", "ETH-USD", "SOL-USD"]
    # Initial prices
    prices = {
        "BTC-USD": 95000.0,
        "ETH-USD": 3200.0,
        "SOL-USD": 145.0
    }

    logger.info("streamer.started", symbols=symbols)

    try:
        while True:
            for symbol in symbols:
                # Random walk simulation
                change_pct = random.uniform(-0.0005, 0.0005) # +/- 0.05%
                prices[symbol] *= (1 + change_pct)
                
                tick = {
                    "symbol": symbol,
                    "price": round(prices[symbol], 2),
                    "bid": round(prices[symbol] * 0.9999, 2),
                    "ask": round(prices[symbol] * 1.0001, 2),
                    "timestamp": int(time.time() * 1000)
                }
                
                # Publish to strategies
                await redis.publish("market:ticks", orjson.dumps(tick).decode())
                
                # Update last price in Redis for frontend
                await redis.hset("market:prices", symbol, prices[symbol])
                
            await asyncio.sleep(1) # 1 tick per second per symbol
    except Exception as e:
        logger.error("streamer.error", error=str(e))
    finally:
        await redis.close()

if __name__ == "__main__":
    asyncio.run(simulate_market())
