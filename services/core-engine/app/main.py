import asyncio
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# utils
from app.utils.db import create_db_pool
from app.utils.redis_client import create_redis_client
from app.utils.health_monitor import health_monitor_loop

# engine
from app.engine.coordinator import StrategyCoordinator

# routers
from app.api.auth import router as auth_router
from app.api.trading import router as trading_router
from app.api.strategy import router as strategy_router
from app.api.risk import router as risk_router
from app.api.research import router as research_router
from app.api.websocket import router as websocket_router
from app.api.health import router as health_router

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("core_engine.starting")

    # a. Buat db_pool
    db_pool = await create_db_pool()
    # b. Buat redis_client
    redis_client = await create_redis_client()
    
    # c. Simpan ke app.state
    app.state.db_pool = db_pool
    app.state.redis_client = redis_client
    
    coordinator = StrategyCoordinator(db_pool=db_pool, redis_client=redis_client)
    app.state.coordinator = coordinator

    # d. asyncio.create_task() untuk coordinator.start() — BUNGKUS try-except
    async def run_coordinator():
        try:
            await coordinator.start()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("core_engine.coordinator_error", error=str(e))

    coordinator_task = asyncio.create_task(run_coordinator())

    # e. asyncio.create_task() untuk health_monitor_loop() — BUNGKUS try-except
    async def run_health_monitor():
        try:
            await health_monitor_loop(db_pool, redis_client)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("core_engine.health_monitor_error", error=str(e))

    monitor_task = asyncio.create_task(run_health_monitor())

    yield

    logger.info("core_engine.stopping")
    monitor_task.cancel()
    coordinator_task.cancel()
    await coordinator.stop()
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()

app = FastAPI(title="QuantBot Core Engine", lifespan=lifespan)

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /health endpoint API
@app.get("/health")
async def health():
    return {"status": "ok", "service": "core-engine"}

# Register routers
app.include_router(auth_router, prefix="/api/auth")
app.include_router(trading_router, prefix="/api/trading")
app.include_router(strategy_router, prefix="/api/strategy")
app.include_router(risk_router, prefix="/api/risk")
app.include_router(research_router, prefix="/api/research")
app.include_router(websocket_router)
app.include_router(health_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
