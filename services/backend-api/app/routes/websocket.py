"""
╔══════════════════════════════════════════════════════════════╗
║  WebSocket Routes — Real-time Dashboard Feed                 ║
║  Streams equity, positions, trades, and risk metrics         ║
╚══════════════════════════════════════════════════════════════╝
"""
import asyncio
import json

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = structlog.get_logger()
router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("ws.client_connected", total=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("ws.client_disconnected", total=len(self.active_connections))

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.active_connections.remove(conn)


manager = ConnectionManager()


@router.websocket("/dashboard")
async def dashboard_feed(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard data.
    Streams: equity updates, positions, risk metrics, trade signals.
    """
    await manager.connect(websocket)

    redis = websocket.app.state.redis
    db = websocket.app.state.pool

    try:
        # Start two concurrent tasks:
        # 1. Periodic data push (polling Redis/DB)
        # 2. Listen for client commands
        await asyncio.gather(
            _stream_dashboard_data(websocket, redis, db),
            _listen_client_messages(websocket),
        )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("ws.error", error=str(e))
        manager.disconnect(websocket)


async def _stream_dashboard_data(websocket: WebSocket, redis, db):
    """Push real-time data to the client every 2 seconds."""
    import random
    while True:
        try:
            import os
            demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"

            # 1. Account / Equity data
            if redis and not demo_mode:
                account = await redis.hgetall("account:balance") or {}
                daily_dd = await redis.get("risk:daily_drawdown") or "0"
                kill_switch = await redis.get("risk:kill_switch") or "false"
            else:
                # Demo Mode data
                account = {
                    "equity": 100000 + random.random() * 200, 
                    "available": 85000, 
                    "margin_used": 15000, 
                    "positions_count": 2
                }
                daily_dd = "0.45"
                kill_switch = "false"

            equity_data = {
                "type": "equity_update",
                "data": {
                    "equity": float(account.get("equity", 0)),
                    "available": float(account.get("available", 0)),
                    "margin_used": float(account.get("margin_used", 0)),
                    "positions_count": int(account.get("positions_count", 0)),
                    "drawdown_pct": float(daily_dd),
                    "kill_switch": kill_switch == "true",
                },
            }
            await websocket.send_json(equity_data)

            # 2. Open positions
            pos_list = []
            if db and not demo_mode:
                async with db.acquire() as conn:
                    positions = await conn.fetch(
                        """
                        SELECT p.*, a.symbol 
                        FROM positions p
                        JOIN assets a ON p.asset_id = a.id
                        WHERE p.status = 'open' 
                        ORDER BY p.opened_at DESC
                        """
                    )
                    for p in positions:
                        pos_list.append({
                            "id": str(p["id"]),
                            "symbol": p["symbol"],
                            "side": p["side"],
                            "size": float(p["quantity"]),
                            "entry_price": float(p["entry_price"]),
                            "current_price": float(p["current_price"] or p["entry_price"]),
                            "unrealized_pnl": float(p["unrealized_pnl"] or 0),
                            "stop_loss": float(p["stop_loss"]) if p["stop_loss"] else None,
                            "take_profit": float(p["take_profit"]) if p["take_profit"] else None,
                        })
            else:
                pos_list = [
                    {"id": "m1", "symbol": "BTC-USD", "side": "long", "size": 0.5, "entry_price": 63000, "current_price": 63500 + random.random()*100, "unrealized_pnl": 250, "stop_loss": 60000, "take_profit": 70000},
                    {"id": "m2", "symbol": "ETH-USD", "side": "short", "size": 5.0, "entry_price": 3500, "current_price": 3450 - random.random()*10, "unrealized_pnl": 250, "stop_loss": 3600, "take_profit": 3200}
                ]
            
            await websocket.send_json({ "type": "positions_update", "data": pos_list })

            # 3. Service health summary
            services = ["hummingbot", "strategy-engine", "backend-api", "ml-engine", "quant-research"]
            health_data = {}
            for svc in services:
                if redis:
                    h = await redis.hgetall(f"health:{svc}")
                    health_data[svc] = h.get("status", "unknown") if h else "healthy" # default to healthy for demo
                else:
                    health_data[svc] = "healthy"

            await websocket.send_json({ "type": "health_update", "data": health_data })

        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error("ws.stream_error", error=str(e))

        await asyncio.sleep(2)


async def _listen_client_messages(websocket: WebSocket):
    """Listen for commands from the frontend (e.g., subscribe to specific symbols)."""
    while True:
        try:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "ping":
                await websocket.send_json({"type": "pong"})

            elif action == "subscribe_trades":
                # Could implement per-symbol subscriptions here
                symbol = data.get("symbol")
                logger.info("ws.subscribe_trades", symbol=symbol)

        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error("ws.listen_error", error=str(e))
            break
