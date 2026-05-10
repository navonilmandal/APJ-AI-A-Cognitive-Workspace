import pandas as pd
from pathlib import Path
from typing import List
from datetime import datetime
from backend.ingestion.base_loader import BaseLoader
from backend.schemas.memory import MemoryObject

class UbuntuLoader(BaseLoader):
    def __init__(self):
        super().__init__(source_name="ubuntu_dialogues")

    def load(self, file_path: Path) -> List[MemoryObject]:
        if not file_path.exists():
            return []
        
        # Large dataset, use chunking if needed in the future, but for now standard load
        df = pd.read_csv(file_path)
        normalized_data = []
        
        for _, row in df.iterrows():
            conv_id = row.get('dialogueID', 'unknown')
            speaker = str(row.get('from', 'user')).lower()
            message = str(row.get('text', ''))
            ts_str = row.get('date')
            
            timestamp = None
            if ts_str:
                try:
                    # Try parsing ISO format
                    timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except Exception:
                    pass

            obj = MemoryObject(
                conversation_id=f"ubuntu_{conv_id}",
                speaker=speaker,
                message=self.clean_text(message),
                source=self.source_name,
                timestamp=timestamp,
                topic="technical_support"
            )
            normalized_data.append(obj)
                
        return normalized_data
