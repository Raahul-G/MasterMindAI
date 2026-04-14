from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pgvector.asyncpg import register_vector
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    connect_args={"statement_cache_size": 0},
)


async def _try_register_vector(conn):
    try:
        await register_vector(conn)
    except Exception:
        pass  # pgvector extension not installed — graph endpoints will fail, but others work


@event.listens_for(engine.sync_engine, "connect")
def on_connect(dbapi_conn, _):
    dbapi_conn.run_async(_try_register_vector)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
