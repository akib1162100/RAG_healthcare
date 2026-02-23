"""
Medical Embedding Generator using ClinicalBERT
Generates embeddings optimized for medical/clinical text
"""
import os
from typing import List
import logging
import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class MedicalEmbeddingGenerator:
    """Generate embeddings using medical-specific models"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize embedding generator
        
        Args:
            model_name: HuggingFace model name. Defaults to ClinicalBERT
        """
        if model_name is None:
            model_name = os.getenv('EMBEDDING_MODEL', 'emilyalsentzer/Bio_ClinicalBERT')
        
        logger.info(f"Loading embedding model: {model_name}")
        
        # Check if GPU is available
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device: {self.device}")
        
        # Load model
        self.model = SentenceTransformer(model_name, device=self.device)
        
        # Get embedding dimension
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.embedding_dim}")
        
        # Verify dimension matches expected (768 for ClinicalBERT)
        expected_dim = int(os.getenv('EMBEDDING_DIM', '768'))
        if self.embedding_dim != expected_dim:
            logger.warning(
                f"Embedding dimension mismatch! Model: {self.embedding_dim}, "
                f"Expected: {expected_dim}. Update EMBEDDING_DIM in .env"
            )
    
    def generate_embeddings(
        self, 
        texts: List[str], 
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            batch_size: Batch size for processing
            show_progress: Show progress bar
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        # Generate embeddings
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_tensor=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        
        # Convert tensor to list of lists (avoids numpy dependency)
        embeddings_list = embeddings.cpu().tolist()
        
        logger.info(f"Generated {len(embeddings_list)} embeddings")
        return embeddings_list
    
    def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return self.generate_embeddings([text], show_progress=False)[0]
