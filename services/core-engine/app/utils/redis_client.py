import os
import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

async def create_redis_client():
    return aioredis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD", ""),
        decode_responses=True,
    )
