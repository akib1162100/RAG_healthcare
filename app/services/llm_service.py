"""
LLM Service - Handles Google Gemma API integration for answer generation
"""
import os
import time
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for generating answers using Google Gemma (External API)"""
    
    def __init__(self):
        self.model = None
        self.model_name = settings.GOOGLE_MODEL_NAME
        self.api_key_set = False
        
        # Chat session management
        self.chat_sessions: Dict[str, Any] = {}
        # Default TTL of 4 minutes in seconds
        self.session_ttl_seconds = int(os.getenv('CHAT_SESSION_TTL_MINUTES', 4)) * 60
        
    async def initialize(self):
        """Initialize Google Gemma API (tolerates missing key for later configuration)"""
        logger.info(f"Initializing Google Gemma API: {self.model_name}")
        
        api_key = settings.GOOGLE_API_KEY
        if api_key and api_key != 'your_google_api_key_here':
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.api_key_set = True
                logger.info("Google Gemma API initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize Google Gemma API: {e}")
                logger.info("LLM will be available once a valid API key is set via /api/v1/config/api-key")
        else:
            logger.info("No Google API key configured. Set one via POST /api/v1/config/api-key")
    
    async def update_api_key(self, api_key: str, model_name: str = None):
        """Update the API key and reinitialize the model at runtime"""
        if model_name:
            self.model_name = model_name
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)
        self.api_key_set = True
        
        logger.info(f"Google Gemma API reconfigured with model: {self.model_name}")
    
    async def generate_answer(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generate an answer using Google Gemma
        
        Args:
            prompt: User's question
            context: Retrieved context from vector database
            system_instruction: Optional system instruction for the model
            
        Returns:
            Generated answer as string
        """
        if not self.model:
            raise RuntimeError("LLM model not initialized. Call initialize() first.")
        
        # Build the full prompt
        full_prompt = self._build_prompt(prompt, context, system_instruction)
        
        try:
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            # Extract text from response
            answer = response.text
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            
            if "404" in str(e) or "not found" in str(e).lower():
                try:
                    logger.warning(f"Model {self.model_name} not available. Attempting fallback retrieval...")
                    import google.generativeai as genai
                    
                    available_models = [
                        m.name.replace('models/', '') 
                        for m in genai.list_models() 
                        if 'generateContent' in m.supported_generation_methods
                    ]
                    
                    if available_models:
                        fallback = next((m for m in available_models if "gemini-1.5" in m), available_models[0])
                        
                        logger.info(f"Auto-switching to allowed fallback model: {fallback}")
                        self.model_name = fallback
                        self.model = genai.GenerativeModel(self.model_name)
                        
                        return self.model.generate_content(full_prompt).text
                except Exception as fallback_error:
                    logger.error(f"Fallback generation recursively failed: {fallback_error}")
            
            raise
    
    def _build_prompt(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Build the complete prompt for the LLM
        
        Args:
            prompt: User's question
            context: Retrieved context
            system_instruction: System instruction
            
        Returns:
            Complete prompt string
        """
        parts = []
        
        # Add system instruction if provided
        if system_instruction:
            parts.append(f"System: {system_instruction}\n")
        else:
            # Default medical system instruction
            parts.append(
                "System: You are a medical AI assistant. Answer questions based on the provided "
                "medical context. Be precise, professional, and cite relevant information from the context. "
                "If the context doesn't contain enough information, acknowledge this limitation.\n"
            )
        
        # Add context if provided
        if context:
            parts.append(f"Context:\n{context}\n")
        
        # Add user question
        parts.append(f"Question: {prompt}\n")
        parts.append("Answer:")
        
        return "\n".join(parts)
    
    async def generate_streaming_answer(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_instruction: Optional[str] = None
    ):
        """
        Generate a streaming answer (for future implementation)
        
        Args:
            prompt: User's question
            context: Retrieved context
            system_instruction: System instruction
            
        Yields:
            Chunks of the generated answer
        """
        if not self.model:
            raise RuntimeError("LLM model not initialized. Call initialize() first.")
        
        full_prompt = self._build_prompt(prompt, context, system_instruction)
        
        try:
            response = self.model.generate_content(full_prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Error in streaming generation: {str(e)}")
            raise
            
    def _cleanup_sessions(self):
        """Remove chat sessions that have exceeded their TTL"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_data in self.chat_sessions.items():
            if current_time - session_data['last_accessed'] > self.session_ttl_seconds:
                expired_sessions.append(session_id)
                
        for session_id in expired_sessions:
            logger.debug(f"Cleaning up expired chat session: {session_id}")
            del self.chat_sessions[session_id]
            
    async def generate_chat_answer(
        self,
        session_id: str,
        prompt: str,
        context: Optional[str] = None,
        system_instruction: Optional[str] = None,
        reset: bool = False,
        patient_seq: Optional[str] = None
    ) -> str:
        """
        Generate an answer using Google Gemma with conversation history tracking
        
        Args:
            session_id: Unique identifier for the user's chat session
            prompt: User's question
            context: Retrieved context from vector database
            system_instruction: Optional system instruction for the model
            reset: If True, wipe the conversation history for this session
            
        Returns:
            Generated answer as string
        """
        if not self.model:
            raise RuntimeError("LLM model not initialized. Call initialize() first.")
            
        # Clean up stale sessions occasionally
        self._cleanup_sessions()
        
        # Build the message content (context + prompt)
        full_prompt = self._build_prompt(prompt, context, system_instruction)
        
        # Reset or initialize session
        if reset or session_id not in self.chat_sessions:
            if reset and session_id in self.chat_sessions:
                logger.info(f"Resetting chat session: {session_id}")
            
            # Start a brand new underlying Gemini ChatSession
            chat_session = self.model.start_chat(history=[])
            
            self.chat_sessions[session_id] = {
                'chat': chat_session,
                'last_accessed': time.time(),
                'patient_seq': patient_seq
            }
        elif patient_seq:
            # Update patient_seq if newly provided to an existing session
            self.chat_sessions[session_id]['patient_seq'] = patient_seq
        
        try:
            # Retrieve active session
            session_data = self.chat_sessions[session_id]
            chat_session = session_data['chat']
            
            # Update access time
            session_data['last_accessed'] = time.time()
            
            # Generate response asynchronously using the chat object
            # Note: The chat object inherently remembers previous messages
            response = chat_session.send_message(full_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error in chat generation for session {session_id}: {str(e)}")
            
            # Detect 404 Model Not Found and attempt self-healing
            if "404" in str(e) or "not found" in str(e).lower():
                try:
                    logger.warning(f"Model {self.model_name} not available. Attempting fallback retrieval...")
                    import google.generativeai as genai
                    
                    available_models = [
                        m.name.replace('models/', '') 
                        for m in genai.list_models() 
                        if 'generateContent' in m.supported_generation_methods
                    ]
                    
                    if available_models:
                        # Try to find a gemini-1.5 model, otherwise pick the first available generative model
                        fallback = next((m for m in available_models if "gemini-1.5" in m), available_models[0])
                        
                        logger.info(f"Auto-switching from {self.model_name} to allowed fallback model: {fallback}")
                        self.model_name = fallback
                        self.model = genai.GenerativeModel(self.model_name)
                        
                        # Re-run chat with new engine
                        chat_session = self.model.start_chat(history=[])
                        self.chat_sessions[session_id] = {'chat': chat_session, 'last_accessed': time.time()}
                        response = chat_session.send_message(full_prompt)
                        return response.text
                except Exception as fallback_error:
                    logger.error(f"Fallback generation recursively failed: {fallback_error}")
            
            raise
