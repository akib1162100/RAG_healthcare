from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Vector storage engine
engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Source Odoo data extraction engine
odoo_engine = create_async_engine(settings.ODOO_DATABASE_URL, echo=True)
OdooAsyncSessionLocal = sessionmaker(
    odoo_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_odoo_db():
    async with OdooAsyncSessionLocal() as session:
        yield session
