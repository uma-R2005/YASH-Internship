from datasets import load_dataset
from transformers import AutoTokenizer
import pandas as pd
import os

print("Loading dataset...")
dataset = load_dataset("emotion")
print(f"Train: {len(dataset['train'])} | Val: {len(dataset['validation'])} | Test: {len(dataset['test'])}")

label_names = dataset['train'].features['label'].names
print("\nEmotion Labels:", label_names)

train_df = pd.DataFrame(dataset['train'])
print("\nLabel distribution:")
print(train_df['label'].value_counts())

print("\nLoading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

def tokenize_function(examples):
    return tokenizer(
        examples['text'],
        padding='max_length',
        truncation=True,
        max_length=128
    )

print("Tokenizing dataset...")
tokenized_dataset = dataset.map(tokenize_function, batched=True)
print(tokenized_dataset)

os.makedirs("data", exist_ok=True)
tokenized_dataset.save_to_disk("data/tokenized_dataset")
print("Dataset saved!")
print("Data preparation complete!")