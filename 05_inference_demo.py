import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import PeftModel
import os

label_names = ["sadness", "joy", "love", "anger", "fear", "surprise"]

risk_mapping = {
    "sadness" : ("HIGH RISK",    "Persistent sadness is a key depression indicator"),
    "joy"     : ("NO RISK",      "Positive emotional state detected"),
    "love"    : ("NO RISK",      "Positive emotional connection detected"),
    "anger"   : ("MEDIUM RISK",  "Anger can indicate emotional distress"),
    "fear"    : ("MEDIUM RISK",  "Anxiety and fear may need attention"),
    "surprise": ("LOW RISK",     "Unexpected emotional response detected")
}

risk_icons = {
    "NO RISK"    : "✅",
    "LOW RISK"   : "🟡",
    "MEDIUM RISK": "🟠",
    "HIGH RISK"  : "🔴"
}

def load_model(model_path):
    print(f"Loading model from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    base_model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=6,
        ignore_mismatched_sizes=True
    )
    model = PeftModel.from_pretrained(base_model, model_path)
    model.eval()
    return model, tokenizer

def predict(text, model, tokenizer):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding='max_length',
        truncation=True,
        max_length=128
    )
    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.softmax(outputs.logits, dim=-1)[0]
    pred_id = torch.argmax(probs).item()
    confidence = probs[pred_id].item() * 100
    emotion = label_names[pred_id]
    risk_level, explanation = risk_mapping[emotion]
    icon = risk_icons[risk_level]

    return {
        "emotion"     : emotion,
        "risk_level"  : risk_level,
        "confidence"  : confidence,
        "explanation" : explanation,
        "icon"        : icon,
        "all_probs"   : {label_names[i]: f"{probs[i].item()*100:.1f}%" for i in range(6)}
    }

def print_report(text, result, model_name):
    print("\n" + "="*55)
    print(f"  MENTAL HEALTH RISK REPORT ({model_name})")
    print("="*55)
    print(f"  Input    : {text[:60]}")
    print(f"  Emotion  : {result['emotion'].upper()}")
    print(f"  Risk     : {result['icon']} {result['risk_level']}")
    print(f"  Confidence: {result['confidence']:.1f}%")
    print(f"  Insight  : {result['explanation']}")
    print(f"\n  All Probabilities:")
    for emotion, prob in result['all_probs'].items():
        bar = "█" * int(float(prob[:-1]) / 5)
        print(f"    {emotion:<10}: {prob:>6}  {bar}")
    print("="*55)

test_texts = [
    "I feel so empty and hopeless, nothing makes sense anymore",
    "Today was absolutely amazing, I got the job I always wanted!",
    "I am so angry at everything, nobody understands me",
    "I am scared about what the future holds for me",
    "I love spending time with my family, they mean everything"
]

if os.path.exists("models/lora_model/final"):
    model_path = "models/lora_model/final"
    model_name = "LoRA"
elif os.path.exists("models/qlora_model/final"):
    model_path = "models/qlora_model/final"
    model_name = "QLoRA"
else:
    print("No trained model found!")
    exit()

model, tokenizer = load_model(model_path)
print(f"\nRunning inference with {model_name} model...")

for text in test_texts:
    result = predict(text, model, tokenizer)
    print_report(text, result, model_name)

print("\nInference Demo Complete!")