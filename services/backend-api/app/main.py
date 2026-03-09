"""
╔══════════════════════════════════════════════════════════════╗
║  Backend API - FastAPI Gateway                               ║
║  Serves data to dashboard, handles authentication, and proxy ║
╚══════════════════════════════════════════════════════════════╝
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncpg
import redis.asyncio as aioredis
import structlog
import os
from dotenv import load_dotenv

from app.routes import auth, trading, strategy, research, risk, websocket

load_dotenv()
logger = structlog.get_logger()

# Global connections
db_pool = None
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("api.starting")
    global db_pool, redis_client
    
    try:
        db_pool = await asyncpg.create_pool(
            host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "quantbot"),
            user=os.getenv("POSTGRES_USER", "quantbot_user"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            min_size=1,
            max_size=5,
            command_timeout=5
        )
        app.state.pool = db_pool
        logger.info("db.connected")
    except Exception as e:
        logger.warning("db.connection_failed", error=str(e))
        app.state.pool = None

    try:
        redis_client = aioredis.Redis(
            host=os.getenv("REDIS_HOST", "127.0.0.1"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD", ""),
            decode_responses=True,
            socket_timeout=5
        )
        app.state.redis = redis_client
        logger.info("redis.connected")
    except Exception as e:
        logger.warning("redis.connection_failed", error=str(e))
        app.state.redis = None
    
    yield
    
    # Shutdown
    logger.info("api.stopping")
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()


app = FastAPI(
    title="QuantBot Institutional API",
    description="Backend API for Hummingbot Infrastructure",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Handled by Nginx in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])
app.include_router(strategy.router, prefix="/api/strategy", tags=["strategy"])
app.include_router(research.router, prefix="/api/research", tags=["research"])
app.include_router(risk.router, prefix="/api/risk", tags=["risk"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
