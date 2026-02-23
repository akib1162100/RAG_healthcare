# Project Structure Overview

## Complete Directory Structure

```
RAG_healthcare/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py                    # API router aggregator
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py             # Health check endpoint
│   │           ├── rag.py                # RAG query endpoints
│   │           └── etl.py                # ETL/indexing endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                     # Centralized configuration
│   │   └── database.py                   # Database session management
│   ├── models/
│   │   ├── medical_rag.py                # Legacy (can be removed)
│   │   └── schemas.py                    # Pydantic models (NEW)
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── vector_repository.py          # pgvector operations
│   ├── services/
│   │   ├── __init__.py
│   │   ├── embedding_service.py          # ClinicalBERT (Local)
│   │   ├── llm_service.py                # Google Gemma (External)
│   │   └── rag_service.py                # RAG orchestration
│   ├── etl/                              # ETL pipeline (existing)
│   ├── database.py                       # Legacy (can be removed)
│   ├── rag_engine.py                     # Legacy (can be removed)
│   └── main.py                           # FastAPI application (UPDATED)
├── database/
│   └── init_pgvector.sql
├── .env.example                          # Environment template (UPDATED)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt                      # Dependencies (UPDATED)
└── README.md
```

## Files to Remove (Legacy)

The following files are now deprecated and can be removed:
- `app/database.py` - Replaced by `app/core/database.py`
- `app/rag_engine.py` - Replaced by service layer
- `app/models/medical_rag.py` - Replaced by `app/models/schemas.py`

## Clean Architecture Layers

### 1. API Layer (`app/api/`)
- FastAPI routers and endpoints
- Request/response handling
- Dependency injection

### 2. Service Layer (`app/services/`)
- Business logic
- Orchestration between components
- External API integration

### 3. Repository Layer (`app/repositories/`)
- Database operations
- Data access abstraction

### 4. Core Layer (`app/core/`)
- Configuration management
- Database connection
- Shared utilities

### 5. Models Layer (`app/models/`)
- Pydantic schemas
- Data validation
- Type definitions
