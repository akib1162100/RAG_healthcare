"""
API v1 Router - Aggregates all v1 endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import health, rag, etl, config

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router)
api_router.include_router(rag.router)
api_router.include_router(etl.router)
api_router.include_router(config.router)
