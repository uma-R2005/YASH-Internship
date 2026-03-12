import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import PeftModel
import plotly.graph_objects as go
import os
import time
import datetime

st.set_page_config(page_title="Mental Health Risk Classifier", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
    * { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #0a0a0f; color: #e8e8f0; }

    /* ── FORCE SIDEBAR ALWAYS VISIBLE ── */
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"] { display: flex !important; visibility: visible !important; width: 22rem !important; min-width: 22rem !important; transform: none !important; }
    [data-testid="stSidebar"] > div { width: 22rem !important; background: #0d0d18 !important; border-right: 1px solid #2d2d4a !important; padding: 1.5rem 1rem !important; }
    section[data-testid="stSidebarContent"] { background: #0d0d18 !important; }
    .main-header { text-align: center; padding: 3rem 0 1rem 0; }
    .main-title { font-family: 'DM Serif Display', serif; font-size: 3.2rem; background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; line-height: 1.2; margin-bottom: 0.5rem; }
    .main-subtitle { color: #6b7280; font-size: 1.1rem; font-weight: 300; letter-spacing: 0.05em; }
    .model-badge { display: inline-block; background: #1a1a2e; border: 1px solid #a78bfa33; color: #a78bfa; padding: 0.3rem 1rem; border-radius: 999px; font-size: 0.8rem; letter-spacing: 0.1em; text-transform: uppercase; margin-top: 1rem; }
    .risk-card { border-radius: 16px; padding: 2rem; text-align: center; margin: 1rem 0; border: 1px solid; position: relative; overflow: hidden; }
    .risk-high   { background: linear-gradient(135deg,#1a0a0a,#2d1515); border-color:#ef444444; box-shadow:0 0 40px #ef444420; }
    .risk-medium { background: linear-gradient(135deg,#1a120a,#2d2015); border-color:#f9731644; box-shadow:0 0 40px #f9731620; }
    .risk-low    { background: linear-gradient(135deg,#0a120a,#152d15); border-color:#22c55e44; box-shadow:0 0 40px #22c55e20; }
    .risk-none   { background: linear-gradient(135deg,#0a0f1a,#152030); border-color:#60a5fa44; box-shadow:0 0 40px #60a5fa20; }
    .risk-icon { font-size: 3.5rem; margin-bottom: 0.5rem; }
    .risk-label { font-size: 1.8rem; font-weight: 600; margin-bottom: 0.3rem; }
    .risk-emotion { font-size: 1rem; color: #9ca3af; letter-spacing: 0.1em; text-transform: uppercase; }
    .risk-confidence { font-size: 2.5rem; font-weight: 700; margin-top: 1rem; }
    .risk-insight { font-size: 0.9rem; color: #9ca3af; margin-top: 0.8rem; font-style: italic; }
    .remedy-card { background: #12121f; border: 1px solid #2d2d4a; border-radius: 12px; padding: 0.9rem 1.2rem; margin: 0.5rem 0; display: flex; align-items: flex-start; gap: 0.8rem; }
    .remedy-emoji { font-size: 1.4rem; min-width: 2rem; }
    .remedy-text { font-size: 0.88rem; color: #c4c4d4; line-height: 1.5; }
    .stTextArea textarea { background: #12121f !important; border: 1px solid #2d2d4a !important; border-radius: 12px !important; color: #e8e8f0 !important; font-size: 1.05rem !important; padding: 1rem !important; }
    .stButton > button { width: 100%; background: linear-gradient(135deg, #7c3aed, #2563eb) !important; color: white !important; border: none !important; border-radius: 12px !important; padding: 0.8rem 2rem !important; font-size: 1.1rem !important; font-weight: 600 !important; }
    .stTabs [data-baseweb="tab-list"] { background: #12121f; border-radius: 12px; padding: 4px; gap: 4px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px !important; color: #6b7280 !important; font-weight: 500 !important; }
    .stTabs [aria-selected="true"] { background: #1e1e35 !important; color: #a78bfa !important; }
    .disclaimer { background: #12121f; border: 1px solid #2d2d4a; border-radius: 12px; padding: 1rem 1.5rem; color: #6b7280; font-size: 0.85rem; text-align: center; margin-top: 2rem; }
    .metric-box { background: #12121f; border: 1px solid #2d2d4a; border-radius: 12px; padding: 1.2rem; text-align: center; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #a78bfa; }
    .metric-label { font-size: 0.8rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; }
    .lora-badge { display: inline-block; background: #1e1e35; border: 1px solid #7c3aed; color: #a78bfa; padding: 0.3rem 1rem; border-radius: 8px; font-size: 0.85rem; font-weight: 600; margin: 0.2rem; }
    .qlora-badge { display: inline-block; background: #1e2e1e; border: 1px solid #16a34a; color: #34d399; padding: 0.3rem 1rem; border-radius: 8px; font-size: 0.85rem; font-weight: 600; margin: 0.2rem; }
    .crisis-banner { background: linear-gradient(135deg, #2d0a0a, #1a0505); border: 2px solid #ef4444; border-radius: 16px; padding: 1.5rem; margin: 1rem 0; animation: pulse 2s infinite; }
    @keyframes pulse { 0%,100% { box-shadow: 0 0 20px #ef444430; } 50% { box-shadow: 0 0 40px #ef444460; } }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

LABEL_NAMES = ["sadness", "joy", "love", "anger", "fear", "surprise"]
CRISIS_KEYWORDS = ["suicide", "want to die", "end my life", "kill myself", "hurt myself", "no reason to live"]

RISK_CONFIG = {
    "sadness": {
        "level": "HIGH RISK", "icon": "🔴", "color": "#ef4444", "css": "risk-high", "crisis": True,
        "insight": "Persistent sadness is a primary depression indicator",
        "action": "Seek professional support as soon as possible",
        "remedies": [
            ("🌞", "Get 15 mins of morning sunlight every day — naturally boosts serotonin levels"),
            ("🏃", "Walk for 20 mins daily — endorphins released directly fight sadness"),
            ("📓", "Journal your feelings every night — writing helps process deep emotions"),
            ("🧘", "Try 10 min guided meditation — apps like Headspace or Calm can guide you"),
            ("🤝", "Talk to someone you trust — isolation always makes sadness worse"),
            ("📞", "iCall Helpline: 9152987821 — free, confidential professional counseling available"),
        ]
    },
    "anger": {
        "level": "MEDIUM RISK", "icon": "🟠", "color": "#f97316", "css": "risk-medium", "crisis": False,
        "insight": "Anger can indicate underlying emotional distress",
        "action": "Practice emotional regulation techniques daily",
        "remedies": [
            ("💨", "Box breathing: Inhale 4s, Hold 4s, Exhale 4s, repeat 5 times"),
            ("🧊", "Splash cold water on your face — activates your body's natural calming reflex"),
            ("🏋️", "Channel it physically — go for a run, do push-ups, or punch a pillow safely"),
            ("✍️", "Write an unsent letter — express your anger fully without any consequences"),
            ("⏸️", "10-second rule — always pause before reacting to anything that triggers you"),
            ("🎵", "Listen to calming music — 432Hz frequency music is known to reduce cortisol"),
        ]
    },
    "fear": {
        "level": "MEDIUM RISK", "icon": "🟠", "color": "#f97316", "css": "risk-medium", "crisis": False,
        "insight": "Anxiety and fear may benefit from professional support",
        "action": "Use grounding techniques to manage anxiety right now",
        "remedies": [
            ("5️⃣", "5-4-3-2-1 Grounding: Name 5 things you see, 4 hear, 3 touch, 2 smell, 1 taste"),
            ("🧘", "Progressive muscle relaxation — tense then slowly release each muscle group"),
            ("📵", "Limit news and social media — excess consumption amplifies anxiety"),
            ("☕", "Cut back on caffeine — it directly worsens anxiety and panic symptoms"),
            ("🛌", "Fix your sleep schedule — anxiety always spikes with sleep deprivation"),
            ("📋", "Write your fears down then challenge each one with real factual evidence"),
        ]
    },
    "surprise": {
        "level": "LOW RISK", "icon": "🟡", "color": "#eab308", "css": "risk-low", "crisis": False,
        "insight": "Unexpected emotional response detected",
        "action": "Take time to pause and process what surprised you",
        "remedies": [
            ("🧠", "Give yourself time — not every surprise needs an immediate reaction"),
            ("📓", "Journal about what surprised you and why it triggered this response"),
            ("💬", "Talk to a trusted friend about the event to gain a fresh perspective"),
            ("🌿", "Take a short nature walk to reset and calm your nervous system"),
            ("🎯", "Refocus on what is within your control — life is naturally unpredictable"),
            ("😴", "Rest well tonight — unexpected events are more mentally tiring than they seem"),
        ]
    },
    "joy": {
        "level": "NO RISK", "icon": "✅", "color": "#22c55e", "css": "risk-none", "crisis": False,
        "insight": "Positive emotional state detected — keep going!",
        "action": "Protect and nurture this positive energy you have",
        "remedies": [
            ("📓", "Gratitude journal — write 3 things you are grateful for every morning"),
            ("🤗", "Share your joy — positive emotions multiply when shared freely"),
            ("🎯", "Set a new goal today — joy gives you the best fuel to start"),
            ("🌱", "Build a new healthy habit now — easiest to start when mood is high"),
            ("📸", "Capture this moment — photos and memories anchor positive emotions"),
            ("💪", "Help someone today — acts of kindness extend your own joy further"),
        ]
    },
    "love": {
        "level": "NO RISK", "icon": "✅", "color": "#22c55e", "css": "risk-none", "crisis": False,
        "insight": "Positive relational affect detected — nurture these bonds",
        "action": "Invest in and celebrate your meaningful relationships",
        "remedies": [
            ("💌", "Express appreciation to someone you love — a simple message means a lot"),
            ("📵", "Put the phone down during quality time — presence strengthens bonds"),
            ("🍽️", "Share a meal with family or friends — communal eating builds connection"),
            ("💬", "Have a deep conversation — go beyond small talk today"),
            ("🎁", "Do something kind for someone without expecting anything in return"),
            ("🌟", "Reflect on what makes your relationships strong and write it down"),
        ]
    },
}

# ── Model Loading ─────────────────────────────────────────────────────────────
@st.cache_resource
def load_lora():
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    base = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=6, ignore_mismatched_sizes=True)
    model = PeftModel.from_pretrained(base, "models/lora_model/final")
    model.eval()
    return model, tokenizer

@st.cache_resource
def load_qlora():
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    base = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=6, ignore_mismatched_sizes=True)
    model = PeftModel.from_pretrained(base, "models/qlora_model/final")
    model.eval()
    return model, tokenizer

def predict(text, model, tokenizer):
    start = time.time()
    inputs = tokenizer(text, return_tensors="pt", padding='max_length', truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
    elapsed = time.time() - start
    probs = torch.softmax(outputs.logits, dim=-1)[0].tolist()
    pred_id = probs.index(max(probs))
    emotion = LABEL_NAMES[pred_id]
    return {
        "emotion": emotion,
        "confidence": probs[pred_id] * 100,
        "probs": {LABEL_NAMES[i]: probs[i] * 100 for i in range(6)},
        "inference_ms": elapsed * 1000,
        **RISK_CONFIG[emotion]
    }

def prob_chart(result, title):
    emotions = list(result['probs'].keys())
    probs = list(result['probs'].values())
    colors = [RISK_CONFIG[e]['color'] for e in emotions]
    fig = go.Figure(go.Bar(x=emotions, y=probs, marker_color=colors,
        text=[f"{p:.1f}%" for p in probs], textposition='outside',
        textfont=dict(color='#9ca3af', size=10)))
    fig.update_layout(
        title=dict(text=title, font=dict(color='#e8e8f0', size=13)),
        paper_bgcolor='#12121f', plot_bgcolor='#12121f', font=dict(color='#9ca3af'),
        xaxis=dict(gridcolor='#2d2d4a'), yaxis=dict(gridcolor='#2d2d4a', range=[0, max(probs)+15], title="Probability (%)"),
        margin=dict(l=10, r=10, t=40, b=10), height=260, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Model Selection")
    mode = st.radio("Choose Mode:", [
        "🤖 LoRA Only",
        "🌿 QLoRA Only",
        "⚡ Compare LoRA vs QLoRA"
    ], index=0)

    st.markdown("---")
    st.markdown("""
    <div style="background:#12121f;border:1px solid #2d2d4a;border-radius:10px;padding:1rem;font-size:0.82rem;color:#9ca3af;">
    <b style="color:#a78bfa">🤖 LoRA</b><br>
    Params trained: 742K (1.09%)<br>
    Size: 268MB | Precision: 32-bit<br><br>
    <b style="color:#34d399">🌿 QLoRA</b><br>
    Params trained: 742K (1.09%)<br>
    Size: 89MB | Precision: 4-bit NF4<br><br>
    <b style="color:#60a5fa">Both use:</b> distilbert-base-uncased<br>
    Dataset: emotion (2000 samples)<br>
    Training: 3 epochs on CPU
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📝 History")
    if "history" not in st.session_state:
        st.session_state.history = []
    if st.session_state.history:
        for h in reversed(st.session_state.history[-5:]):
            st.markdown(f'<div style="background:#12121f;border:1px solid #2d2d4a;border-radius:8px;padding:0.5rem;margin:0.3rem 0;font-size:0.78rem;color:#9ca3af;">"{h["text"][:28]}..."<br><span style="color:{RISK_CONFIG[h["emotion"]]["color"]}">{h["emotion"].upper()}</span> · {h["model"]} · {h["time"]}</div>', unsafe_allow_html=True)
        if st.button("🗑 Clear History"):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("No history yet")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <div class="main-title">Mental Health Risk Classifier</div>
    <div class="main-subtitle">Powered by LoRA & QLoRA Fine-tuned DistilBERT</div>
    <div class="model-badge">🧠 Compare LoRA vs QLoRA — Live Side by Side</div>
</div>
""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

lora_exists  = os.path.exists("models/lora_model/final")
qlora_exists = os.path.exists("models/qlora_model/final")

if not lora_exists and not qlora_exists:
    st.error("No trained models found! Run 02_lora_finetuning.py and 03_qlora_finetuning.py first.")
    st.stop()

col_in, col_out = st.columns([1.1, 1.9], gap="large")

with col_in:
    st.markdown("### 💬 Enter Your Text")
    user_text = st.text_area("", placeholder="Type how you are feeling...\n\nExample: I feel so empty and hopeless", height=180, label_visibility="collapsed")
    analyze_btn = st.button("🔍 Analyze Now", use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Try an example:**")
    for ex in [
        "I feel so empty and hopeless, nothing makes sense",
        "Today was amazing! I got the promotion I wanted!",
        "I am terrified about what the future holds for me",
        "I love spending time with my family so much"
    ]:
        if st.button(f"→ {ex[:45]}...", key=ex, use_container_width=True):
            user_text = ex
            analyze_btn = True

with col_out:
    if analyze_btn and user_text.strip():

        # Run selected models
        lora_result = qlora_result = None

        run_lora  = (mode == "🤖 LoRA Only") or ("Compare" in mode)
        run_qlora = (mode == "🌿 QLoRA Only") or ("Compare" in mode)

        if run_lora:
            if lora_exists:
                with st.spinner("Running LoRA model..."):
                    lm, lt = load_lora()
                    lora_result = predict(user_text, lm, lt)
            else:
                st.warning("LoRA model not found. Run 02_lora_finetuning.py first.")

        if run_qlora:
            if qlora_exists:
                with st.spinner("Running QLoRA model..."):
                    qm, qt = load_qlora()
                    qlora_result = predict(user_text, qm, qt)
            else:
                st.warning("QLoRA model not found. Run 03_qlora_finetuning.py first.")

        # Save history
        if lora_result or qlora_result:
            r = lora_result or qlora_result
            mn = "LoRA vs QLoRA" if (lora_result and qlora_result) else ("LoRA" if lora_result else "QLoRA")
            st.session_state.history.append({"text": user_text, "emotion": r["emotion"], "model": mn, "time": datetime.datetime.now().strftime("%H:%M")})

        # Crisis check
        is_crisis = any(kw in user_text.lower() for kw in CRISIS_KEYWORDS)
        if lora_result and lora_result.get("crisis") and lora_result["confidence"] > 70:
            is_crisis = True
        if is_crisis:
            st.markdown("""<div class="crisis-banner">
                <div style="font-size:1.3rem;font-weight:700;color:#ef4444;margin-bottom:0.5rem">🚨 CRISIS ALERT</div>
                <div style="color:#fca5a5;font-size:0.9rem;margin-bottom:1rem">You are not alone. Please reach out now.</div>
                <div style="display:flex;gap:1rem;flex-wrap:wrap;">
                    <div style="background:#2d0a0a;border:1px solid #ef4444;border-radius:8px;padding:0.4rem 0.8rem;color:#fca5a5;font-size:0.82rem">📞 iCall: <b>9152987821</b></div>
                    <div style="background:#2d0a0a;border:1px solid #ef4444;border-radius:8px;padding:0.4rem 0.8rem;color:#fca5a5;font-size:0.82rem">📞 Vandrevala: <b>1860-2662-345</b></div>
                    <div style="background:#2d0a0a;border:1px solid #ef4444;border-radius:8px;padding:0.4rem 0.8rem;color:#fca5a5;font-size:0.82rem">📞 NIMHANS: <b>080-46110007</b></div>
                </div></div>""", unsafe_allow_html=True)

        # ── COMPARE MODE ──────────────────────────────────────────────────────
        if "Compare" in mode and lora_result and qlora_result:
            tab1, tab2, tab3 = st.tabs(["⚡ Side by Side", "📈 Probability Charts", "🔬 Detailed Comparison"])

            with tab1:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<div style="text-align:center;margin-bottom:0.5rem"><span class="lora-badge">🤖 LoRA Model</span></div>', unsafe_allow_html=True)
                    st.markdown(f"""<div class="risk-card {lora_result['css']}">
                        <div class="risk-icon">{lora_result['icon']}</div>
                        <div class="risk-label" style="color:{lora_result['color']}">{lora_result['level']}</div>
                        <div class="risk-emotion">{lora_result['emotion']}</div>
                        <div class="risk-confidence" style="color:{lora_result['color']}">{lora_result['confidence']:.1f}%</div>
                        <div class="risk-insight">{lora_result['insight']}</div>
                    </div>""", unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-box"><div class="metric-value" style="color:#6b7280;font-size:1.1rem">⏱ {lora_result["inference_ms"]:.0f} ms</div><div class="metric-label">Inference Time</div></div>', unsafe_allow_html=True)

                with c2:
                    st.markdown('<div style="text-align:center;margin-bottom:0.5rem"><span class="qlora-badge">🌿 QLoRA Model</span></div>', unsafe_allow_html=True)
                    st.markdown(f"""<div class="risk-card {qlora_result['css']}">
                        <div class="risk-icon">{qlora_result['icon']}</div>
                        <div class="risk-label" style="color:{qlora_result['color']}">{qlora_result['level']}</div>
                        <div class="risk-emotion">{qlora_result['emotion']}</div>
                        <div class="risk-confidence" style="color:{qlora_result['color']}">{qlora_result['confidence']:.1f}%</div>
                        <div class="risk-insight">{qlora_result['insight']}</div>
                    </div>""", unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-box"><div class="metric-value" style="color:#6b7280;font-size:1.1rem">⏱ {qlora_result["inference_ms"]:.0f} ms</div><div class="metric-label">Inference Time</div></div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                if lora_result["emotion"] == qlora_result["emotion"]:
                    st.success(f"✅ Both models AGREE — Emotion: **{lora_result['emotion'].upper()}** → **{lora_result['level']}**")
                else:
                    st.warning(f"⚠️ Models DISAGREE — LoRA: **{lora_result['emotion'].upper()}** | QLoRA: **{qlora_result['emotion'].upper()}**")

            with tab2:
                c1, c2 = st.columns(2)
                with c1:
                    prob_chart(lora_result, "🤖 LoRA — Emotion Probabilities")
                with c2:
                    prob_chart(qlora_result, "🌿 QLoRA — Emotion Probabilities")

            with tab3:
                st.markdown("### 🔬 Head-to-Head Comparison")
                st.markdown('<div style="display:grid;grid-template-columns:2fr 2fr 2fr 1fr;gap:0.5rem;padding:0.5rem 0;border-bottom:1px solid #2d2d4a;margin-bottom:0.5rem"><span style="color:#6b7280;font-size:0.8rem;font-weight:600">METRIC</span><span style="color:#a78bfa;font-size:0.8rem;font-weight:600">🤖 LORA</span><span style="color:#34d399;font-size:0.8rem;font-weight:600">🌿 QLORA</span><span style="color:#6b7280;font-size:0.8rem;font-weight:600">STATUS</span></div>', unsafe_allow_html=True)
                rows = [
                    ("Detected Emotion", lora_result["emotion"].upper(), qlora_result["emotion"].upper()),
                    ("Risk Level", lora_result["level"], qlora_result["level"]),
                    ("Confidence", f"{lora_result['confidence']:.1f}%", f"{qlora_result['confidence']:.1f}%"),
                    ("Inference Time", f"{lora_result['inference_ms']:.0f} ms", f"{qlora_result['inference_ms']:.0f} ms"),
                ]
                for metric, lv, qv in rows:
                    same = lv == qv
                    status = '<span style="color:#22c55e;font-size:0.8rem">✓ Same</span>' if same else '<span style="color:#f97316;font-size:0.8rem">⚡ Differ</span>'
                    st.markdown(f'<div style="display:grid;grid-template-columns:2fr 2fr 2fr 1fr;gap:0.5rem;padding:0.6rem 0;border-bottom:1px solid #1a1a2e"><span style="color:#9ca3af;font-size:0.85rem">{metric}</span><span style="color:#a78bfa;font-size:0.85rem;font-weight:600">{lv}</span><span style="color:#34d399;font-size:0.85rem;font-weight:600">{qv}</span>{status}</div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f'<span style="color:{lora_result["color"]};font-weight:700;font-size:1rem">💡 Recommended Remedies</span>', unsafe_allow_html=True)
                for emoji, txt in lora_result['remedies']:
                    st.markdown(f'<div class="remedy-card"><span class="remedy-emoji">{emoji}</span><span class="remedy-text">{txt}</span></div>', unsafe_allow_html=True)

        # ── SINGLE MODEL MODE ─────────────────────────────────────────────────
        else:
            result = lora_result if lora_result else qlora_result
            if result is None:
                st.stop()
            model_name = "LoRA" if lora_result else "QLoRA"
            badge = "lora-badge" if lora_result else "qlora-badge"
            tab1, tab2 = st.tabs(["📊 Simple View", "🔬 Detailed Analysis"])

            with tab1:
                st.markdown(f'<div style="text-align:center;margin-bottom:0.5rem"><span class="{badge}">{"🤖" if model_name=="LoRA" else "🌿"} {model_name} Model</span></div>', unsafe_allow_html=True)
                st.markdown(f"""<div class="risk-card {result['css']}">
                    <div class="risk-icon">{result['icon']}</div>
                    <div class="risk-label" style="color:{result['color']}">{result['level']}</div>
                    <div class="risk-emotion">{result['emotion']}</div>
                    <div class="risk-confidence" style="color:{result['color']}">{result['confidence']:.1f}%</div>
                    <div class="risk-insight">{result['insight']}</div>
                </div>""", unsafe_allow_html=True)
                st.markdown(f'<div style="margin-top:1rem;margin-bottom:0.4rem;"><span style="color:{result["color"]};font-weight:700;font-size:1.05rem;">💡 Recommended Remedies</span><br><span style="color:#6b7280;font-size:0.82rem;">{result["action"]}</span></div>', unsafe_allow_html=True)
                for emoji, txt in result['remedies']:
                    st.markdown(f'<div class="remedy-card"><span class="remedy-emoji">{emoji}</span><span class="remedy-text">{txt}</span></div>', unsafe_allow_html=True)

            with tab2:
                prob_chart(result, f"{'🤖' if model_name=='LoRA' else '🌿'} {model_name} — Emotion Probability Distribution")
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.markdown(f'<div class="metric-box"><div class="metric-value" style="color:{result["color"]}">{result["confidence"]:.1f}%</div><div class="metric-label">Confidence</div></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="metric-box"><div class="metric-value">{result["emotion"].title()}</div><div class="metric-label">Emotion</div></div>', unsafe_allow_html=True)
                with m3:
                    st.markdown(f'<div class="metric-box"><div class="metric-value" style="color:{result["color"]}">{result["icon"]}</div><div class="metric-label">{result["level"]}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div style="margin-top:1.5rem;margin-bottom:0.5rem;"><span style="color:{result["color"]};font-weight:700;font-size:1.05rem;">💡 Recommended Remedies</span></div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                for i, (emoji, txt) in enumerate(result['remedies']):
                    with c1 if i % 2 == 0 else c2:
                        st.markdown(f'<div class="remedy-card"><span class="remedy-emoji">{emoji}</span><span class="remedy-text">{txt}</span></div>', unsafe_allow_html=True)

    elif analyze_btn:
        st.warning("Please enter some text first!")
    else:
        mode_display = mode.replace("🤖 ", "").replace("🌿 ", "").replace("⚡ ", "")
        st.markdown(f'<div style="height:300px;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#12121f;border:1px dashed #2d2d4a;border-radius:16px;color:#4b5563;text-align:center;padding:2rem;"><div style="font-size:3rem;margin-bottom:1rem">🧠</div><div style="font-size:1.1rem;color:#6b7280">Mode: <b style="color:#a78bfa">{mode_display}</b></div><div style="font-size:0.85rem;margin-top:0.5rem">Enter text and click Analyze</div></div>', unsafe_allow_html=True)

st.markdown('<div class="disclaimer">⚠️ <strong>Disclaimer:</strong> For educational purposes only. Not a substitute for professional mental health advice. &nbsp;|&nbsp; <strong>LoRA & QLoRA Fine-tuned DistilBERT</strong></div>', unsafe_allow_html=True)