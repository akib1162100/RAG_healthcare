from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Odoo RAG Healthcare Service"
    APP_VERSION: str = "1.0.0"
    
    # Vector Database Settings (pgvector storage)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://odoo:odoo@db:5432/odoo")
    
    # Source Odoo Database Settings (for ETL extraction)
    ODOO_DATABASE_URL: str = os.getenv("ODOO_DATABASE_URL", "postgresql+asyncpg://odoo:odoo@host.docker.internal:5432/odoo")
    
    # Vector DB Settings
    VECTOR_TABLE_NAME: str = "odoo_medical_embeddings"
    VECTOR_DIMENSION: int = 768  # ClinicalBERT dimension
    
    # Embedding Settings
    EMBEDDING_MODEL_NAME: str = "emilyalsentzer/Bio_ClinicalBERT"
    
    # LLM Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_MODEL_NAME: str = "gemini-1.5-flash"  # or gemma-2-9b if available
    
    # Odoo Settings
    ODOO_URL: str = os.getenv("ODOO_URL", "")
    ODOO_DB: str = os.getenv("ODOO_DB", "")
    ODOO_USER: str = os.getenv("ODOO_USER", "")
    ODOO_PASSWORD: str = os.getenv("ODOO_PASSWORD", "")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
