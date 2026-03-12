# Mental Health Emotion Classifier — LoRA & QLoRA Fine-Tuning

A project that fine-tunes DistilBERT on emotion detection using parameter-efficient methods (LoRA & QLoRA) for mental health risk assessment.

---

## Project Overview

This project fine-tunes DistilBERT using two parameter-efficient techniques — LoRA and QLoRA — to classify text into 6 emotions. The predictions are then mapped to mental health risk levels with actionable remedies, making it useful for early mental health screening applications.

---

## Key Features

### Emotion Detection
- Classifies input text into 6 emotions: sadness, joy, love, anger, fear, and surprise
- Uses fine-tuned DistilBERT with LoRA and QLoRA adapters
- Returns confidence score for each prediction
- Shows probability distribution across all 6 emotions

### Mental Health Risk Assessment
- Maps each detected emotion to a risk level automatically
- Four risk levels: HIGH RISK, MEDIUM RISK, LOW RISK, and NO RISK
- Provides a short insight explaining why the risk level was assigned
- Displays recommended remedies tailored to each emotion

### Crisis Detection
- Scans input text for crisis keywords such as "suicide", "want to die", "end my life", and similar phrases
- Instantly shows a crisis banner with helpline numbers when detected
- Includes iCall Helpline: 9152987821 for immediate support

### Dual Model Comparison (app.py)
- Run both LoRA and QLoRA models on the same input simultaneously
- Side-by-side comparison of emotion, risk level, confidence, and inference time
- Shows whether both models agree or disagree on the prediction
- Head-to-head comparison table with per-metric breakdown

### Probability Chart
- Interactive bar chart showing the probability of all 6 emotions
- Powered by Plotly for smooth, responsive visualization
- Available for both single model and dual model modes

### Recommended Remedies
- Each emotion comes with 6 curated, practical remedies
- Examples: breathing exercises for anger, journaling for sadness, sunlight exposure tips
- Displayed as cards with emoji icons for easy reading

### Streamlit Web App
- Clean dark-themed UI built with Streamlit
- Sidebar for model selection (LoRA only, QLoRA only, or both)
- Tabbed view: Simple View and Detailed Analysis
- Fully responsive layout with wide mode enabled

---

## Emotions and Risk Levels

| Emotion  | Risk Level  | Example Remedy                          |
|----------|-------------|------------------------------------------|
| Sadness  | HIGH RISK   | Journal feelings, morning sunlight, iCall helpline |
| Anger    | MEDIUM RISK | Box breathing, cold water, physical activity |
| Fear     | MEDIUM RISK | Grounding techniques, limit news, therapy |
| Surprise | LOW RISK    | Pause and reflect, talk to someone       |
| Joy      | NO RISK     | Maintain routine, share positivity       |
| Love     | NO RISK     | Nurture connections, express gratitude   |

---

## Pipeline Flow

```
01_data_preparation.py
        ↓ (saves tokenized dataset)
02_lora_finetuning.py  ──┐
                          ├──→ 04_evaluation.py → comparison chart
03_qlora_finetuning.py ──┘
        ↓ (either model)
05_inference_demo.py → mental health risk reports
        ↓
    app.py → interactive Streamlit web UI
```

## Technologies Used

| Category            | Tools / Libraries                          |
|---------------------|--------------------------------------------|
| Base Model          | DistilBERT (distilbert-base-uncased)        |
| Fine-Tuning         | LoRA, QLoRA via PEFT library                |
| Quantization        | BitsAndBytes (4-bit NF4)                    |
| Training Framework  | HuggingFace Transformers + Trainer API      |
| Dataset             | dair-ai/emotion from HuggingFace Datasets   |
| Evaluation Metrics  | Accuracy, Weighted F1 Score                 |
| Visualization       | Matplotlib, Seaborn (eval), Plotly (web app)|
| Web App             | Streamlit                                   |
| Deep Learning       | PyTorch                                     |

---

## LoRA vs QLoRA — How They Work

### LoRA (Low-Rank Adaptation)
```
Frozen DistilBERT (float32)
        +
Small trainable adapter matrices injected into:
    ├── q_lin (Query attention layer)
    └── v_lin (Value attention layer)

Only ~0.5% of parameters are trained!
```

### QLoRA (Quantized LoRA)
```
DistilBERT compressed to 4-bit (NF4) — 8x less memory
        +
Same LoRA adapters trained in float16

Best of both worlds: tiny memory + good accuracy
```

### Comparison Table

| Feature          | Full Fine-Tuning | LoRA    | QLoRA        |
|------------------|-----------------|---------|--------------|
| Params Trained   | 67M             | ~300K   | ~300K        |
| Memory Usage     | High            | Medium  | Low          |
| GPU Required     | Yes             | No      | Yes          |
| Training Speed   | Slow            | Fast    | Fastest      |
| Quality Loss     | None            | Minimal | Very Minimal |

---

## Model Configuration

```python
# LoRA Config (same for both LoRA and QLoRA)
LoraConfig(
    task_type      = TaskType.SEQ_CLS,
    r              = 8,
    lora_alpha     = 16,
    lora_dropout   = 0.1,
    target_modules = ["q_lin", "v_lin"]
)

# QLoRA Quantization Config
BitsAndBytesConfig(
    load_in_4bit              = True,
    bnb_4bit_quant_type       = "nf4",
    bnb_4bit_compute_dtype    = torch.float16,
    bnb_4bit_use_double_quant = True
)
```

---

## Dataset

- Dataset: dair-ai/emotion on HuggingFace
- Source: English Twitter messages
- Labels: 6 emotions — sadness, joy, love, anger, fear, surprise

| Split      | Total Samples | Used in Project |
|------------|--------------|----------------|
| Train      | 16,000       | 2,000 – 3,000  |
| Validation | 2,000        | 400            |
| Test       | 2,000        | 400            |

> Dataset is intended for educational and research purposes only.

---

Here's a clean 2-3 line summary you can use anywhere:

---

This project fine-tunes DistilBERT using LoRA and QLoRA techniques to classify text into 6 emotions — sadness, joy, love, anger, fear, and surprise. The detected emotion is mapped to a mental health risk level with actionable remedies and crisis support. A Streamlit web app allows users to run predictions using either or both models side by side with real-time confidence scores.
