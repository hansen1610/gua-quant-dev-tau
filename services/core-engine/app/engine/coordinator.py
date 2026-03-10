import asyncio
import os
import time
from typing import Dict

import structlog

from app.engine.risk_engine import InstitutionalRiskEngine
from app.strategies.ema_trend import EMATrendStrategy
from app.strategies.fibonacci_pullback import FibonacciPullbackStrategy

logger = structlog.get_logger()

class StrategyCoordinator:
    def __init__(self, db_pool, redis_client):
        self.db_pool = db_pool
        self.redis = redis_client
        self.risk_engine = InstitutionalRiskEngine()
        self.risk_engine.set_redis(self.redis)
        self.risk_engine.set_db(self.db_pool)
        self.strategies = {}
        self._running = False
        
    async def start(self):
        logger.info("strategy_engine.starting")
        
        # Load active strategies
        await self._load_strategies()
        self._running = True
        
        # Start loops
        await asyncio.gather(
            self._market_data_listener(),
            self._strategy_eval_loop(),
            self.risk_engine.monitor_risk_loop()
        )

    async def stop(self):
        logger.info("strategy_engine.stopping")
        self._running = False

    async def _load_strategies(self):
        """Load strategies from database"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM strategies WHERE is_enabled = true")
            for row in rows:
                logger.info("strategy_engine.row_type", type=str(type(row)), data=dict(row))
                strat_type = row['type']
                strat_id = str(row['id'])
                if strat_type in ['ema_trend', 'trend_following']:
                    self.strategies[strat_id] = EMATrendStrategy(dict(row))
                elif strat_type in ['fib_pullback', 'mean_reversion']:
                    self.strategies[strat_id] = FibonacciPullbackStrategy(dict(row))
                # Future types can be added here
                
        logger.info("strategy_engine.loaded", count=len(self.strategies))
        # Report health/ready status
        await self.redis.set("service:core-engine:status", "running")
        await self.redis.set("service:core-engine:last_heartbeat", int(time.time()))

    async def _market_data_listener(self):
        """Listen to market data from Redis (populated by Hummingbot)"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe("market:ticks")
        
        async for message in pubsub.listen():
            if not self._running:
                break
            if message["type"] == "message":
                import orjson
                data = orjson.loads(message["data"])
                # Route to appropriate strategies
                for strat_id, strategy in self.strategies.items():
                    if data['symbol'] in strategy.symbols:
                        await strategy.on_tick(data)

    async def _strategy_eval_loop(self):
        """Periodic evaluation of candles and generation of signals"""
        while self._running:
            for strat_id, strategy in self.strategies.items():
                try:
                    signals = await strategy.evaluate()
                    for signal in signals:
                        # Pass through Risk Engine first
                        approved_signal = await self.risk_engine.validate_signal(signal, strategy)
                        if approved_signal:
                            await self._publish_signal(approved_signal)
                except Exception as e:
                    logger.error("strategy_engine.eval_error", strategy_id=strat_id, error=str(e))
            # Heartbeat
            await self.redis.set("service:core-engine:last_heartbeat", int(time.time()))
            await asyncio.sleep(5)  # Evaluate every 5 seconds

    async def _publish_signal(self, signal: dict):
        """Publish valid signal to Redis for Hummingbot execution"""
        import orjson
        await self.redis.publish("signals:execute", orjson.dumps(signal).decode())
        logger.info("strategy_engine.signal_published", signal=signal)
