from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
from backend.schemas.memory import MemoryObject
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

class BaseLoader(ABC):
    """Abstract base class for all dataset loaders."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def load(self, file_path: Path) -> List[MemoryObject]:
        """Loads and normalizes the dataset into MemoryObjects."""
        pass

    def clean_text(self, text: str) -> str:
        """Standard text cleaning for conversational data."""
        if not text:
            return ""
        # Basic cleaning: remove extra whitespace, handle common noise
        return " ".join(text.split()).strip()
