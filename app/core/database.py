from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Vector storage engine (internal pgvector database)
engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Note: Odoo data access is exclusively via JSON-RPC API.
# No direct database connection to Odoo is created.

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

