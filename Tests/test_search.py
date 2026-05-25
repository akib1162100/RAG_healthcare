import asyncio
import os
import google.generativeai as genai
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.repositories.vector_repository import VectorRepository
from app.core.config import settings
from unittest.mock import AsyncMock

async def test_search():
    engine = create_async_engine(os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/rag_healthcare'))
    async with engine.connect() as conn:
        repo = VectorRepository(conn)
        
        # Test with dummy embedding vector (768 dimensions of 0.1)
        dummy_embedding = [0.1] * 768
        
        try:
            results = await repo.search_similar(
                query_embedding=dummy_embedding,
                limit=5,
                metadata_filter={'patient_seq': '20250700224002'}
            )
            print(f"search_similar returned {len(results)} records")
        except Exception as e:
            print(f"search_similar failed: {e}")
            
    await engine.dispose()
    
    # Check Gemini models
    try:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print("Available generative models:", models)
    except Exception as e:
        print("Model list failed:", e)

asyncio.run(test_search())
