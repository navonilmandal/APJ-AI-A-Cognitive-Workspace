import pandas as pd
import ast
from pathlib import Path
from typing import List
from backend.ingestion.base_loader import BaseLoader
from backend.schemas.memory import MemoryObject

class PersonaLoader(BaseLoader):
    def __init__(self):
        super().__init__(source_name="personachat")

    def load(self, file_path: Path) -> List[MemoryObject]:
        if not file_path.exists():
            return []
        
        df = pd.read_csv(file_path)
        normalized_data = []
        
        for _, row in df.iterrows():
            conv_id = str(row.get('conv_id', 'unknown'))
            # PersonaChat dialogue is often stored as a string representation of a list
            dialogue = row.get('dialogue', '[]')
            
            try:
                if isinstance(dialogue, str):
                    turns = ast.literal_eval(dialogue)
                else:
                    turns = dialogue
                
                for i, turn in enumerate(turns):
                    # Format is usually "Persona A: message" or "Persona B: message"
                    if ":" in turn:
                        speaker, message = turn.split(":", 1)
                    else:
                        speaker = "unknown"
                        message = turn
                        
                    obj = MemoryObject(
                        conversation_id=f"persona_{conv_id}",
                        speaker=speaker.strip().lower(),
                        message=self.clean_text(message),
                        source=self.source_name,
                        topic="persona_consistency"
                    )
                    normalized_data.append(obj)
            except Exception as e:
                continue
                
        return normalized_data
