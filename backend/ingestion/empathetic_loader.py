import pandas as pd
from pathlib import Path
from typing import List
from backend.ingestion.base_loader import BaseLoader
from backend.schemas.memory import MemoryObject

class EmpatheticLoader(BaseLoader):
    def __init__(self):
        super().__init__(source_name="empathetic_dialogues")

    def load(self, file_path: Path) -> List[MemoryObject]:
        if not file_path.exists():
            return []
        
        # This dataset often has slightly different formats depending on how it was saved
        df = pd.read_csv(file_path)
        normalized_data = []
        
        for idx, row in df.iterrows():
            # Match the columns in emotion-emotion_69k.csv
            message = row.get('empathetic_dialogues') or row.get('utterance') or row.get('Situation') or ""
            emotion_val = row.get('emotion')
            emotion = str(emotion_val) if pd.notna(emotion_val) else "neutral"
            conv_id = row.get('conv_id') or str(idx)
            
            if not message:
                continue
                
            speaker = "user" # Defaulting if not specified
            if ":" in str(message):
                parts = str(message).split(":", 1)
                speaker = parts[0].strip().lower()
                message = parts[1]

            obj = MemoryObject(
                conversation_id=f"emp_{conv_id}",
                speaker=speaker,
                message=self.clean_text(str(message)),
                source=self.source_name,
                emotion=emotion,
                topic="empathetic_response"
            )
            normalized_data.append(obj)
                
        return normalized_data
