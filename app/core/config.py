import json
from typing import Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Odoo RAG Healthcare Service"
    APP_VERSION: str = "1.0.0"
    
    # Vector Database Settings (pgvector storage)
    DATABASE_URL: str = "postgresql+asyncpg://odoo:odoo@db:5432/odoo"
    
    # Vector DB Settings
    VECTOR_TABLE_NAME: str = "odoo_medical_embeddings"
    VECTOR_DIMENSION: int = 768  # ClinicalBERT dimension
    
    # Embedding Settings
    EMBEDDING_MODEL_NAME: str = "emilyalsentzer/Bio_ClinicalBERT"
    EMBEDDING_DEVICE: str = "auto"  # 'cuda', 'cpu', or 'auto'
    
    # LLM Settings — default backend is Google API with gemma-4-31b-it
    LLM_BACKEND: str = "google"
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "gemma-medical-4b-m"
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL_NAME: str = "gemma-4-31b-it"
    
    # Odoo JSON-RPC API Settings (all Odoo access via API only)
    ODOO_INSTANCES: str = ""
    ODOO_URL: str = ""
    ODOO_API_KEY: str = ""
    ODOO_DB: str = ""
    
    # Odoo field configuration
    PATIENT_SEQ_FIELD: str = "patient_seq"  # Field name for patient sequence on res.partner

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def get_odoo_instances(self) -> List[Dict[str, str]]:
        if self.ODOO_INSTANCES:
            instances = json.loads(self.ODOO_INSTANCES)
            if not isinstance(instances, list):
                raise ValueError("ODOO_INSTANCES must be a JSON array")
            seen = set()
            normalized = []
            for item in instances:
                if not isinstance(item, dict):
                    raise ValueError("Each ODOO_INSTANCES entry must be an object")
                instance_id = str(item.get("instance_id") or "").strip()
                if not instance_id:
                    raise ValueError("Each ODOO_INSTANCES entry must include instance_id")
                if instance_id in seen:
                    raise ValueError(f"Duplicate Odoo instance_id: {instance_id}")
                seen.add(instance_id)
                normalized.append({
                    "instance_id": instance_id,
                    "url": str(item.get("url") or "").rstrip("/"),
                    "api_key": str(item.get("api_key") or ""),
                    "db": str(item.get("db") or instance_id),
                })
            if normalized:
                return normalized

        default_url = self.ODOO_URL.rstrip("/")
        default_instance_id = self.ODOO_DB or "default"
        if default_url or self.ODOO_API_KEY or self.ODOO_DB:
            return [{
                "instance_id": default_instance_id,
                "url": default_url,
                "api_key": self.ODOO_API_KEY,
                "db": self.ODOO_DB or default_instance_id,
            }]
        return []

    def get_default_odoo_instance(self) -> Dict[str, str]:
        instances = self.get_odoo_instances()
        if not instances:
            return {
                "instance_id": "default",
                "url": self.ODOO_URL.rstrip("/"),
                "api_key": self.ODOO_API_KEY,
                "db": self.ODOO_DB or "default",
            }
        return instances[0]

settings = Settings()
