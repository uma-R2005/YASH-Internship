import torch
import numpy as np
from datasets import load_from_disk
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig
)
from peft import get_peft_model, LoraConfig, TaskType, prepare_model_for_kbit_training
from sklearn.metrics import f1_score, accuracy_score
import os

# ── 0. Check Device ───────────────────────────────────────────────────────────
if torch.cuda.is_available():
    device = "cuda"
    print(f"Using GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    use_4bit = True
else:
    device = "cpu"
    print("No GPU — using CPU mode (QLoRA 4-bit requires GPU, falling back to 8-bit CPU)")
    use_4bit = False

# ── 1. Load Tokenized Dataset ─────────────────────────────────────────────────
print("\nLoading tokenized dataset...")
tokenized_dataset = load_from_disk("data/tokenized_dataset")

small_train = tokenized_dataset['train'].select(range(3000))
small_val   = tokenized_dataset['validation'].select(range(400))
small_test  = tokenized_dataset['test'].select(range(400))

print(f"Train : {len(small_train)} samples")
print(f"Val   : {len(small_val)} samples")
print(f"Test  : {len(small_test)} samples")

# ── 2. QLoRA Quantization Config ──────────────────────────────────────────────
print("\nSetting up QLoRA quantization config...")

if use_4bit:
    # 4-bit quantization (QLoRA) — GPU only
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",           # NormalFloat4 quantization
        bnb_4bit_compute_dtype=torch.float16, # Compute in float16
        bnb_4bit_use_double_quant=True        # Double quantization for extra memory savings
    )
    print("4-bit NF4 quantization enabled (QLoRA)")

    # ── 3. Load Quantized Model ───────────────────────────────────────────────
    print("\nLoading 4-bit quantized DistilBERT...")
    model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=6,
        quantization_config=bnb_config,
        device_map="auto"
    )
    # Prepare model for k-bit training
    model = prepare_model_for_kbit_training(model)

else:
    # CPU fallback — load normally
    print("\nLoading DistilBERT (CPU mode)...")
    model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=6,
        ignore_mismatched_sizes=True
    )

# ── 4. Apply LoRA on top of Quantized Model ───────────────────────────────────
print("\nApplying LoRA adapters on quantized model...")
lora_config = LoraConfig(
    task_type=TaskType.SEQ_CLS,
    r=8,                        # LoRA rank
    lora_alpha=16,              # Scaling
    lora_dropout=0.1,
    target_modules=["q_lin", "v_lin"],
    bias="none"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ── 5. Metrics ────────────────────────────────────────────────────────────────
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, predictions)
    f1  = f1_score(labels, predictions, average='weighted')
    return {"accuracy": acc, "f1_weighted": f1}

# ── 6. Training Arguments ─────────────────────────────────────────────────────
os.makedirs("models/qlora_model", exist_ok=True)
os.makedirs("outputs/qlora_logs", exist_ok=True)

training_args = TrainingArguments(
    output_dir="models/qlora_model",
    num_train_epochs=3,
    per_device_train_batch_size=32,       # Larger batch = faster
    per_device_eval_batch_size=32,
    warmup_steps=50,
    weight_decay=0.01,
    logging_dir="outputs/qlora_logs",
    logging_steps=20,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    fp16=(device == "cuda"),              # fp16 speeds up GPU training
    dataloader_num_workers=0,             # 0 fixes Windows multiprocessing
    report_to="none"
)

# ── 7. Trainer ────────────────────────────────────────────────────────────────
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=small_train,
    eval_dataset=small_val,
    compute_metrics=compute_metrics
)

# ── 8. Train ──────────────────────────────────────────────────────────────────
print("\n" + "="*50)
print("  STARTING QLORA FINE-TUNING")
print("="*50)
trainer.train()

# ── 9. Save ───────────────────────────────────────────────────────────────────
os.makedirs("models/qlora_model/final", exist_ok=True)
model.save_pretrained("models/qlora_model/final")
print("\nQLoRA model saved to models/qlora_model/final")

# ── 10. Evaluate ──────────────────────────────────────────────────────────────
print("\nEvaluating on test set...")
results = trainer.evaluate(small_test)
print("\n" + "="*50)
print("  QLORA RESULTS")
print("="*50)
print(f"  Accuracy  : {results['eval_accuracy']:.4f}")
print(f"  F1 Score  : {results['eval_f1_weighted']:.4f}")
print("="*50)
print("\nQLoRA Fine-tuning Complete!")