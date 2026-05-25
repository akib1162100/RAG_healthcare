"""
Embedding Service - Handles text embeddings generation
"""
from typing import List
from transformers import AutoTokenizer, AutoModel
import torch
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings using a configurable model (default: ClinicalBERT)"""
    
    def __init__(self, model_name: str = None):
        from app.core.config import settings
        if model_name is None:
            model_name = settings.EMBEDDING_MODEL_NAME
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.dimension = settings.VECTOR_DIMENSION
        
    async def initialize(self):
        """Load embedding model and tokenizer"""
        logger.info(f"Loading embedding model: {self.model_name}")
        
        # Device selection from config
        from app.core.config import settings
        device_setting = settings.EMBEDDING_DEVICE
        if device_setting == 'auto':
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            device = device_setting
        logger.info(f"Embedding device: {device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        if device == 'cuda' and torch.cuda.is_available():
            self.model = self.model.to(device)
        self.device = device
        
        # Set to evaluation mode (no training)
        self.model.eval()
        if hasattr(self.model, "config") and getattr(self.model.config, "hidden_size", None):
            self.dimension = int(self.model.config.hidden_size)
        
        logger.info(f"Embedding model loaded successfully: {self.model_name}")
    
    def _mean_pooling(self, model_output, attention_mask):
        """Mean pooling to get sentence embeddings"""
        token_embeddings = model_output[0]  # First element contains token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using ClinicalBERT
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("Embedding model not initialized. Call initialize() first.")
        
        # Tokenize
        encoded_input = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )
        if getattr(self, "device", "cpu") == "cuda" and torch.cuda.is_available():
            encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
        
        # Generate embeddings (no gradient computation needed)
        with torch.no_grad():
            model_output = self.model(**encoded_input)
        
        # Apply mean pooling
        sentence_embeddings = self._mean_pooling(model_output, encoded_input['attention_mask'])
        
        # Convert to list
        embedding = sentence_embeddings[0].detach().cpu().tolist()
        
        return embedding
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("Embedding model not initialized. Call initialize() first.")
        
        # Tokenize all texts
        encoded_input = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )
        if getattr(self, "device", "cpu") == "cuda" and torch.cuda.is_available():
            encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
        
        # Generate embeddings
        with torch.no_grad():
            model_output = self.model(**encoded_input)
        
        # Apply mean pooling
        sentence_embeddings = self._mean_pooling(model_output, encoded_input['attention_mask'])
        
        # Convert to list of lists
        embeddings = sentence_embeddings.detach().cpu().tolist()
        
        return embeddings
    
    def get_dimension(self) -> int:
        """Return the embedding dimension"""
        return self.dimension
