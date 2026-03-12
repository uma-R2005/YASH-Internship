import torch
import numpy as np
import time
from datasets import load_from_disk
from transformers import AutoTokenizer
from peft import PeftModel, PeftConfig
from sklearn.metrics import (
    f1_score, accuracy_score,
    classification_report, confusion_matrix
)
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ── 0. Setup ──────────────────────────────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using: {device.upper()}")

label_names = ["sadness", "joy", "love", "anger", "fear", "surprise"]
tokenized_dataset = load_from_disk("data/tokenized_dataset")
test_dataset = tokenized_dataset['test'].select(range(400))

tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
os.makedirs("outputs", exist_ok=True)

# ── 1. Evaluation Function ────────────────────────────────────────────────────
def evaluate_model(model_path, model_name):
    from transformers import AutoModelForSequenceClassification
    from peft import PeftModel

    print(f"\nLoading {model_name}...")
    start = time.time()

    base_model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=6,
        ignore_mismatched_sizes=True
    )
    model = PeftModel.from_pretrained(base_model, model_path)
    model = model.to(device)
    model.eval()

    load_time = time.time() - start
    print(f"Loaded in {load_time:.1f}s")

    # Run predictions
    all_preds, all_labels = [], []
    infer_start = time.time()

    for i in range(0, len(test_dataset), 32):
        batch = test_dataset[i:i+32]
        inputs = {
            'input_ids': torch.tensor(batch['input_ids']).to(device),
            'attention_mask': torch.tensor(batch['attention_mask']).to(device)
        }
        with torch.no_grad():
            outputs = model(**inputs)
        preds = torch.argmax(outputs.logits, dim=-1).cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(batch['label'])

    infer_time = time.time() - infer_start

    acc = accuracy_score(all_labels, all_preds)
    f1  = f1_score(all_labels, all_preds, average='weighted')

    print(f"\n{'='*40}")
    print(f"  {model_name} RESULTS")
    print(f"{'='*40}")
    print(f"  Accuracy       : {acc:.4f}")
    print(f"  F1 Weighted    : {f1:.4f}")
    print(f"  Inference Time : {infer_time:.2f}s")
    print(f"{'='*40}")
    print(classification_report(all_labels, all_preds, target_names=label_names))

    return {
        "name": model_name,
        "accuracy": acc,
        "f1": f1,
        "inference_time": infer_time,
        "predictions": all_preds,
        "labels": all_labels
    }

# ── 2. Evaluate Both Models ───────────────────────────────────────────────────
results = {}

if os.path.exists("models/lora_model/final"):
    results['lora'] = evaluate_model("models/lora_model/final", "LoRA")
else:
    print("LoRA model not found — run 02_lora_finetuning.py first")

if os.path.exists("models/qlora_model/final"):
    results['qlora'] = evaluate_model("models/qlora_model/final", "QLoRA")
else:
    print("QLoRA model not found — run 03_qlora_finetuning.py first")

# ── 3. Side-by-Side Comparison ────────────────────────────────────────────────
if len(results) == 2:
    print("\n" + "="*50)
    print("  LORA vs QLORA COMPARISON")
    print("="*50)
    print(f"  {'Metric':<20} {'LoRA':>10} {'QLoRA':>10}")
    print(f"  {'-'*40}")
    print(f"  {'Accuracy':<20} {results['lora']['accuracy']:>10.4f} {results['qlora']['accuracy']:>10.4f}")
    print(f"  {'F1 Weighted':<20} {results['lora']['f1']:>10.4f} {results['qlora']['f1']:>10.4f}")
    print(f"  {'Inference Time':<20} {results['lora']['inference_time']:>9.2f}s {results['qlora']['inference_time']:>9.2f}s")
    print("="*50)

    # ── 4. Plot Comparison ────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("LoRA vs QLoRA Comparison", fontsize=16, fontweight='bold')

    # Accuracy & F1 comparison
    metrics = ['Accuracy', 'F1 Score']
    lora_vals   = [results['lora']['accuracy'],  results['lora']['f1']]
    qlora_vals  = [results['qlora']['accuracy'], results['qlora']['f1']]

    x = np.arange(len(metrics))
    axes[0].bar(x - 0.2, lora_vals,  0.4, label='LoRA',  color='steelblue')
    axes[0].bar(x + 0.2, qlora_vals, 0.4, label='QLoRA', color='coral')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(metrics)
    axes[0].set_ylim(0, 1)
    axes[0].set_title("Accuracy & F1 Score")
    axes[0].legend()
    axes[0].set_ylabel("Score")

    # Confusion matrix LoRA
    cm_lora = confusion_matrix(results['lora']['labels'], results['lora']['predictions'])
    sns.heatmap(cm_lora, annot=True, fmt='d', ax=axes[1],
                xticklabels=label_names, yticklabels=label_names, cmap='Blues')
    axes[1].set_title("LoRA Confusion Matrix")
    axes[1].set_ylabel("True Label")
    axes[1].set_xlabel("Predicted Label")
    plt.setp(axes[1].get_xticklabels(), rotation=45, ha='right')

    # Confusion matrix QLoRA
    cm_qlora = confusion_matrix(results['qlora']['labels'], results['qlora']['predictions'])
    sns.heatmap(cm_qlora, annot=True, fmt='d', ax=axes[2],
                xticklabels=label_names, yticklabels=label_names, cmap='Oranges')
    axes[2].set_title("QLoRA Confusion Matrix")
    axes[2].set_ylabel("True Label")
    axes[2].set_xlabel("Predicted Label")
    plt.setp(axes[2].get_xticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig("outputs/lora_vs_qlora_comparison.png", dpi=150, bbox_inches='tight')
    print("\nComparison plot saved to outputs/lora_vs_qlora_comparison.png")
    plt.show()

print("\nEvaluation Complete!")