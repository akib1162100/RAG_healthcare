"""
API Router for configuration endpoints
Allows runtime configuration of API keys and service settings
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging
import json
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["Configuration"])

# Reference to LLM service (set at startup)
llm_service = None


class SetApiKeyRequest(BaseModel):
    """Request to set the Google Generative Language API key"""
    api_key: str = Field(..., description="Google Generative AI API key", min_length=10)
    model_name: Optional[str] = Field(
        default=None,
        description="Optional: Google model name (e.g. gemini-flash-latest, gemma-4-26b-a4b-it)"
    )


class ConfigStatusResponse(BaseModel):
    """Current configuration status"""
    llm_backend: str
    google_api_key_set: bool
    google_model_name: str
    ollama_model_name: Optional[str] = None
    llm_status: str


class ConfigUpdateResponse(BaseModel):
    """Response after updating configuration"""
    status: str
    message: str
    backend: Optional[str] = None
    model_name: Optional[str] = None


class SetLLMConfigRequest(BaseModel):
    """Request to update LLM backend/model selection"""
    backend: Optional[str] = Field(
        default=None,
        description="Optional: auto, google, or local"
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Optional: Google model name"
    )
    ollama_model: Optional[str] = Field(
        default=None,
        description="Optional: local Ollama model name"
    )


class OdooCredentialsRequest(BaseModel):
    odooUrl: str = Field(..., description="Base URL of Odoo, e.g. http://host.docker.internal:8069")
    apiKey: str = Field(..., description="API Key for Odoo Bearer Authentication")

@router.post("/odoo-credentials", response_model=ConfigUpdateResponse)
async def set_odoo_credentials(request: OdooCredentialsRequest):
    """
    Save Odoo credentials dynamically so the ETL pipeline can use them
    instead of relying purely on environment variables.
    """
    try:
        config_path = "/app/odoo_config.json"
        with open(config_path, "w") as f:
            json.dump(request.model_dump(), f, indent=4)
        
        logger.info("Odoo credentials successfully updated and saved to disk.")
        return ConfigUpdateResponse(
            status="success",
            message="Odoo credentials saved successfully. Future ETL syncs will use them."
        )
    except Exception as e:
        logger.error(f"Failed to save Odoo credentials: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")

@router.post("/api-key", response_model=ConfigUpdateResponse)
async def set_api_key(request: SetApiKeyRequest):
    """
    Set or update the Google Generative Language API key at runtime.
    This immediately reconfigures the LLM service without requiring a restart.
    
    - **api_key**: Your Google AI API key (get one at https://aistudio.google.com/apikey)
    - **model_name**: Optional model override (default from GOOGLE_MODEL_NAME)
    """
    if not llm_service:
        raise HTTPException(status_code=503, detail="LLM service not initialized")
    
    try:
        model_name = request.model_name or llm_service.model_name
        await llm_service.update_api_key(request.api_key, model_name)
        
        logger.info(f"API key updated successfully, model: {model_name}")
        
        return ConfigUpdateResponse(
            status="success",
            message="API key configured and LLM model reloaded successfully",
            backend=llm_service.backend,
            model_name=model_name
        )
    except Exception as e:
        logger.error(f"Failed to update API key: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to configure API key: {str(e)}")


@router.post("/llm", response_model=ConfigUpdateResponse)
async def set_llm_config(request: SetLLMConfigRequest):
    """
    Set runtime LLM configuration.

    Use `.env` for persistent startup config. Use this endpoint for temporary
    runtime changes without editing code.
    """
    if not llm_service:
        raise HTTPException(status_code=503, detail="LLM service not initialized")

    if request.backend and request.backend.lower() not in {"auto", "google", "gemini", "gemma", "local"}:
        raise HTTPException(status_code=400, detail="backend must be one of: auto, google, local")

    try:
        await llm_service.update_config(
            backend=request.backend,
            model_name=request.model_name,
            ollama_model=request.ollama_model,
        )
        return ConfigUpdateResponse(
            status="success",
            message="LLM configuration updated successfully",
            backend=llm_service.configured_backend,
            model_name=llm_service.model_name,
        )
    except Exception as e:
        logger.error(f"Failed to update LLM config: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to update LLM config: {str(e)}")


@router.post("/llm-backend", response_model=ConfigUpdateResponse)
async def set_llm_backend_alias(request: SetLLMConfigRequest):
    """Backward-compatible alias used by the Odoo addon settings screen."""
    return await set_llm_config(request)


@router.get("/status", response_model=ConfigStatusResponse)
async def get_config_status():
    """
    Get current configuration status.
    Shows whether API key is set and which model is active.
    """
    if not llm_service:
        raise HTTPException(status_code=503, detail="LLM service not initialized")
    
    has_key = llm_service.api_key_set
    model_ready = llm_service.model is not None
    
    return ConfigStatusResponse(
        llm_backend=llm_service.configured_backend,
        google_api_key_set=has_key,
        google_model_name=llm_service.model_name,
        ollama_model_name=llm_service.ollama_model,
        llm_status="ready" if (has_key and model_ready) else "not configured"
    )

@router.get("/debug-models")
async def get_available_models():
    """List all available models for the currently configured API key."""
    if not llm_service or not llm_service.api_key_set:
        raise HTTPException(status_code=400, detail="API key not set")
    import google.generativeai as genai
    try:
        models = [m.name for m in genai.list_models()]
        return {"models": models}
    except Exception as e:
        return {"error": str(e)}
