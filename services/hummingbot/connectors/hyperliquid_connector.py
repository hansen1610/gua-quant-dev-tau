"""
╔══════════════════════════════════════════════════════════════╗
║  Hyperliquid Perpetual Futures Connector                     ║
║  WebSocket real-time data + REST order management            ║
╚══════════════════════════════════════════════════════════════╝
"""
import asyncio
import hashlib
import hmac
import json
import time
from decimal import Decimal
from typing import Any, Callable, Optional

import aiohttp
import structlog
import websockets
from pydantic import BaseModel

logger = structlog.get_logger()

# ── Constants ─────────────────────────────────────────────
MAINNET_API = "https://api.hyperliquid.xyz"
TESTNET_API = "https://api.hyperliquid-testnet.xyz"
MAINNET_WS = "wss://api.hyperliquid.xyz/ws"
TESTNET_WS = "wss://api.hyperliquid-testnet.xyz/ws"


class OrderResult(BaseModel):
    success: bool
    order_id: Optional[str] = None
    filled_price: Optional[float] = None
    filled_qty: Optional[float] = None
    slippage: Optional[float] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None


class PositionInfo(BaseModel):
    symbol: str
    side: str  # "long" | "short"
    size: float
    entry_price: float
    unrealized_pnl: float
    leverage: float
    liquidation_price: Optional[float] = None
    funding_rate: Optional[float] = None


class HyperliquidConnector:
    """
    Production connector for Hyperliquid perpetual futures.
    Supports WebSocket streaming + REST order execution.
    """

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        wallet_address: str = "",
        testnet: bool = True,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.wallet_address = wallet_address
        self.testnet = testnet

        self.base_url = TESTNET_API if testnet else MAINNET_API
        self.ws_url = TESTNET_WS if testnet else MAINNET_WS

        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._ws_callbacks: dict[str, list[Callable]] = {}
        self._running = False
        self._reconnect_delay = 1
        self._max_reconnect_delay = 60

        # Funding rate cache
        self._funding_rates: dict[str, float] = {}
        self._orderbook_cache: dict[str, dict] = {}

    # ── Session Management ────────────────────────────────
    async def connect(self):
        """Initialize HTTP session and WebSocket connection."""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            json_serialize=json.dumps,
        )
        self._running = True
        logger.info("hyperliquid.connected", testnet=self.testnet)

    async def disconnect(self):
        """Gracefully close all connections."""
        self._running = False
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
        logger.info("hyperliquid.disconnected")

    # ── REST API Methods ──────────────────────────────────
    async def _post(self, endpoint: str, payload: dict) -> dict:
        """Send authenticated POST request."""
        start = time.monotonic()
        try:
            async with self._session.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers=self._auth_headers(payload),
            ) as resp:
                latency = int((time.monotonic() - start) * 1000)
                data = await resp.json()
                if resp.status != 200:
                    logger.error("hyperliquid.api_error", status=resp.status, data=data)
                return {**data, "_latency_ms": latency}
        except Exception as e:
            logger.error("hyperliquid.request_failed", error=str(e))
            return {"error": str(e), "_latency_ms": -1}

    async def _info_post(self, payload: dict) -> dict:
        """Send info request (no auth required)."""
        try:
            async with self._session.post(
                f"{self.base_url}/info", json=payload
            ) as resp:
                return await resp.json()
        except Exception as e:
            logger.error("hyperliquid.info_failed", error=str(e))
            return {"error": str(e)}

    def _auth_headers(self, payload: dict) -> dict:
        """Generate authentication headers."""
        if not self.api_key:
            return {}
        timestamp = str(int(time.time() * 1000))
        message = json.dumps(payload, separators=(",", ":")) + timestamp
        signature = hmac.new(
            self.api_secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
        }

    # ── Market Data ───────────────────────────────────────
    async def get_market_data(self, symbol: str) -> dict:
        """Get current market data for a symbol."""
        data = await self._info_post({"type": "metaAndAssetCtxs"})
        if "error" in data:
            return data
        try:
            universe = data[0]["universe"]
            ctxs = data[1]
            for i, asset in enumerate(universe):
                if asset["name"] == symbol:
                    ctx = ctxs[i]
                    return {
                        "symbol": symbol,
                        "mark_price": float(ctx.get("markPx", 0)),
                        "mid_price": float(ctx.get("midPx", 0)),
                        "funding_rate": float(ctx.get("funding", 0)),
                        "open_interest": float(ctx.get("openInterest", 0)),
                        "volume_24h": float(ctx.get("dayNtlVlm", 0)),
                    }
        except (KeyError, IndexError, TypeError) as e:
            logger.error("hyperliquid.parse_error", error=str(e))
        return {"error": f"Symbol {symbol} not found"}

    async def get_orderbook(self, symbol: str, depth: int = 20) -> dict:
        """Get L2 orderbook."""
        data = await self._info_post({"type": "l2Book", "coin": symbol})
        if "error" in data:
            return data
        try:
            levels = data.get("levels", [[], []])
            bids = [{"price": float(b["px"]), "size": float(b["sz"])} for b in levels[0][:depth]]
            asks = [{"price": float(a["px"]), "size": float(a["sz"])} for a in levels[1][:depth]]
            return {"symbol": symbol, "bids": bids, "asks": asks}
        except (KeyError, TypeError) as e:
            return {"error": str(e)}

    async def get_funding_rate(self, symbol: str) -> float:
        """Get current funding rate."""
        data = await self.get_market_data(symbol)
        return data.get("funding_rate", 0.0)

    async def get_candles(
        self, symbol: str, interval: str = "1h", limit: int = 500
    ) -> list[dict]:
        """Get historical candle data."""
        end_time = int(time.time() * 1000)
        interval_ms = {
            "1m": 60_000, "5m": 300_000, "15m": 900_000,
            "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000,
        }
        ms = interval_ms.get(interval, 3_600_000)
        start_time = end_time - (limit * ms)

        data = await self._info_post({
            "type": "candleSnapshot",
            "req": {"coin": symbol, "interval": interval, "startTime": start_time, "endTime": end_time},
        })
        if isinstance(data, list):
            return [
                {
                    "timestamp": c.get("t", 0),
                    "open": float(c.get("o", 0)),
                    "high": float(c.get("h", 0)),
                    "low": float(c.get("l", 0)),
                    "close": float(c.get("c", 0)),
                    "volume": float(c.get("v", 0)),
                }
                for c in data
            ]
        return []

    # ── Order Execution ───────────────────────────────────
    async def place_order(
        self,
        symbol: str,
        side: str,  # "buy" | "sell"
        size: float,
        price: Optional[float] = None,
        order_type: str = "market",
        reduce_only: bool = False,
        leverage: int = 1,
    ) -> OrderResult:
        """Place an order on Hyperliquid perps."""
        start = time.monotonic()
        try:
            # Get current price for slippage calculation
            market = await self.get_market_data(symbol)
            if "error" in market:
                return OrderResult(success=False, error=market["error"])

            ref_price = market["mid_price"]

            # Build order action
            is_buy = side.lower() == "buy"
            if order_type == "market":
                # Market order: use aggressive limit with slippage tolerance
                slippage_bps = 10  # 0.1% slippage tolerance
                if is_buy:
                    limit_px = round(ref_price * (1 + slippage_bps / 10000), 6)
                else:
                    limit_px = round(ref_price * (1 - slippage_bps / 10000), 6)
                order_spec = {
                    "limit": {"tif": "Ioc"},
                }
            else:
                limit_px = price or ref_price
                order_spec = {
                    "limit": {"tif": "Gtc"},
                }

            action = {
                "type": "order",
                "orders": [
                    {
                        "a": self._symbol_to_index(symbol),
                        "b": is_buy,
                        "p": str(limit_px),
                        "s": str(size),
                        "r": reduce_only,
                        "t": order_spec,
                    }
                ],
                "grouping": "na",
            }

            result = await self._post("/exchange", {
                "action": action,
                "nonce": int(time.time() * 1000),
                "signature": "",  # Simplified; real impl uses eth_account signing
                "vaultAddress": None,
            })

            latency = int((time.monotonic() - start) * 1000)

            if "error" in result:
                return OrderResult(
                    success=False, error=result["error"], latency_ms=latency
                )

            # Parse response
            statuses = result.get("response", {}).get("data", {}).get("statuses", [])
            if statuses and "filled" in statuses[0]:
                filled = statuses[0]["filled"]
                filled_price = float(filled.get("avgPx", 0))
                slippage = abs(filled_price - ref_price) / ref_price if ref_price else 0
                return OrderResult(
                    success=True,
                    order_id=filled.get("oid", ""),
                    filled_price=filled_price,
                    filled_qty=float(filled.get("totalSz", 0)),
                    slippage=round(slippage, 6),
                    latency_ms=latency,
                )
            elif statuses and "resting" in statuses[0]:
                resting = statuses[0]["resting"]
                return OrderResult(
                    success=True,
                    order_id=resting.get("oid", ""),
                    latency_ms=latency,
                )
            else:
                return OrderResult(
                    success=False,
                    error=f"Unexpected response: {statuses}",
                    latency_ms=latency,
                )

        except Exception as e:
            latency = int((time.monotonic() - start) * 1000)
            logger.error("hyperliquid.order_failed", error=str(e))
            return OrderResult(success=False, error=str(e), latency_ms=latency)

    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an open order."""
        action = {
            "type": "cancel",
            "cancels": [{"a": self._symbol_to_index(symbol), "o": int(order_id)}],
        }
        result = await self._post("/exchange", {
            "action": action,
            "nonce": int(time.time() * 1000),
            "signature": "",
        })
        return "error" not in result

    async def close_position(self, symbol: str) -> OrderResult:
        """Close entire position for a symbol."""
        positions = await self.get_positions()
        for pos in positions:
            if pos.symbol == symbol:
                side = "sell" if pos.side == "long" else "buy"
                return await self.place_order(
                    symbol=symbol,
                    side=side,
                    size=abs(pos.size),
                    order_type="market",
                    reduce_only=True,
                )
        return OrderResult(success=False, error="No open position found")

    # ── Position Management ───────────────────────────────
    async def get_positions(self) -> list[PositionInfo]:
        """Get all open positions."""
        if not self.wallet_address:
            return []
        data = await self._info_post({
            "type": "clearinghouseState",
            "user": self.wallet_address,
        })
        if "error" in data:
            return []
        positions = []
        for pos in data.get("assetPositions", []):
            p = pos.get("position", {})
            size = float(p.get("szi", 0))
            if size == 0:
                continue
            positions.append(PositionInfo(
                symbol=p.get("coin", ""),
                side="long" if size > 0 else "short",
                size=abs(size),
                entry_price=float(p.get("entryPx", 0)),
                unrealized_pnl=float(p.get("unrealizedPnl", 0)),
                leverage=float(p.get("leverage", {}).get("value", 1)),
                liquidation_price=float(p.get("liquidationPx", 0)) if p.get("liquidationPx") else None,
            ))
        return positions

    async def get_account_balance(self) -> dict:
        """Get account balance and equity."""
        if not self.wallet_address:
            return {"equity": 0, "available": 0, "margin_used": 0}
        data = await self._info_post({
            "type": "clearinghouseState",
            "user": self.wallet_address,
        })
        if "error" in data:
            return {"equity": 0, "available": 0, "margin_used": 0}
        margin = data.get("marginSummary", {})
        return {
            "equity": float(margin.get("accountValue", 0)),
            "available": float(margin.get("totalRawUsd", 0)),
            "margin_used": float(margin.get("totalMarginUsed", 0)),
        }

    # ── WebSocket Streaming ───────────────────────────────
    async def start_ws(self):
        """Start WebSocket connection with auto-reconnect."""
        while self._running:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self._ws = ws
                    self._reconnect_delay = 1
                    logger.info("hyperliquid.ws_connected")
                    async for message in ws:
                        await self._handle_ws_message(json.loads(message))
            except websockets.exceptions.ConnectionClosed:
                logger.warning("hyperliquid.ws_disconnected")
            except Exception as e:
                logger.error("hyperliquid.ws_error", error=str(e))

            if self._running:
                logger.info("hyperliquid.ws_reconnecting", delay=self._reconnect_delay)
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, self._max_reconnect_delay
                )

    async def subscribe_trades(self, symbol: str, callback: Callable):
        """Subscribe to real-time trade feed."""
        self._ws_callbacks.setdefault(f"trades:{symbol}", []).append(callback)
        if self._ws:
            await self._ws.send(json.dumps({
                "method": "subscribe",
                "subscription": {"type": "trades", "coin": symbol},
            }))

    async def subscribe_orderbook(self, symbol: str, callback: Callable):
        """Subscribe to real-time orderbook updates."""
        self._ws_callbacks.setdefault(f"l2Book:{symbol}", []).append(callback)
        if self._ws:
            await self._ws.send(json.dumps({
                "method": "subscribe",
                "subscription": {"type": "l2Book", "coin": symbol},
            }))

    async def subscribe_user_events(self, callback: Callable):
        """Subscribe to user-specific order/position updates."""
        if not self.wallet_address:
            return
        self._ws_callbacks.setdefault("userEvents", []).append(callback)
        if self._ws:
            await self._ws.send(json.dumps({
                "method": "subscribe",
                "subscription": {"type": "userEvents", "user": self.wallet_address},
            }))

    async def _handle_ws_message(self, data: dict):
        """Route WebSocket messages to registered callbacks."""
        channel = data.get("channel", "")
        msg_data = data.get("data", {})

        for key, callbacks in self._ws_callbacks.items():
            if channel and key.startswith(channel):
                for cb in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(cb):
                            await cb(msg_data)
                        else:
                            cb(msg_data)
                    except Exception as e:
                        logger.error("hyperliquid.ws_callback_error", error=str(e))

    # ── Utilities ─────────────────────────────────────────
    _symbol_index_cache: dict = {}

    def _symbol_to_index(self, symbol: str) -> int:
        """Convert symbol name to Hyperliquid asset index."""
        known = {
            "BTC": 0, "ETH": 1, "SOL": 2, "ARB": 3, "DOGE": 4,
            "AVAX": 5, "MATIC": 6, "OP": 7, "APT": 8, "INJ": 9,
        }
        clean = symbol.replace("-USD", "").replace("-USDC", "").upper()
        return known.get(clean, 0)
