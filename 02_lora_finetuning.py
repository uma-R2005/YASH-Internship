import torch
import numpy as np
from datasets import load_from_disk
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer
)
from peft import get_peft_model, LoraConfig, TaskType
from sklearn.metrics import f1_score, accuracy_score
import os

# ── 0. Check Device ───────────────────────────────────────────────────────────
if torch.cuda.is_available():
    device = "cuda"
    print(f"Using GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
else:
    device = "cpu"
    print("No GPU found — using CPU")

# ── 1. Load Tokenized Dataset ─────────────────────────────────────────────────
print("\nLoading tokenized dataset...")
tokenized_dataset = load_from_disk("data/tokenized_dataset")

# Use small subset for speed
small_train = tokenized_dataset['train'].select(range(2000))
small_val   = tokenized_dataset['validation'].select(range(400))
small_test  = tokenized_dataset['test'].select(range(400))

print(f"Train : {len(small_train)} samples")
print(f"Val   : {len(small_val)} samples")
print(f"Test  : {len(small_test)} samples")

# ── 2. Load Base Model ────────────────────────────────────────────────────────
print("\nLoading DistilBERT base model...")
model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=6,
    ignore_mismatched_sizes=True
)

# ── 3. Apply LoRA Config ──────────────────────────────────────────────────────
print("\nApplying LoRA adapters...")
lora_config = LoraConfig(
    task_type=TaskType.SEQ_CLS,
    r=8,                        # LoRA rank
    lora_alpha=16,              # Scaling factor
    lora_dropout=0.1,           # Dropout
    target_modules=["q_lin", "v_lin"]  # Which layers to adapt
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ── 4. Metrics ────────────────────────────────────────────────────────────────
label_names = ["sadness", "joy", "love", "anger", "fear", "surprise"]

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, predictions)
    f1  = f1_score(labels, predictions, average='weighted')
    return {"accuracy": acc, "f1_weighted": f1}

# ── 5. Training Arguments ─────────────────────────────────────────────────────
os.makedirs("models/lora_model", exist_ok=True)
os.makedirs("outputs/lora_logs", exist_ok=True)

training_args = TrainingArguments(
    output_dir="models/lora_model",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    warmup_steps=50,
    weight_decay=0.01,
    logging_dir="outputs/lora_logs",
    logging_steps=20,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    report_to="none"
)

# ── 6. Trainer Setup ──────────────────────────────────────────────────────────
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=small_train,
    eval_dataset=small_val,
    compute_metrics=compute_metrics
)

# ── 7. Train ──────────────────────────────────────────────────────────────────
print("\n" + "="*50)
print("  STARTING LORA FINE-TUNING")
print("="*50)
trainer.train()

# ── 8. Save ───────────────────────────────────────────────────────────────────
os.makedirs("models/lora_model/final", exist_ok=True)
model.save_pretrained("models/lora_model/final")
print("\nLoRA model saved to models/lora_model/final")

# ── 9. Evaluate on Test Set ───────────────────────────────────────────────────
print("\nEvaluating on test set...")
results = trainer.evaluate(small_test)
print("\n" + "="*50)
print("  LORA RESULTS")
print("="*50)
print(f"  Accuracy  : {results['eval_accuracy']:.4f}")
print(f"  F1 Score  : {results['eval_f1_weighted']:.4f}")
print("="*50)
print("\nLoRA Fine-tuning Complete!")