"""
LLM Service - Handles Google Gemini API integration for answer generation
Supports two backends:
  local  → Ollama (GPU) via OLLAMA_BASE_URL
  google → Google Gemini API via GOOGLE_API_KEY
"""
import os
import time
import logging
import aiohttp
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for generating answers — Ollama (local GPU) or Google Gemini."""

    def __init__(self):
        self.model = None
        self.model_name = settings.GOOGLE_MODEL_NAME
        self.api_key_set = False

        # Backend selection: 'local' (Ollama), 'google', or 'auto'
        self.configured_backend: str = settings.LLM_BACKEND.lower()
        self.backend: str = self.configured_backend
        self.ollama_model: str = settings.OLLAMA_MODEL
        self.ollama_base_url: str = settings.OLLAMA_BASE_URL

        # Chat session management
        self.chat_sessions: Dict[str, Any] = {}
        self.session_ttl_seconds = int(os.getenv('CHAT_SESSION_TTL_MINUTES', 5)) * 60
        
    async def initialize(self):
        """Initialize the configured LLM backend.
        
        Priority: Google API is the default. Ollama is tried only as a fallback
        when Google cannot initialize, or when backend is explicitly 'local'.
        """
        # Google-first: try Google for 'google', 'gemini', 'gemma', and 'auto'
        if self.configured_backend in ("google", "gemini", "gemma", "auto"):
            if self._configure_google_model():
                return
            logger.warning("Google backend could not initialize; trying Ollama fallback")

        # Ollama fallback (or primary when explicitly 'local')
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(
                    f"{self.ollama_base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as r:
                    if r.status == 200:
                        data = await r.json()
                        models = [m['name'] for m in data.get('models', [])]
                        logger.info(f"Ollama reachable. Available models: {models}")
                        # Pick configured model or first available
                        if self.ollama_model not in models and models:
                            self.ollama_model = models[0]
                            logger.info(f"Switching Ollama model to {self.ollama_model}")
                        self.backend = 'local'
                        logger.info(f"LLM backend = LOCAL Ollama [{self.ollama_model}] at {self.ollama_base_url}")
                        return
        except Exception as e:
            logger.warning(f"Ollama not reachable ({e})")

        # Last resort: try Google if we haven't yet (for 'local' backend that failed)
        if self.configured_backend == "local" and not self.api_key_set:
            logger.warning("Configured local backend failed; attempting Google as last resort")
            self._configure_google_model()

    def _configure_google_model(self) -> bool:
        """Configure the hosted Google model, returning whether it is ready."""
        logger.info(f"Initializing Google Gemini API: {self.model_name}")
        api_key = settings.GOOGLE_API_KEY
        if api_key and api_key != 'your_google_api_key_here':
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.api_key_set = True
                self.backend = 'google'
                logger.info("Google Gemini API initialized successfully")
                return True
            except Exception as e:
                logger.warning(f"Could not initialize Google Gemini API: {e}")
        else:
            logger.info("No Google API key configured. Set one via POST /api/v1/config/api-key")
        return False
    
    async def update_api_key(self, api_key: str, model_name: str = None):
        """Update the API key and reinitialize the model at runtime"""
        if model_name:
            self.model_name = model_name
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)
        self.api_key_set = True
        
        logger.info(f"Google Generative Language API reconfigured with model: {self.model_name}")

    async def update_config(
        self,
        backend: Optional[str] = None,
        model_name: Optional[str] = None,
        ollama_model: Optional[str] = None,
    ) -> None:
        """Update LLM runtime configuration without changing source code."""
        if backend:
            self.configured_backend = backend.lower()
            self.backend = self.configured_backend
        if model_name:
            self.model_name = model_name
        if ollama_model:
            self.ollama_model = ollama_model

        if self.configured_backend in ("google", "gemini", "gemma") and self.api_key_set:
            self.model = genai.GenerativeModel(self.model_name)
            self.backend = "google"
    
    async def generate_answer(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generate an answer using the configured LLM backend.
        Routes to Google Gemini or local Ollama based on self.backend.
        
        Args:
            prompt: User's question
            context: Retrieved context from vector database
            system_instruction: Optional system instruction for the model
            
        Returns:
            Generated answer as string
        """
        # Build the full prompt
        full_prompt = self._build_prompt(prompt, context, system_instruction)
        
        try:
            if self.backend == 'local':
                # Route through Ollama
                messages = [{"role": "user", "content": full_prompt}]
                return await self._ollama_chat(messages, temperature=0.3, max_tokens=2048, json_mode=False)
            else:
                # Route through Google Gemini
                if not self.model:
                    raise RuntimeError("Google Gemini model not initialized. Call initialize() first.")
                response = self.model.generate_content(full_prompt)
                return response.text
            
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
                        fallback = self._select_fallback_model(available_models)
                        
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
        patient_seq: Optional[str] = None,
        chat_history: Optional[list] = None
    ) -> dict:
        """
        Generate an answer using the configured Google Gemini or hosted Gemma model
        with conversation history tracking.
        
        Args:
            session_id: Unique identifier for the user's chat session
            prompt: User's question
            context: Retrieved context from vector database
            system_instruction: Optional system instruction for the model
            reset: If True, wipe the conversation history for this session
            patient_seq: Optional patient sequence for context filtering
            chat_history: Optional list of previous messages from Odoo DB
                         [{"role": "user"/"assistant", "content": "..."}]
            
        Returns:
            Dict with 'text', 'context_preserved', and 'message_count'
        """
        if not self.model:
            raise RuntimeError("LLM model not initialized. Call initialize() first.")
            
        # Clean up stale sessions occasionally
        self._cleanup_sessions()
        
        is_existing_session = (not reset) and (session_id in self.chat_sessions)
        
        # Determine if we have Odoo-provided chat history
        has_odoo_history = bool(chat_history and len(chat_history) > 0)
        
        # Reset or initialize session
        if reset or session_id not in self.chat_sessions:
            if reset and session_id in self.chat_sessions:
                logger.info(f"Resetting chat session: {session_id}")
            
            # Start a brand new underlying Gemini ChatSession
            chat_session = self.model.start_chat(history=[])
            
            self.chat_sessions[session_id] = {
                'chat': chat_session,
                'last_accessed': time.time(),
                'patient_seq': patient_seq,
                'message_count': 0
            }
        elif patient_seq:
            # Update patient_seq if newly provided to an existing session
            self.chat_sessions[session_id]['patient_seq'] = patient_seq
        
        # Build the message to send
        if has_odoo_history:
            # --- Odoo-managed chat history mode ---
            # Prepend the conversation history from Odoo DB as structured context
            parts = []
            
            # System instruction
            if system_instruction:
                parts.append(f"System: {system_instruction}\n")
            else:
                parts.append(
                    "System: You are a medical AI assistant. Answer questions based on the provided "
                    "medical context. Be precise, professional, and cite relevant information from the context. "
                    "If the context doesn't contain enough information, acknowledge this limitation.\n"
                )
            
            # Medical document context
            if context and context != "No relevant context found.":
                parts.append(f"Medical Context:\n{context}\n")
            
            # Previous conversation history
            parts.append("=== Previous Conversation History ===")
            for msg in chat_history:
                role_label = "User" if msg.get('role') == 'user' else "Assistant"
                parts.append(f"{role_label}: {msg.get('content', '')}")
            parts.append("=== End of History ===\n")
            
            # Current question
            parts.append(
                "IMPORTANT: The above shows the previous conversation history. "
                "Reference this history when answering the following new question. "
                "The user may be referring to topics discussed in earlier messages."
            )
            parts.append(f"\nNew Question: {prompt}\n")
            parts.append("Answer (referencing conversation history and medical context):")
            
            message_to_send = "\n".join(parts)
            logger.debug(f"Sending message with {len(chat_history)} Odoo history entries for session {session_id}")
            
        elif is_existing_session:
            # For follow-up messages (no Odoo history, but in-memory session exists),
            # only send new context + question
            parts = []
            parts.append(
                "IMPORTANT: This is a follow-up message in an ongoing conversation. "
                "Reference our previous conversation above when answering. "
                "The user may be referring to topics discussed in earlier messages."
            )
            if context and context != "No relevant context found.":
                parts.append(f"\nAdditional Context:\n{context}\n")
            parts.append(f"Follow-up Question: {prompt}\n")
            parts.append("Answer (referencing our conversation history):")
            message_to_send = "\n".join(parts)
            logger.debug(f"Sending follow-up message to existing session {session_id}")
        else:
            # For new/reset sessions, send the full prompt with system instruction
            message_to_send = self._build_prompt(prompt, context, system_instruction)
            logger.debug(f"Sending initial message to new session {session_id}")
        
        try:
            # Retrieve active session
            session_data = self.chat_sessions[session_id]
            chat_session = session_data['chat']
            
            # Update access time and message count
            session_data['last_accessed'] = time.time()
            session_data['message_count'] = session_data.get('message_count', 0) + 1
            
            # Generate response using the chat object
            # The chat object inherently remembers previous messages
            response = chat_session.send_message(message_to_send)
            
            return {
                'text': response.text,
                'context_preserved': is_existing_session or has_odoo_history,
                'message_count': session_data['message_count']
            }
            
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
                        fallback = self._select_fallback_model(available_models)
                        
                        logger.info(f"Auto-switching from {self.model_name} to allowed fallback model: {fallback}")
                        self.model_name = fallback
                        self.model = genai.GenerativeModel(self.model_name)
                        
                        # Re-run chat with new engine
                        chat_session = self.model.start_chat(history=[])
                        self.chat_sessions[session_id] = {'chat': chat_session, 'last_accessed': time.time(), 'message_count': 1}
                        response = chat_session.send_message(message_to_send)
                        return {
                            'text': response.text,
                            'context_preserved': False,
                            'message_count': 1
                        }
                except Exception as fallback_error:
                    logger.error(f"Fallback generation recursively failed: {fallback_error}")
            
            raise

    async def generate_medical_summary(
        self,
        patient_seq: str,
        context: str,
    ) -> str:
        """
        Generate a structured medical summary JSON for a patient.
        Routes through Ollama (local GPU) or Google Gemini based on self.backend.
        """
        prompt = f"""You are a senior clinical AI assistant. Analyze the following patient medical records and produce a comprehensive medical summary strictly in the JSON format shown below.

PATIENT ID: {patient_seq}

=== PATIENT MEDICAL RECORDS ===
{context}
=== END OF RECORDS ===

Return ONLY a valid JSON object (no markdown fences, no extra text) with this exact structure:

{{
  "allergy_alert": "...",
  "patient_demographics": {{
    "patient_name": "...",
    "date_of_birth_age": "...",
    "contact": "...",
    "presenting_doctor": "...",
    "past_medical_history": "...",
    "gender": "...",
    "hmo_hospital": "...",
    "reg_no": ""
  }},
  "vitals_at_visit": [
    {{"parameter": "...", "recorded_value": "...", "status": "...", "normal_range": "..."}}
  ],
  "chief_complaints": {{
    "primary_complaints": [ "..." ],
    "secondary_background_complaints": [ "..." ]
  }},
  "red_flag_indicators": {{
    "alert_message": "...",
    "cardiology_red_flags": [ "..." ],
    "routine_red_flags": [ "..." ]
  }},
  "diagnoses": [
    {{"diagnosis": "...", "secondary_complication": "...", "icd_10": "...", "snomed": "...", "type": "Primary | Secondary | Rule Out", "specialty": "..."}}
  ],
  "medications_prescribed": {{
    "date": "...",
    "current_medications": [
      {{"medication_drug_name": "...", "dose": "...", "freq": "...", "route": "...", "food": "...", "duration": "...", "qty": "...", "margin": "..."}}
    ],
    "other_historical_medications": [ "..." ]
  }},
  "investigations_ordered": [
    {{"category": "...", "test_panel": "...", "clinical_indication": "..."}}
  ],
  "clinical_decision_mapping": [
    {{"complaint": "...", "time_course": "...", "pattern": "...", "most_likely_dx": "...", "next_action": "..."}}
  ],
  "advise_care_plan": {{
    "lifestyle_diet": [ "..." ],
    "medication_instructions": [ "..." ],
    "warning_signs_seek_care": [ "..." ]
  }},
  "follow_up_monitoring_plan": {{
    "next_visit": "...",
    "signature_status": "...",
    "investigations": "...",
    "referral": "..."
  }}
}}

Instructions:
- Extract ALL data strictly from the patient records. Do NOT invent data.
- If a field has no data available, use null or an empty string "".
- Return ONLY the JSON object. No explanation, no markdown fences.
"""
        try:
            if self.backend == 'local':
                messages = [{"role": "user", "content": prompt}]
                return await self._ollama_chat(messages, temperature=0.1, max_tokens=4096)
            else:
                if not self.model:
                    raise RuntimeError("Google Gemini model not initialized")
                response = self.model.generate_content(prompt)
                return response.text
        except Exception as e:
            logger.error(f"Error generating medical summary for patient {patient_seq}: {e}")
            raise

    async def generate_prescription_details(self, patient_seq: str, context: str, base_details: Optional[dict] = None) -> str:
        """
        Generate a strictly structured single-prescription JSON.
        Routes through Ollama (local GPU) or Google Gemini based on self.backend.
        """
        import json

        base_json = json.dumps(base_details or {}, ensure_ascii=False, indent=2)

        prompt = f"""You are a senior clinical AI assistant. Analyze the single prescription record and produce a detailed 10-section prescription document strictly in JSON format.

PATIENT ID: {patient_seq}

=== PRESCRIPTION RECORD ===
{context}
=== END OF RECORD ===

=== BASELINE STRUCTURED EXTRACTION ===
{base_json}
=== END BASELINE ===

Use the baseline structured extraction as the factual starting point and improve it.
Rules:
- This document must describe ONLY this prescription/visit.
- Preserve all factual data already present in the baseline JSON.
- Improve especially these sections when possible from the prescription data:
  red_flag_indicators, diagnoses, clinical_decision_mapping,
  advise_care_plan, follow_up_monitoring_plan.
- Do NOT invent diagnoses, allergy, or follow-up items that are not supported by the record.
- If a field is missing or not applicable, use "-" or an empty list/object according to schema.
- Return ONLY valid JSON matching the schema exactly.
"""

        try:
            if self.backend == 'local':
                # Ollama path — uses structured output via Pydantic schema
                from app.models.medical_rag import PrescriptionDetailsResponse
                ollama_url = f"{self.ollama_base_url}/api/generate"
                schema = PrescriptionDetailsResponse.model_json_schema()
                payload = {
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": schema
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(ollama_url, json=payload, timeout=aiohttp.ClientTimeout(total=180)) as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                        return data.get("response", "{}")
            else:
                # Google Gemini path
                if not self.model:
                    raise RuntimeError("Google Gemini model not initialized")
                response = self.model.generate_content(prompt)
                return response.text
        except Exception as e:
            logger.error(f"Error generating prescription details for {patient_seq}: {e}")
            raise

    # ─────────────────────────────────────────────────────────────────────────
    # Ollama backend helper
    # ─────────────────────────────────────────────────────────────────────────

    async def _ollama_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = True,
    ) -> str:
        """Send a chat request to local Ollama and return the response text."""
        import aiohttp
        url = f"{self.ollama_base_url}/api/chat"
        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if json_mode:
            payload["format"] = "json"   # enforce valid JSON output
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("message", {}).get("content", "{}")

    async def _google_generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> str:
        """Send messages to Google Gemini and return text."""
        if not self.model:
            raise RuntimeError("Google Gemini model not initialized")
        # Flatten messages into a single prompt string
        prompt = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in messages
        )
        response = self.model.generate_content(prompt)
        return response.text

    # ─────────────────────────────────────────────────────────────────────────
    # MAP PHASE: intermediate chunk summarization
    # ─────────────────────────────────────────────────────────────────────────

    def _select_fallback_model(self, available_models: List[str]) -> str:
        """Prefer the configured model family, then fast Gemini, then any valid model."""
        preferences = []
        if self.model_name.startswith("gemma"):
            preferences.extend(["gemma-4", "gemma-3", "gemma"])
        if self.model_name.startswith("gemini"):
            preferences.extend(["gemini-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini"])
        preferences.extend(["gemini-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemma-4", "gemma-3"])

        for prefix in preferences:
            match = next((m for m in available_models if m.startswith(prefix)), None)
            if match:
                return match
        return available_models[0]

    async def generate_intermediate_chunk(self, patient_seq: str, records_text: str) -> str:
        """
        MAP phase — compress a small batch of raw medical records into a compact,
        factual JSON intermediate. This is NOT the final formatted report; it is
        deliberately terse to keep the Reduce phase prompt small.

        Returns a JSON string with flat key→value lists that the Reduce step merges.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a clinical data extractor. Your ONLY job is to read raw medical "
                    "records and extract every factual data point into a compact JSON object. "
                    "Do NOT format for presentation. Do NOT invent data. "
                    "Return ONLY a valid JSON object with these keys:\n"
                    "{\n"
                    "  \"patient_seq\": \"\",\n"
                    "  \"demographics\": {"
                        "\"patient_name\":\"\",\"date_of_birth_age\":\"\",\"gender\":\"\","
                        "\"contact\":\"\",\"presenting_doctor\":\"\","
                        "\"hmo_hospital\":\"\",\"reg_no\":\"\",\"past_medical_history\":\"\"},\n"
                    "  \"vitals_at_visit\": [{\"parameter\":\"\",\"recorded_value\":\"\",\"status\":\"Normal|High|Low|Critical\",\"normal_range\":\"\"}],\n"
                    "  \"primary_complaints\": [\"...\"],\n"
                    "  \"secondary_complaints\": [\"...\"],\n"
                    "  \"clinical_impression\": \"\",\n"
                    "  \"vitals_indicators\": [{\"symptom_test\":\"\",\"finding_flag\":\"Positive|Negative|Noted|Absent\"}],\n"
                    "  \"labs\": [{\"investigation\":\"\",\"result\":\"\",\"normal_range\":\"\",\"unit\":\"\",\"status\":\"Normal|High|Low|Critical\"}],\n"
                    "  \"medications\": [{\"medication_drug_name\":\"\",\"dose\":\"\",\"freq\":\"\",\"route\":\"\",\"food\":\"\",\"duration\":\"\",\"qty\":\"\",\"amount\":\"\",\"margin\":\"\",\"date\":\"\"}],\n"
                    "  \"history\": [{\"category\":\"\",\"past_plant\":\"\",\"description\":\"\"}],\n"
                    "  \"clinical_record_mapping\": [{\"complaint\":\"\",\"trend_note\":\"\",\"start_date\":\"\",\"end_date\":\"\"}],\n"
                    "  \"care_plan\": [{\"clinical_action\":\"\",\"additional_considerations\":\"\",\"priority_level\":\"High|Medium|Low\",\"next_time\":\"\"}],\n"
                    "  \"follow_up\": [{\"test_name\":\"\",\"frequency\":\"\",\"monitoring_points\":\"\",\"scheduling_date\":\"\"}],\n"
                    "  \"allergies\": [\"...\"]\n"
                    "}\n"
                    "Use empty string for missing fields. Return ONLY the JSON."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Patient ID: {patient_seq}\n\n"
                    f"=== RAW MEDICAL RECORDS ===\n{records_text}\n=== END ==="
                )
            }
        ]
        start = time.time()
        try:
            if self.backend == 'local':
                result = await self._ollama_chat(messages, temperature=0.1, max_tokens=2048)
            else:
                result = await self._google_generate(messages, temperature=0.1, max_tokens=2048)
            logger.info(f"Intermediate chunk generated in {time.time()-start:.2f}s [{self.backend}]")
            return result
        except Exception as e:
            logger.error(f"Error generating intermediate chunk for {patient_seq}: {e}")
            raise

    # ─────────────────────────────────────────────────────────────────────────
    # REDUCE PHASE: merge all intermediate chunks into the final 10-section JSON
    # ─────────────────────────────────────────────────────────────────────────

    async def generate_summary_from_chunks(
        self,
        patient_seq: str,
        chunk_summaries: list,   # list of compact JSON dicts from the Map phase
        loose_records_text: str  # raw text of records not yet in any full chunk
    ) -> str:
        """
        REDUCE phase — merge all intermediate chunk summaries (and any loose new
        records) into the authoritative 10-section clinical summary JSON.

        chunk_summaries: list of dicts produced by generate_intermediate_chunk().
        loose_records_text: raw text of any records that don't yet complete a chunk.
        """
        import json as _json
        chunks_text = _json.dumps(chunk_summaries, indent=2)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior clinical physician and expert medical AI assistant. "
                    "You will receive a list of pre-processed intermediate medical data chunks "
                    "plus any new unsummarized records for a specific patient. "
                    "Your task is to merge ALL of them into ONE comprehensive clinical summary "
                    "matching the HMS hospital report format EXACTLY. "
                    "Return ONLY a valid JSON object — no markdown, no explanation, no code fences.\n\n"
                    "EXACT required schema (field names are fixed — do not rename them):\n"
                    "{\n"
                    "  \"allergy_alert\": \"\",\n"
                    "  \"patient_demographics\": {\n"
                    "    \"patient_name\":\"\", \"date_of_birth_age\":\"\", \"gender\":\"\",\n"
                    "    \"contact\":\"\", \"presenting_doctor\":\"\", \"hmo_hospital\":\"\",\n"
                    "    \"reg_no\":\"\", \"past_medical_history\":\"\", \"patient_id\":\"\"\n"
                    "  },\n"
                    "  \"vitals_at_visit\": [{\"parameter\":\"\",\"recorded_value\":\"\",\"status\":\"Normal|High|Low|Critical\",\"normal_range\":\"\"}],\n"
                    "  \"chief_complaints\": {\n"
                    "    \"primary_complaints\": [\"...\"],\n"
                    "    \"secondary_background_complaints\": [\"...\"],\n"
                    "    \"clinical_impression\": \"\"\n"
                    "  },\n"
                    "  \"vitals_indicators\": [{\"symptom_test\":\"\",\"finding_flag\":\"Positive|Negative|Noted|Absent\"}],\n"
                    "  \"lab_report_mandatory\": [{\"investigation\":\"\",\"result\":\"\",\"normal_range\":\"\",\"unit\":\"\",\"status\":\"Normal|High|Low|Critical\"}],\n"
                    "  \"medications_prescribed\": {\n"
                    "    \"prescription_date\":\"\", \"physician\":\"\", \"diagnosis\":\"\",\n"
                    "    \"current_medications\": [{\n"
                    "      \"medication_drug_name\":\"\",\"dose\":\"\",\"freq\":\"\",\n"
                    "      \"route\":\"Oral|IV|IM|Topical|Inhalation\",\n"
                    "      \"food\":\"Before Food|After Food|With Food|Empty Stomach\",\n"
                    "      \"duration\":\"\",\"qty\":\"\",\"amount\":\"\",\"margin\":\"\"\n"
                    "    }]\n"
                    "  },\n"
                    "  \"medical_history_findings\": [{\"category\":\"Past History|Family History|Surgical History|Allergy|Vaccination|Habit\",\"past_plant\":\"\",\"description\":\"\"}],\n"
                    "  \"clinical_record_mapping\": [{\"complaint\":\"\",\"trend_note\":\"Improving|Worsening|Stationary|Resolved|New\",\"start_date\":\"\",\"end_date\":\"\"}],\n"
                    "  \"suspect_and_care_plan\": [{\"clinical_action\":\"\",\"additional_considerations\":\"\",\"priority_level\":\"High|Medium|Low\",\"next_time\":\"\"}],\n"
                    "  \"follow_up_monitoring_plan\": [{\"test_name\":\"\",\"frequency\":\"Weekly|Monthly|3-Monthly|Annually|As Needed\",\"monitoring_points\":\"\",\"scheduling_date\":\"\"}]\n"
                    "}\n\n"
                    "Rules:\n"
                    "- 'medications_prescribed.current_medications' MUST reflect the MOST RECENT prescription across ALL chunks.\n"
                    "- Merge vitals_at_visit and lab_report_mandatory from all chunks; deduplicate by parameter/investigation name.\n"
                    "- 'allergy_alert': populate only if an allergy is explicitly documented, else leave empty string.\n"
                    "- All field names are FIXED — do not use different names.\n"
                    "- Use empty string for any unavailable field. Never fabricate data.\n"
                    "- Return ONLY the JSON object."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Patient ID: {patient_seq}\n\n"
                    f"=== INTERMEDIATE CHUNK SUMMARIES ===\n{chunks_text}\n\n"
                    + (
                        f"=== ADDITIONAL UNSUMMARIZED RECORDS ===\n{loose_records_text}\n"
                        if loose_records_text.strip() else ""
                    )
                    + "Produce the unified clinical summary JSON now."
                )
            }
        ]
        start = time.time()
        logger.info(f"Reduce: merging {len(chunk_summaries)} chunks [{self.backend}] for {patient_seq}")
        try:
            if self.backend == 'local':
                result = await self._ollama_chat(messages, temperature=0.1, max_tokens=4096)
            else:
                result = await self._google_generate(messages, temperature=0.1, max_tokens=4096)
            logger.info(f"Summary reduce completed in {time.time()-start:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Error in reduce phase for {patient_seq}: {e}")
            raise


    # ─────────────────────────────────────────────────────────────────────────
    # INCREMENTAL ROLL-FORWARD: merge new records into existing summary
    # ─────────────────────────────────────────────────────────────────────────

    async def merge_summary_with_new_records(
        self,
        patient_seq: str,
        existing_summary: dict,
        new_records_text: str,
    ) -> str:
        """
        Incremental roll-forward — merges NEW medical records into an existing
        summary JSON with a single LLM call.  Much cheaper than full Map-Reduce.

        Args:
            patient_seq:      Patient identifier.
            existing_summary: The current rolling summary JSON dict.
            new_records_text: Raw text of records not yet in the summary.

        Returns:
            Updated JSON string with the same schema as the original summary.
        """
        import json as _json

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior clinical physician. You will receive an EXISTING medical "
                    "summary JSON and NEW medical records for the same patient. "
                    "Your job is to UPDATE the existing summary by incorporating the new "
                    "information. Follow these rules:\n\n"
                    "1. Keep ALL existing data intact — do NOT remove anything.\n"
                    "2. ADD new findings to the appropriate sections.\n"
                    "3. If new medications are prescribed, they become 'current_medications'; "
                    "   move previously-current meds to 'other_historical_medications'.\n"
                    "4. Update vitals_at_visit with the latest values.\n"
                    "5. Append new complaints, diagnoses, and investigations.\n"
                    "6. Update follow_up_monitoring_plan with the latest schedule.\n"
                    "7. Preserve the EXACT JSON schema — do not rename any keys.\n"
                    "8. Return ONLY the updated JSON object — no markdown, no explanation.\n"
                    "9. Do NOT invent data. Only add what is explicitly in the new records."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Patient ID: {patient_seq}\n\n"
                    f"=== EXISTING SUMMARY (JSON) ===\n"
                    f"{_json.dumps(existing_summary, indent=2)}\n\n"
                    f"=== NEW RECORDS TO INCORPORATE ===\n"
                    f"{new_records_text}\n\n"
                    "Produce the UPDATED summary JSON now."
                ),
            },
        ]

        start = time.time()
        logger.info(
            f"Roll-forward merge: {len(new_records_text)} chars of new records "
            f"for {patient_seq} [{self.backend}]"
        )
        try:
            if self.backend == "local":
                result = await self._ollama_chat(messages, temperature=0.1, max_tokens=4096)
            else:
                result = await self._google_generate(messages, temperature=0.1, max_tokens=4096)
            logger.info(f"Roll-forward merge completed in {time.time()-start:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Error in roll-forward merge for {patient_seq}: {e}")
            raise
