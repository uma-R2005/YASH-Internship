# 🎨 The Creativity Dial

An interactive AI creative writing studio built with Streamlit that lets you **see in real time** how LLM sampling parameters — Temperature, Top P, and Top K — change the style, tone, and creativity of generated text.

---

## ✨ Features

- **6 writing styles** — Poem, Story Opener, Joke, Tweet/Caption, Horror Scene, Startup Pitch
- **4 quick presets** — Robot Mode, Balanced, Creative, and Chaotic
- **Live mood indicator** that updates as you move the sliders
- **Output history** — compare up to 4 previous generations side-by-side
- **Parameter explainer cards** — learn what Temperature, Top P, and Top K actually do


## 🧠 How It Works

The app sends a prompt to the **Llama 3.1 8B Instant** model via the Groq API, with parameters controlled entirely by the sidebar sliders.

| Parameter | What it controls |
|-----------|-----------------|
| 🌡️ **Temperature** | Randomness of word choice. Low = safe & predictable. High = wild & experimental. |
| 🎯 **Top P** | The cumulative probability threshold for token sampling. Low = only likely words. High = wider vocabulary. |
| 🔢 **Top K** | Number of candidate tokens considered per step. Low = precise. High = diverse. |



## 📁 Project Structure

```
creativity-dial/
├── app.py          # Main Streamlit application
├── .env            # Your API key (not committed to git)
└── README.md
```

---


## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | Web UI framework |
| `groq` | Groq API client |
| `python-dotenv` | Load `.env` for API key |

---

## 🔐 Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Your Groq API key — get one at [console.groq.com](https://console.groq.com/) |

---
