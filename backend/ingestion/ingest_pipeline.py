import time
from pathlib import Path
from typing import List, Optional
from backend.core.config import settings
from backend.ingestion.persona_loader import PersonaLoader
from backend.ingestion.dailydialog_loader import DailyDialogLoader
from backend.ingestion.empathetic_loader import EmpatheticLoader
from backend.ingestion.ubuntu_loader import UbuntuLoader
from backend.memory.vector_store import VectorStore
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

class IngestionPipeline:
    """
    Centralized pipeline for loading, normalizing, and vectorizing conversational datasets.
    """
    def __init__(self, limit_per_dataset: int = 500):
        self.limit = limit_per_dataset
        self.vector_store = VectorStore()
        self.loaders = [
            (PersonaLoader(), settings.DATA_DIR / "raw" / "personachat" / "personachat.csv"),
            (DailyDialogLoader(), settings.DATA_DIR / "raw" / "dailydialog" / "train.csv"),
            (EmpatheticLoader(), settings.DATA_DIR / "raw" / "empathetic_dialogues" / "emotion-emotion_69k.csv"),
            (UbuntuLoader(), settings.DATA_DIR / "raw" / "ubuntu_dialogues" / "dialogueText.csv"),
        ]

    def run(self):
        """Executes the full ingestion and vectorization process."""
        logger.info(f"Starting Semantic Memory Ingestion (Limit: {self.limit} per dataset)")
        start_time = time.time()
        
        total_ingested = 0
        for loader, path in self.loaders:
            if not path.exists():
                logger.warning(f"Skipping {loader.source_name}: File not found at {path}")
                continue
            
            try:
                logger.info(f"Processing {loader.source_name}...")
                memories = loader.load(path)
                
                if self.limit > 0:
                    memories = memories[:self.limit]
                
                if memories:
                    # Batch processing to Qdrant
                    # Add Isolation Tags
                    for obj in memories:
                        obj.memory_type = "dataset"
                        obj.user_id = "system_dataset"
                    
                    self.vector_store.upsert_memories(memories)
                    total_ingested += len(memories)
                    logger.info(f"Ingested {len(memories)} turns from {loader.source_name}")
                else:
                    logger.warning(f"No valid memories extracted from {loader.source_name}")
                    
            except Exception as e:
                logger.error(f"Error during ingestion of {loader.source_name}: {e}")

        duration = time.time() - start_time
        logger.info(f"Ingestion Pipeline Complete. Total Vectors: {total_ingested} | Duration: {duration:.2f}s")

if __name__ == "__main__":
    # Standard run with 500 limit for testing
    pipeline = IngestionPipeline(limit_per_dataset=500)
    pipeline.run()
