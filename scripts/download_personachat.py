from datasets import load_dataset
import pandas as pd
import os

# Create directories
os.makedirs(
    "data/raw/personachat",
    exist_ok=True
)

print("Downloading PersonaChat dataset...")

# Load dataset
dataset = load_dataset(
    "Cynaptics/persona-chat"
)

# Convert train split to dataframe
train_df = pd.DataFrame(
    dataset["train"]
)

# Save CSV
train_df.to_csv(
    "data/raw/personachat/personachat.csv",
    index=False
)

print("PersonaChat dataset saved successfully.")