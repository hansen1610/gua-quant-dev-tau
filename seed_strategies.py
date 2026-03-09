
import asyncio
import os
import json
import asyncpg
from uuid import uuid4

# Database connection info from .env logic
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "quantbot"
POSTGRES_USER = "quantbot_user"
POSTGRES_PASSWORD = "change_me_strong_password_here"

STRATEGIES = [
    {
        "name": "EMA Trend Cluster",
        "type": "trend_follow",
        "risk_per_trade": 0.01,
        "parameters": {
            "fast_ema": 21,
            "slow_ema": 90,
            "volume_filter": True,
            "timeframe": "15m"
        }
    },
    {
        "name": "Fibonacci Pullback Cluster",
        "type": "mean_reversion",
        "risk_per_trade": 0.015,
        "parameters": {
            "levels": [0.382, 0.5, 0.618],
            "entry_level": 0.618,
            "stop_loss_level": 0.786,
            "timeframe": "1h"
        }
    },
    {
        "name": "Multi-Timeframe Cluster",
        "type": "multi_timeframe",
        "risk_per_trade": 0.02,
        "parameters": {
            "htf": "1h",
            "ltf": "15m",
            "trend_indicator": "ema_alignment"
        }
    },
    {
        "name": "Regime Detection Cluster",
        "type": "adaptive",
        "risk_per_trade": 0.01,
        "parameters": {
            "adx_threshold": 25,
            "atr_multiplier": 2.0,
            "mode": "auto_switch"
        }
    }
]

async def seed():
    try:
        conn = await asyncpg.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
        )
        
        print("Connected to database. Seeding strategies...")
        
        # Check if already seeded
        count = await conn.fetchval("SELECT count(*) FROM strategies")
        if count > 0:
            print(f"Database already has {count} strategies. Skipping seed.")
            await conn.close()
            return

        for s in STRATEGIES:
            await conn.execute(
                """
                INSERT INTO strategies (id, name, type, parameters, risk_per_trade, is_enabled)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                uuid4(),
                s["name"],
                s["type"],
                json.dumps(s["parameters"]),
                s["risk_per_trade"],
                True # Start enabled for demo
            )
            print(f"Inserted: {s['name']}")
            
        await conn.close()
        print("Seeding complete.")
    except Exception as e:
        print(f"Error seeding database: {e}")

if __name__ == "__main__":
    asyncio.run(seed())
