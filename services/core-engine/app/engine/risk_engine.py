"""
╔══════════════════════════════════════════════════════════════╗
║  Institutional Risk Engine                                   ║
║  Capital preservation, dynamic sizing, drawdown control      ║
╚══════════════════════════════════════════════════════════════╝
"""
import asyncio
import os
import structlog

logger = structlog.get_logger()

class InstitutionalRiskEngine:
    def __init__(self):
        self.redis = None
        self.db_pool = None
        self.max_daily_drawdown = float(os.getenv("MAX_DAILY_DRAWDOWN_PCT", "0.05"))
        self.max_portfolio_exposure = float(os.getenv("MAX_PORTFOLIO_EXPOSURE_PCT", "0.30"))

    def set_redis(self, redis_client):
        self.redis = redis_client

    def set_db(self, db_pool):
        self.db_pool = db_pool

    async def validate_signal(self, signal: dict, strategy) -> dict | None:
        """
        Validate a trading signal against hard risk limits.
        If approved, dynamically sizes the position.
        """
        symbol = signal.get("symbol")
        
        # 1. Check Global Kill Switch
        kill_switch = await self.redis.get("risk:kill_switch")
        if kill_switch == "true":
            logger.warning("risk_engine.kill_switch_active", symbol=symbol)
            return None
            
        # 2. Check Daily Drawdown limit
        current_dd = await self.redis.get("risk:daily_drawdown")
        if current_dd and float(current_dd) >= self.max_daily_drawdown:
            logger.warning("risk_engine.max_drawdown_reached", symbol=symbol, dd=current_dd)
            # Auto-fire kill switch
            await self.redis.set("risk:kill_switch", "true")
            await self._log_event("critical", "Max daily drawdown reached. Global kill switch engaged.")
            return None

        # 3. Size the position dynamically
        sized_signal = await self._calculate_position_size(signal, strategy)
        if not sized_signal:
            return None

        return sized_signal

    async def _calculate_position_size(self, signal: dict, strategy) -> dict | None:
        """Calculate position size based on account equity and volatility."""
        account_data = await self.redis.hgetall("account:balance")
        if not account_data:
            return None
            
        equity = float(account_data.get("equity", 0))
        if equity <= 0:
            return None

        # Default fixed percentage risk
        risk_pct = strategy.risk_per_trade
        target_risk_usd = equity * risk_pct
        
        # If stop loss is provided, size based on risk amount
        stop_loss = signal.get("stop_loss")
        entry_price = signal.get("price")  # From signal or market
        
        if stop_loss and entry_price:
            risk_per_unit = abs(entry_price - stop_loss)
            if risk_per_unit > 0:
                qty = target_risk_usd / risk_per_unit
            else:
                qty = (equity * 0.01) / entry_price # fallback
        else:
            # Fallback size
            qty = target_risk_usd / entry_price if entry_price else 0

        # Check max portfolio exposure
        current_used = float(account_data.get("margin_used", 0))
        proposed_notional = qty * entry_price if entry_price else 0
        
        if (current_used + proposed_notional) / equity > self.max_portfolio_exposure:
            logger.warning("risk_engine.max_exposure", symbol=signal.get("symbol"))
            return None

        signal["size"] = round(qty, 4)
        return signal

    async def monitor_risk_loop(self):
        """Continuously monitor portfolio health in background."""
        while True:
            try:
                if self.redis and self.db_pool:
                    # Sync risk settings from Redis (updated by API)
                    settings = await self.redis.get("risk:settings")
                    if settings:
                        import orjson
                        cfg = orjson.loads(settings)
                        self.max_daily_drawdown = cfg.get("max_drawdown_limit", self.max_daily_drawdown)
                        self.max_portfolio_exposure = cfg.get("risk_limit_pct", self.max_portfolio_exposure)

                    # Check for large drawdowns across all open positions
                    account_data = await self.redis.hgetall("account:balance")
                    if account_data:
                        drawdown = float(account_data.get("drawdown_pct", 0))
                        if drawdown >= self.max_daily_drawdown:
                            await self.redis.set("risk:kill_switch", "true")
                            await self._log_event("emergency", f"Emergency Kill Switch: Portfolio drawdown {drawdown}% exceeded limit {self.max_daily_drawdown}%")
                            logger.critical("risk_engine.emergency_shutdown", drawdown=drawdown)
                
                await self.redis.set("service:risk-engine:last_heartbeat", int(asyncio.get_event_loop().time()))
            except Exception as e:
                logger.error("risk_engine.monitor_error", error=str(e))
            await asyncio.sleep(10)

    async def _log_event(self, severity: str, desc: str):
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO risk_events (event_type, severity, description) VALUES ($1, $2, $3)",
                    "drawdown_breach", severity, desc
                )
