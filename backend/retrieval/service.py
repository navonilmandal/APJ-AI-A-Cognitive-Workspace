import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from backend.core.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

class RetrievalService:
    """
    Service for semantic search and vector retrieval.
    Initial implementation uses FAISS + SentenceTransformers.
    """
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.embedder = SentenceTransformer(self.model_name)
        self.dimension = self.embedder.get_sentence_embedding_dimension()
        
        # FAISS Index
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata: List[Dict[str, Any]] = []
        
        # Persistence path
        self.save_path = settings.PROJECT_ROOT / "artifacts" / "vector_store.pkl"
        self.save_path.parent.mkdir(exist_ok=True)
        
        # Auto-load existing index
        self.load()

    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        """Embeds and adds multiple documents to the index."""
        if not texts:
            return
            
        embeddings = self.embedder.encode(texts)
        self.index.add(np.array(embeddings).astype('float32'))
        self.metadata.extend(metadatas)
        logger.info(f"Added {len(texts)} documents to retrieval index.")

    def add_document(self, text: str, metadata: Dict[str, Any]):
        self.add_documents([text], [metadata])

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Performs semantic search."""
        query_embedding = self.embedder.encode([query])
        distances, indices = self.index.search(
            np.array(query_embedding).astype('float32'), limit
        )
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                results.append({
                    "metadata": self.metadata[idx],
                    "score": float(distances[0][i])
                })
        return results

    def save(self):
        """Persists the index and metadata to disk."""
        data = {
            "index": faiss.serialize_index(self.index),
            "metadata": self.metadata
        }
        with open(self.save_path, "wb") as f:
            pickle.dump(data, f)
        logger.info(f"Retrieval store saved to {self.save_path}")

    def load(self):
        """Loads index and metadata from disk."""
        if not self.save_path.exists():
            logger.warning("No retrieval store found to load.")
            return
            
        with open(self.save_path, "rb") as f:
            data = pickle.load(f)
            self.index = faiss.deserialize_index(data["index"])
            self.metadata = data["metadata"]
        logger.info("Retrieval store loaded successfully.")
