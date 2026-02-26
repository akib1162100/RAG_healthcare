"""
RAG Service - Orchestrates Retrieval-Augmented Generation
"""
import logging
from typing import List, Dict, Any, Optional
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.repositories.vector_repository import VectorRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class RAGService:
    """Service for orchestrating RAG pipeline: Embed -> Retrieve -> Generate"""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        llm_service: LLMService
    ):
        self.embedding_service = embedding_service
        self.llm_service = llm_service
    
    async def query(
        self,
        prompt: str,
        session: AsyncSession,
        limit: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute RAG query: embed question, retrieve context, generate answer
        
        Args:
            prompt: User's question
            session: Database session
            limit: Number of similar documents to retrieve
            metadata_filter: Optional filters for retrieval
            system_instruction: Optional system instruction for LLM
            
        Returns:
            Dict with response, sources, and metadata
        """
        logger.info(f"RAG query: {prompt[:100]}...")
        
        # Step 1: Generate embedding for the query (Local ClinicalBERT)
        query_embedding = await self.embedding_service.generate_embedding(prompt)
        logger.debug(f"Generated query embedding (dim={len(query_embedding)})")
        
        # Step 2: Retrieve similar documents from vector DB
        vector_repo = VectorRepository(session)
        similar_docs = await vector_repo.search_similar(
            query_embedding=query_embedding,
            limit=limit,
            metadata_filter=metadata_filter
        )
        logger.debug(f"Retrieved {len(similar_docs)} similar documents")
        
        # Step 3: Build context from retrieved documents
        context = self._build_context(similar_docs)
        
        # Step 4: Generate answer using Google Gemma (External API)
        # Gracefully handle LLM failures (e.g. invalid API key)
        try:
            answer = await self.llm_service.generate_answer(
                prompt=prompt,
                context=context,
                system_instruction=system_instruction
            )
            logger.info("Answer generated successfully")
        except Exception as llm_error:
            logger.warning(f"LLM generation failed: {llm_error}")
            answer = (
                f"[LLM unavailable - showing retrieved medical context]\n\n"
                f"Found {len(similar_docs)} relevant medical records:\n\n"
                f"{context}"
            )
        
        # Step 5: Format response
        sources = [
            {
                'content': doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content'],
                'metadata': doc['metadata'],
                'similarity': doc['similarity']
            }
            for doc in similar_docs
        ]
        
        return {
            'response': answer,
            'sources': sources,
            'metadata': {
                'num_sources': len(similar_docs),
                'filters_applied': metadata_filter or {}
            }
        }
    
    async def chat(
        self,
        prompt: str,
        session_id: str,
        session: AsyncSession,
        reset: bool = False,
        limit: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
        system_instruction: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Execute Conversational RAG query: embed question, retrieve context, append to session history
        
        Args:
            prompt: User's question
            session_id: Unique identifier for the conversation session
            session: Database session
            reset: Whether to clear the LLM memory for this session
            limit: Number of similar documents to retrieve
            metadata_filter: Optional filters for retrieval
            system_instruction: Optional system instruction for LLM
            chat_history: Optional list of previous messages [{"role": "user"/"assistant", "content": "..."}]
            
        Returns:
            Dict with response, sources, and metadata
        """
        logger.info(f"RAG chat (session {session_id}): {prompt[:100]}...")
        if chat_history:
            logger.info(f"Received {len(chat_history)} messages as chat history context")
        
        # --- SESSION PERSISTENCE LOGIC ---
        current_patient_seq = metadata_filter.get('patient_seq') if metadata_filter else None
        
        if reset:
            if session_id in self.llm_service.chat_sessions:
                self.llm_service.chat_sessions[session_id]['patient_seq'] = None
        else:
            if not current_patient_seq and session_id in self.llm_service.chat_sessions:
                current_patient_seq = self.llm_service.chat_sessions[session_id].get('patient_seq')
                if current_patient_seq:
                    logger.info(f"Recovered patient_seq '{current_patient_seq}' from session '{session_id}'")
                    if metadata_filter is None:
                        metadata_filter = {}
                    metadata_filter['patient_seq'] = current_patient_seq
                    
                    if system_instruction is None:
                        system_instruction = (
                            "You are a medical AI assistant tailored to analyze a specific patient's context. "
                            "The provided context contains the known medical history for this patient. "
                            "If the user asks about a symptom or condition that is NOT explicitly mentioned "
                            "in the records, DO NOT simply say it's not present. Instead, analyze the patient's "
                            "existing medical history (e.g., past diseases, medications, chief complaints like heart issues) "
                            "and provide medical guidance on how the new symptom might be related to their known underlying conditions. "
                            "Offer plausible connections based on medical knowledge and strongly advise seeking immediate care "
                            "if their history warrants it."
                        )

        # In case it's a reset with no meaningful prompt
        if reset and not prompt.strip():
            # Just reset the LLM memory
            await self.llm_service.generate_chat_answer(
                session_id=session_id,
                prompt="Initialize",
                reset=True,
                patient_seq=current_patient_seq
            )
            return {
                'response': "Conversation history cleared successfully.",
                'sources': [],
                'metadata': {'num_sources': 0, 'session_id': session_id, 'reset': True, 'context_preserved': False, 'message_count': 0}
            }
        
        # Step 1: Generate embedding for the new user message
        query_embedding = await self.embedding_service.generate_embedding(prompt)
        
        # Step 2: Retrieve similar medical documents based on the new message
        vector_repo = VectorRepository(session)
        similar_docs = await vector_repo.search_similar(
            query_embedding=query_embedding,
            limit=limit,
            metadata_filter=metadata_filter
        )
        
        # Step 3: Parse and build medical document context string
        context = self._build_context(similar_docs)
        
        # Step 4: Inject into LLM Chat Session
        context_preserved = False
        message_count = 1
        try:
            chat_result = await self.llm_service.generate_chat_answer(
                session_id=session_id,
                prompt=prompt,
                context=context,
                system_instruction=system_instruction,
                reset=reset,
                patient_seq=current_patient_seq,
                chat_history=chat_history,
            )
            answer = chat_result['text']
            context_preserved = chat_result.get('context_preserved', False)
            message_count = chat_result.get('message_count', 1)
            logger.info(f"Chat answer generated successfully for session {session_id} (context_preserved={context_preserved}, msg#{message_count})")
        except Exception as llm_error:
            logger.warning(f"LLM chat generation failed: {llm_error}")
            answer = (
                f"[LLM unavailable - showing retrieved medical context]\n\n"
                f"Found {len(similar_docs)} relevant medical records:\n\n"
                f"{context}"
            )
            
        # Step 5: Format response
        sources = [
            {
                'content': doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content'],
                'metadata': doc['metadata'],
                'similarity': doc['similarity']
            }
            for doc in similar_docs
        ]
        
        return {
            'response': answer,
            'sources': sources,
            'metadata': {
                'num_sources': len(similar_docs),
                'filters_applied': metadata_filter or {},
                'session_id': session_id,
                'reset_applied': reset,
                'context_preserved': context_preserved,
                'message_count': message_count,
                'chat_history_length': len(chat_history) if chat_history else 0
            }
        }
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Build context string from retrieved documents
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant context found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[Document {i}]")
            context_parts.append(doc['content'])
            
            # Add metadata if available
            if doc.get('metadata'):
                metadata_str = ', '.join([f"{k}: {v}" for k, v in doc['metadata'].items()])
                context_parts.append(f"Metadata: {metadata_str}")
            
            context_parts.append("")  # Empty line between documents
        
        return "\n".join(context_parts)
    
    async def index_document(
        self,
        content: str,
        session: AsyncSession,
        metadata: Optional[Dict[str, Any]] = None,
        source_model: Optional[str] = None,
        source_id: Optional[int] = None
    ) -> int:
        """
        Index a single document: generate embedding and store in vector DB
        
        Args:
            content: Document text
            session: Database session
            metadata: Document metadata
            source_model: Odoo model name
            source_id: Odoo record ID
            
        Returns:
            ID of inserted record
        """
        # Generate embedding
        embedding = await self.embedding_service.generate_embedding(content)
        
        # Store in vector DB
        vector_repo = VectorRepository(session)
        record_id = await vector_repo.insert_embedding(
            content=content,
            embedding=embedding,
            metadata=metadata,
            source_model=source_model,
            source_id=source_id
        )
        
        return record_id
    
    async def index_documents_batch(
        self,
        documents: List[Dict[str, Any]],
        session: AsyncSession
    ) -> int:
        """
        Index multiple documents in batch
        
        Args:
            documents: List of dicts with keys: content, metadata, source_model, source_id
            session: Database session
            
        Returns:
            Number of documents indexed
        """
        if not documents:
            return 0
        
        logger.info(f"Indexing {len(documents)} documents...")
        
        # Extract texts for batch embedding
        texts = [doc['content'] for doc in documents]
        
        # Generate embeddings in batch
        embeddings = await self.embedding_service.generate_embeddings_batch(texts)
        
        # Prepare records for insertion
        records = []
        for doc, embedding in zip(documents, embeddings):
            records.append({
                'content': doc['content'],
                'embedding': embedding,
                'metadata': doc.get('metadata'),
                'source_model': doc.get('source_model'),
                'source_id': doc.get('source_id')
            })
        
        # Insert into vector DB
        vector_repo = VectorRepository(session)
        count = await vector_repo.insert_embeddings_batch(records)
        
        logger.info(f"Indexed {count} documents successfully")
        
        return count
