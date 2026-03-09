"""
╔══════════════════════════════════════════════════════════════╗
║  Hummingbot Execution Engine                                 ║
║  Core order lifecycle, failover, latency monitoring          ║
╚══════════════════════════════════════════════════════════════╝
"""
import asyncio
import os
import signal
import time
from datetime import datetime, timezone
from typing import Optional

import asyncpg
import redis.asyncio as aioredis
import structlog
from dotenv import load_dotenv

from connectors.hyperliquid_connector import HyperliquidConnector, OrderResult

load_dotenv()
logger = structlog.get_logger()


class ExecutionEngine:
    """
    Core execution engine:
    - Receives signals from Strategy Engine via Redis pub/sub
    - Executes orders on Hyperliquid
    - Manages order lifecycle (submit → fill → confirm)
    - Monitors latency and slippage
    - Implements failover and auto-restart
    """

    def __init__(self):
        self.connector = HyperliquidConnector(
            api_key=os.getenv("HYPERLIQUID_API_KEY", ""),
            api_secret=os.getenv("HYPERLIQUID_API_SECRET", ""),
            wallet_address=os.getenv("HYPERLIQUID_WALLET_ADDRESS", ""),
            testnet=os.getenv("HYPERLIQUID_TESTNET", "true").lower() == "true",
        )
        self.trading_mode = os.getenv("TRADING_MODE", "simulation")
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis: Optional[aioredis.Redis] = None
        self._running = False
        self._latency_samples: list[int] = []

    async def start(self):
        """Initialize connections and start the execution loop."""
        logger.info("execution_engine.starting", mode=self.trading_mode)

        # Database connection
        self.db_pool = await asyncpg.create_pool(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "quantbot"),
            user=os.getenv("POSTGRES_USER", "quantbot_user"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            min_size=2,
            max_size=10,
        )

        # Redis connection
        self.redis = aioredis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD", ""),
            decode_responses=True,
        )

        # Connect to Hyperliquid
        await self.connector.connect()

        self._running = True

        # Start concurrent tasks
        await asyncio.gather(
            self._signal_listener(),
            self._heartbeat_loop(),
            self._funding_monitor(),
            self._equity_snapshot_loop(),
            self.connector.start_ws(),
        )

    async def stop(self):
        """Graceful shutdown."""
        logger.info("execution_engine.stopping")
        self._running = False
        await self.connector.disconnect()
        if self.db_pool:
            await self.db_pool.close()
        if self.redis:
            await self.redis.close()
        logger.info("execution_engine.stopped")

    # ── Signal Listener (Redis Pub/Sub) ───────────────────
    async def _signal_listener(self):
        """Listen for trade signals from Strategy Engine."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe("signals:execute")
        logger.info("execution_engine.listening", channel="signals:execute")

        async for message in pubsub.listen():
            if not self._running:
                break
            if message["type"] == "message":
                try:
                    import orjson
                    signal_data = orjson.loads(message["data"])
                    await self._process_signal(signal_data)
                except Exception as e:
                    logger.error("execution_engine.signal_error", error=str(e))

    async def _process_signal(self, signal: dict):
        """Process a trade signal from the strategy engine."""
        symbol = signal.get("symbol")
        action = signal.get("action")  # "buy" | "sell" | "close"
        size = signal.get("size", 0)
        strategy_id = signal.get("strategy_id")
        stop_loss = signal.get("stop_loss")
        take_profit = signal.get("take_profit")

        logger.info(
            "execution_engine.processing_signal",
            symbol=symbol,
            action=action,
            size=size,
            strategy=strategy_id,
        )

        # Check risk limits before execution
        risk_ok = await self._check_risk_limits(symbol, size, action)
        if not risk_ok:
            logger.warning("execution_engine.risk_blocked", symbol=symbol)
            await self._log_risk_event("risk_block", f"Order blocked by risk limits: {symbol} {action}")
            return

        if self.trading_mode == "simulation":
            result = await self._simulate_order(symbol, action, size)
        else:
            result = await self.connector.place_order(
                symbol=symbol,
                side=action if action != "close" else "sell",
                size=size,
                order_type="market",
                reduce_only=(action == "close"),
            )

        # Record order in database
        await self._record_order(result, signal)

        # Track latency
        if result.latency_ms and result.latency_ms > 0:
            self._latency_samples.append(result.latency_ms)
            if len(self._latency_samples) > 100:
                self._latency_samples.pop(0)

        # Publish result back
        await self.redis.publish("signals:result", result.model_dump_json())

        logger.info(
            "execution_engine.order_result",
            success=result.success,
            latency_ms=result.latency_ms,
            slippage=result.slippage,
        )

    async def _simulate_order(self, symbol: str, action: str, size: float) -> OrderResult:
        """Simulate order execution for paper trading."""
        market = await self.connector.get_market_data(symbol)
        price = market.get("mid_price", 0)
        if price == 0:
            # Use a simulated price if API isn't connected
            import random
            price = random.uniform(40000, 50000) if "BTC" in symbol else random.uniform(2000, 3000)

        # Simulate realistic slippage
        import random
        slippage = random.uniform(0.0001, 0.001)
        if action == "buy":
            filled_price = price * (1 + slippage)
        else:
            filled_price = price * (1 - slippage)

        return OrderResult(
            success=True,
            order_id=f"SIM-{int(time.time()*1000)}",
            filled_price=round(filled_price, 2),
            filled_qty=size,
            slippage=round(slippage, 6),
            latency_ms=1,
        )

    # ── Risk Checks ───────────────────────────────────────
    async def _check_risk_limits(self, symbol: str, size: float, action: str) -> bool:
        """Pre-execution risk validation."""
        try:
            # Check kill switch
            kill_switch = await self.redis.get("risk:kill_switch")
            if kill_switch == "true":
                return False

            # Check daily drawdown
            daily_dd = await self.redis.get("risk:daily_drawdown")
            max_dd = float(os.getenv("MAX_DAILY_DRAWDOWN_PCT", "0.05"))
            if daily_dd and float(daily_dd) >= max_dd:
                return False

            # Check max exposure
            exposure = await self.redis.get("risk:total_exposure")
            max_exp = float(os.getenv("MAX_PORTFOLIO_EXPOSURE_PCT", "0.30"))
            if exposure and float(exposure) >= max_exp:
                return False

            # Check consecutive losses
            consec_losses = await self.redis.get("risk:consecutive_losses")
            max_consec = int(os.getenv("MAX_CONSECUTIVE_LOSSES", "5"))
            if consec_losses and int(consec_losses) >= max_consec:
                return False

            return True
        except Exception as e:
            logger.error("execution_engine.risk_check_failed", error=str(e))
            return False  # Fail-safe: block trade if risk check fails

    # ── Database Operations ───────────────────────────────
    async def _record_order(self, result: OrderResult, signal: dict):
        """Record order result in PostgreSQL."""
        if not self.db_pool:
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO orders (external_id, strategy_id, side, order_type,
                                       quantity, filled_quantity, filled_price, status,
                                       slippage, latency_ms, error_message)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """,
                    result.order_id,
                    signal.get("strategy_id"),
                    signal.get("action", "buy"),
                    "market",
                    signal.get("size", 0),
                    result.filled_qty or 0,
                    result.filled_price or 0,
                    "filled" if result.success else "error",
                    result.slippage or 0,
                    result.latency_ms or 0,
                    result.error,
                )
        except Exception as e:
            logger.error("execution_engine.db_error", error=str(e))

    async def _log_risk_event(self, event_type: str, description: str):
        """Log risk event to database."""
        if not self.db_pool:
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO risk_events (event_type, severity, description)
                    VALUES ($1, $2, $3)
                    """,
                    event_type, "warning", description,
                )
        except Exception as e:
            logger.error("execution_engine.risk_log_error", error=str(e))

    # ── Background Tasks ──────────────────────────────────
    async def _heartbeat_loop(self):
        """Publish heartbeat to Redis for monitoring."""
        while self._running:
            avg_latency = (
                sum(self._latency_samples) / len(self._latency_samples)
                if self._latency_samples
                else 0
            )
            await self.redis.hset("health:hummingbot", mapping={
                "status": "running",
                "mode": self.trading_mode,
                "avg_latency_ms": str(round(avg_latency, 1)),
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            })
            await asyncio.sleep(10)

    async def _funding_monitor(self):
        """Monitor funding rates and publish alerts."""
        symbols = ["BTC", "ETH", "SOL"]
        while self._running:
            for symbol in symbols:
                try:
                    rate = await self.connector.get_funding_rate(symbol)
                    await self.redis.hset(f"market:{symbol}", "funding_rate", str(rate))
                    # Alert if funding rate is extreme
                    if abs(rate) > 0.001:  # > 0.1%
                        await self._log_risk_event(
                            "extreme_funding",
                            f"{symbol} funding rate: {rate:.4%}",
                        )
                except Exception as e:
                    logger.error("execution_engine.funding_error", symbol=symbol, error=str(e))
            await asyncio.sleep(300)  # Check every 5 min

    async def _equity_snapshot_loop(self):
        """Take periodic equity snapshots."""
        while self._running:
            try:
                balance = await self.connector.get_account_balance()
                positions = await self.connector.get_positions()

                if self.db_pool:
                    async with self.db_pool.acquire() as conn:
                        await conn.execute(
                            """
                            INSERT INTO equity_snapshots
                                (total_equity, available_balance, unrealized_pnl, num_open_positions)
                            VALUES ($1, $2, $3, $4)
                            """,
                            balance.get("equity", 0),
                            balance.get("available", 0),
                            sum(p.unrealized_pnl for p in positions),
                            len(positions),
                        )

                # Update Redis cache
                await self.redis.hset("account:balance", mapping={
                    "equity": str(balance.get("equity", 0)),
                    "available": str(balance.get("available", 0)),
                    "margin_used": str(balance.get("margin_used", 0)),
                    "positions_count": str(len(positions)),
                })
            except Exception as e:
                logger.error("execution_engine.snapshot_error", error=str(e))
            await asyncio.sleep(60)  # Every minute


# ── Entry Point ───────────────────────────────────────────
async def main():
    engine = ExecutionEngine()

    # Graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(engine.stop()))
        except NotImplementedError:
            pass  # Windows doesn't support signal handlers

    try:
        await engine.start()
    except KeyboardInterrupt:
        await engine.stop()


if __name__ == "__main__":
    asyncio.run(main())
