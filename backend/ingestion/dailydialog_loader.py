import pandas as pd
import ast
from pathlib import Path
from typing import List
from backend.ingestion.base_loader import BaseLoader
from backend.schemas.memory import MemoryObject

class DailyDialogLoader(BaseLoader):
    def __init__(self):
        super().__init__(source_name="dailydialog")

    def load(self, file_path: Path) -> List[MemoryObject]:
        if not file_path.exists():
            return []
        
        df = pd.read_csv(file_path)
        normalized_data = []
        
        for idx, row in df.iterrows():
            dialogue = row.get('dialog', '[]')
            
            try:
                if isinstance(dialogue, str):
                    turns = ast.literal_eval(dialogue)
                else:
                    turns = dialogue
                
                for i, message in enumerate(turns):
                    # DailyDialog is usually turn-based (User A -> User B)
                    speaker = "user_a" if i % 2 == 0 else "user_b"
                    
                    obj = MemoryObject(
                        conversation_id=f"daily_{idx}",
                        speaker=speaker,
                        message=self.clean_text(message),
                        source=self.source_name,
                        topic="daily_life"
                    )
                    normalized_data.append(obj)
            except Exception:
                continue
                
        return normalized_data
