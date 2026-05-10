from pathlib import Path
from backend.core.config import settings
from backend.ingestion.persona_loader import PersonaLoader
from backend.ingestion.dailydialog_loader import DailyDialogLoader
from backend.ingestion.empathetic_loader import EmpatheticLoader
from backend.ingestion.ubuntu_loader import UbuntuLoader
from backend.retrieval.service import RetrievalService
from backend.memory.service import MemoryService
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

def run_all_ingestions(limit_per_dataset: int = 100):
    """
    Main orchestration function to normalize all datasets and store in memory.
    """
    retrieval = RetrievalService()
    memory = MemoryService(retrieval)
    
    loaders = [
        (PersonaLoader(), settings.DATA_DIR / "raw" / "personachat" / "personachat.csv"),
        (DailyDialogLoader(), settings.DATA_DIR / "raw" / "dailydialog" / "train.csv"),
        (EmpatheticLoader(), settings.DATA_DIR / "raw" / "empathetic_dialogues" / "emotion-emotion_69k.csv"),
        (UbuntuLoader(), settings.DATA_DIR / "raw" / "ubuntu_dialogues" / "dialogueText.csv"),
    ]
    
    for loader, path in loaders:
        logger.info(f"Starting ingestion: {loader.source_name} from {path}")
        try:
            memories = loader.load(path)
            if limit_per_dataset > 0:
                memories = memories[:limit_per_dataset]
            
            if memories:
                for m in memories:
                    m.user_id = "dataset_user"
                    m.memory_type = "dataset"
                memory.store_memories(memories)
                logger.info(f"Successfully ingested {len(memories)} turns from {loader.source_name}")
            else:
                logger.warning(f"No data found for {loader.source_name} at {path}")
        except Exception as e:
            logger.error(f"Failed to ingest {loader.source_name}: {e}")

    # Persist the vector store
    retrieval.save()
    logger.info("Cognitive Memory Foundation built successfully.")

if __name__ == "__main__":
    run_all_ingestions(limit_per_dataset=100)
