"""
API Router for configuration endpoints
Allows runtime configuration of API keys and service settings
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["Configuration"])

# Reference to LLM service (set at startup)
llm_service = None


class SetApiKeyRequest(BaseModel):
    """Request to set the Google API key"""
    api_key: str = Field(..., description="Google Generative AI API key", min_length=10)
    model_name: Optional[str] = Field(
        default=None,
        description="Optional: Google model name (e.g. gemini-1.5-flash, gemini-1.5-pro)"
    )


class ConfigStatusResponse(BaseModel):
    """Current configuration status"""
    google_api_key_set: bool
    google_model_name: str
    llm_status: str


class ConfigUpdateResponse(BaseModel):
    """Response after updating configuration"""
    status: str
    message: str
    model_name: str


@router.post("/api-key", response_model=ConfigUpdateResponse)
async def set_api_key(request: SetApiKeyRequest):
    """
    Set or update the Google Generative AI API key at runtime.
    This immediately reconfigures the LLM service without requiring a restart.
    
    - **api_key**: Your Google AI API key (get one at https://aistudio.google.com/apikey)
    - **model_name**: Optional model override (default: gemini-1.5-flash)
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
            model_name=model_name
        )
    except Exception as e:
        logger.error(f"Failed to update API key: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to configure API key: {str(e)}")


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
        google_api_key_set=has_key,
        google_model_name=llm_service.model_name,
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
