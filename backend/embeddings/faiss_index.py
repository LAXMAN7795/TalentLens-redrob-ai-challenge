import json
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any
import numpy as np
import faiss

logger = logging.getLogger(__name__)

class FAISSIndexManager:
    """
    Manages vector storage, indexing, and similarity searches using FAISS.
    Maintains a persistent mapping between FAISS integer offsets and string Candidate IDs.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        # Use IndexFlatIP (Inner Product) which acts as Cosine Similarity for L2-normalized vectors
        self.index = faiss.IndexFlatIP(dimension)
        # Sequence of candidate IDs matching FAISS internal offsets [0, 1, 2, ...]
        self.offset_to_candidate_id: List[str] = []

    def add_vectors(self, vectors: np.ndarray, candidate_ids: List[str]) -> None:
        """
        Appends vectors to the FAISS index and records the corresponding candidate IDs.
        Vectors must be pre-normalized and match the dimensions of the index.
        """
        if len(vectors) == 0:
            return

        if len(vectors) != len(candidate_ids):
            raise ValueError(
                f"Mismatch: Got {len(vectors)} vectors but {len(candidate_ids)} candidate IDs."
            )

        if vectors.shape[1] != self.dimension:
            raise ValueError(
                f"Vector dimension mismatch: Expected {self.dimension}, got {vectors.shape[1]}"
            )

        # Cast to float32 as FAISS expects single precision floats
        vectors_f32 = vectors.astype(np.float32)
        self.index.add(vectors_f32)
        
        # Extend the mapping list
        self.offset_to_candidate_id.extend(candidate_ids)
        logger.info(f"Added {len(candidate_ids)} vectors to FAISS index. Total index size: {self.index.ntotal}")

    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """
        Performs a vector search for the nearest K matches.
        Returns a list of (candidate_id, cosine_similarity_score) sorted by highest similarity first.
        """
        if self.index.ntotal == 0:
            logger.warning("Attempted search on an empty FAISS index.")
            return []

        # query_vector must be of shape (1, dimension) or (dimension,)
        if query_vector.ndim == 1:
            query_vector = np.expand_dims(query_vector, axis=0)

        query_vector_f32 = query_vector.astype(np.float32)
        
        # Clamp K to index size to prevent indexing errors
        actual_k = min(k, self.index.ntotal)
        
        # Search the index
        scores, indices = self.index.search(query_vector_f32, actual_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            # FAISS returns -1 if there are not enough matches
            if idx != -1 and idx < len(self.offset_to_candidate_id):
                cand_id = self.offset_to_candidate_id[idx]
                results.append((cand_id, float(score)))
                
        return results

    def save(self, filepath: Union[str, Path]) -> None:
        """
        Persists the index binary and JSON-formatted offset mappings to disk.
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(path))
        
        # Save mapping companion file
        mapping_path = path.with_suffix(".mapping.json")
        with open(mapping_path, "w", encoding="utf-8") as file:
            json.dump(self.offset_to_candidate_id, file, indent=2)
            
        logger.info(f"FAISS index and ID mapping saved successfully at: {path}")

    def load(self, filepath: Union[str, Path]) -> None:
        """
        Loads the FAISS index binary and ID offset mapping from disk.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"FAISS index file not found: {path}")

        # Load FAISS index
        self.index = faiss.read_index(str(path))
        
        # Load mapping file
        mapping_path = path.with_suffix(".mapping.json")
        if mapping_path.exists():
            with open(mapping_path, "r", encoding="utf-8") as file:
                self.offset_to_candidate_id = json.load(file)
            logger.info(f"FAISS index loaded. Total entries: {self.index.ntotal}")
        else:
            logger.warning(f"ID mapping file missing at {mapping_path}. Search lookups will fail.")
            self.offset_to_candidate_id = []
            
        # Verify alignment
        if len(self.offset_to_candidate_id) != self.index.ntotal:
            logger.error(
                f"Index alignment mismatch: FAISS has {self.index.ntotal} entries "
                f"but mapping has {len(self.offset_to_candidate_id)}."
            )
