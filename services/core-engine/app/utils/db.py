import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def create_db_pool():
    return await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "quantbot"),
        user=os.getenv("POSTGRES_USER", "quantbot_user"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        min_size=1,
        max_size=5,
    )
