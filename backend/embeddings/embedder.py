import logging
from typing import List, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class CandidateEmbedder:
    """
    Generates semantic embeddings using the BAAI/bge-large-en-v1.5 sentence-transformer model.
    Optimized for batch candidate ingestion and query-passage search retrieval.
    """
    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5", device: Optional[str] = None):
        import torch
        
        # Determine execution hardware: GPU (CUDA) if available, fallback to CPU
        if not device:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Initializing embedding model '{model_name}' on device '{self.device}'...")
        
        try:
            self.model = SentenceTransformer(model_name, device=self.device)
            # Dimension size of BAAI/bge-large-en-v1.5 is 1024
            self.dimension = 1024
            logger.info("Embedding model loaded successfully.")
        except Exception as exc:
            logger.critical(f"Failed to load embedding model '{model_name}': {exc}")
            raise

    def embed_passages(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        """
        Generates dense vector embeddings for candidate profile passages.
        Returns a numpy array of shape (num_texts, dimension), L2 normalized.
        """
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)
            
        logger.info(f"Generating embeddings for {len(texts)} passages in batches of {batch_size}...")
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,  # Automatically L2 normalizes for Cosine Similarity search
                show_progress_bar=False,
                convert_to_numpy=True
            )
            return embeddings.astype(np.float32)
        except Exception as exc:
            logger.error(f"Error during passage encoding: {exc}")
            raise

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generates a dense vector embedding for a job description search query.
        Appends the required BGE retrieval prefix to optimize search performance.
        """
        # BGE v1.5 recommendation: append instructions to search query inputs
        instruction = "Represent this sentence for searching relevant passages: "
        formatted_query = f"{instruction}{query.strip()}"
        
        try:
            query_vector = self.model.encode(
                [formatted_query],
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True
            )[0]
            return query_vector.astype(np.float32)
        except Exception as exc:
            logger.error(f"Error encoding search query: {exc}")
            raise
