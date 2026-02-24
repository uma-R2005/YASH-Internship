# UPDATED VERSION WITH DYNAMIC SECTIONS
import streamlit as st
import os
import time
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from rouge_score import rouge_scorer

load_dotenv()

st.set_page_config(
    page_title="Domo RFP Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e, #16213e);
        border-right: 1px solid #0f3460;
    }
    .user-bubble {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 18px 18px 4px 18px;
        padding: 14px 18px;
        color: white;
        margin: 8px 0;
        box-shadow: 0 4px 15px rgba(102,126,234,0.4);
        text-align: right;
    }
    .col-header-mistral {
        background: linear-gradient(135deg, #1e3a5f, #0f3460);
        border-radius: 12px 12px 0 0;
        padding: 12px 16px;
        border: 1px solid #667eea;
        border-bottom: none;
        color: white;
        font-weight: 700;
        font-size: 0.95rem;
    }
    .col-body-mistral {
        background: linear-gradient(135deg, #1a1a3e, #1e3a5f);
        border-radius: 0 0 12px 12px;
        padding: 14px 16px;
        border: 1px solid #667eea;
        color: #ccd6f6;
        font-size: 0.88rem;
        min-height: 200px;
    }
    .col-header-web {
        background: linear-gradient(135deg, #1a3a2e, #0f4030);
        border-radius: 12px 12px 0 0;
        padding: 12px 16px;
        border: 1px solid #00b894;
        border-bottom: none;
        color: white;
        font-weight: 700;
        font-size: 0.95rem;
    }
    .col-body-web {
        background: linear-gradient(135deg, #1a2e1a, #1a3a2e);
        border-radius: 0 0 12px 12px;
        padding: 14px 16px;
        border: 1px solid #00b894;
        color: #ccd6f6;
        font-size: 0.88rem;
        min-height: 200px;
    }
    .accuracy-box-mistral {
        background: linear-gradient(135deg, #1e3a5f, #0f3460);
        border-radius: 10px;
        padding: 14px;
        margin: 8px 0;
        border: 1px solid #667eea;
        color: white;
        font-size: 0.85rem;
    }
    .accuracy-box-web {
        background: linear-gradient(135deg, #1a3a2e, #0f4030);
        border-radius: 10px;
        padding: 14px;
        margin: 8px 0;
        border: 1px solid #00b894;
        color: white;
        font-size: 0.85rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #1e3a5f, #0f3460);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        border: 1px solid #0f3460;
    }
    .stat-val { font-size: 1.4rem; font-weight: 700; color: #667eea; }
    .stat-lbl { font-size: 0.75rem; color: #8892b0; margin-top: 4px; }
    .feature-card {
        background: linear-gradient(135deg, #1e3a5f, #0f3460);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border: 1px solid #0f3460;
        color: #ccd6f6;
        font-size: 0.85rem;
    }
    .keyword-tag {
        background: #667eea;
        color: white;
        padding: 3px 10px;
        border-radius: 15px;
        font-size: 0.75rem;
        margin: 3px;
        display: inline-block;
    }
    .deadline-card {
        background: linear-gradient(135deg, #3a1e1e, #601010);
        border-radius: 10px;
        padding: 14px;
        margin: 6px 0;
        border: 1px solid #ff6b6b;
        color: white;
        font-size: 0.85rem;
    }
    .contact-card {
        background: linear-gradient(135deg, #1e3a1e, #104010);
        border-radius: 10px;
        padding: 14px;
        margin: 6px 0;
        border: 1px solid #00b894;
        color: white;
        font-size: 0.85rem;
    }
    .summary-box {
        background: linear-gradient(135deg, #1e2a3a, #0f1e30);
        border-radius: 12px;
        padding: 18px;
        margin: 10px 0;
        border: 1px solid #667eea;
        color: #ccd6f6;
        font-size: 0.88rem;
        line-height: 1.8;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white; border: none; border-radius: 25px;
        padding: 10px 20px; font-weight: 600; width: 100%;
    }
    .tab-content {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-radius: 0 12px 12px 12px;
        padding: 20px;
        border: 1px solid #0f3460;
    }
    #MainMenu {visibility:hidden;}
    footer {visibility:hidden;}
    header {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# Session State
for key, val in {
    "messages": [], "query_engine": None,
    "ready": False, "chunks": 0,
    "process_time": 0, "query_count": 0,
    "summary": "", "key_info": {},
    "analytics": [], "selected_section": "All",
    "language": "English"
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ── Web Knowledge Base ──
def search_web(query: str):
    query_lower = query.lower()
    knowledge_base = {
        "sccm": [
            {"title": "Wikipedia: Microsoft Configuration Manager (SCCM)", "href": "https://en.wikipedia.org/wiki/Microsoft_Configuration_Manager", "body": "Microsoft Endpoint Configuration Manager (formerly SCCM) is a systems management software product developed by Microsoft for managing large groups of computers. It provides remote control, patch management, software distribution, operating system deployment, network access protection, and hardware and software inventory."},
            {"title": "Wikipedia: Patch Management", "href": "https://en.wikipedia.org/wiki/Patch_(computing)", "body": "Patch management is the process of distributing and applying updates to software. SCCM automates the patching of workstations and servers, ensuring third-party software like Chrome, Adobe, and Office are updated regularly."},
            {"title": "Wikipedia: Microsoft Intune", "href": "https://en.wikipedia.org/wiki/Microsoft_Intune", "body": "Microsoft Intune is a cloud-based service that focuses on mobile device management (MDM) and mobile application management (MAM). It allows IT administrators to manage and secure company devices and applications."}
        ],
        "goals": [
            {"title": "Wikipedia: Request for Proposal", "href": "https://en.wikipedia.org/wiki/Request_for_proposal", "body": "A Request for Proposal (RFP) is a business document that announces a project, describes it, and solicits bids from qualified contractors to complete it."},
            {"title": "Wikipedia: IT Infrastructure", "href": "https://en.wikipedia.org/wiki/IT_infrastructure", "body": "IT infrastructure refers to the composite hardware, software, network resources and services required for the existence, operation and management of an enterprise IT environment."},
            {"title": "Wikipedia: IT Governance", "href": "https://en.wikipedia.org/wiki/IT_governance", "body": "IT governance is a subset of corporate governance focused on information technology systems and their performance and risk management."}
        ],
        "cybersecurity": [
            {"title": "Wikipedia: Cybersecurity", "href": "https://en.wikipedia.org/wiki/Computer_security", "body": "Cybersecurity is the practice of protecting systems, networks, and programs from digital attacks. Best practices include MFA, SIEM monitoring, API security, and conditional access policies."},
            {"title": "Wikipedia: SIEM", "href": "https://en.wikipedia.org/wiki/Security_information_and_event_management", "body": "Security Information and Event Management (SIEM) aggregates and analyzes activity from security sources to detect threats, create alerts, and support compliance requirements."},
            {"title": "Wikipedia: Multi-Factor Authentication", "href": "https://en.wikipedia.org/wiki/Multi-factor_authentication", "body": "Multi-factor authentication (MFA) is an authentication method that requires the user to provide two or more verification factors to gain access to a resource."}
        ],
        "governance": [
            {"title": "Wikipedia: IT Governance", "href": "https://en.wikipedia.org/wiki/IT_governance", "body": "IT governance provides a structure for aligning IT strategy with business strategy. It involves defining policies, procedures, and controls for managing IT resources."},
            {"title": "Wikipedia: ITSM", "href": "https://en.wikipedia.org/wiki/IT_service_management", "body": "IT Service Management (ITSM) refers to the entirety of activities directed by policies, organized and structured in processes, performed by an organization to plan, design, deliver, operate and control IT services."},
            {"title": "Wikipedia: ITIL", "href": "https://en.wikipedia.org/wiki/ITIL", "body": "ITIL (Information Technology Infrastructure Library) is a set of detailed practices for IT service management that focuses on aligning IT services with business needs."}
        ],
        "azure": [
            {"title": "Wikipedia: Microsoft Azure", "href": "https://en.wikipedia.org/wiki/Microsoft_Azure", "body": "Microsoft Azure is a cloud computing service operated by Microsoft for application management via Microsoft-managed data centers."},
            {"title": "Wikipedia: Cloud Computing", "href": "https://en.wikipedia.org/wiki/Cloud_computing", "body": "Cloud computing is the on-demand availability of computer system resources, especially data storage and computing power, without direct active management by the user."},
            {"title": "Wikipedia: Azure API Management", "href": "https://en.wikipedia.org/wiki/API_management", "body": "API management is the process of creating and publishing web APIs, enforcing their usage policies, controlling access, and collecting analytics."}
        ],
        "fte": [
            {"title": "Wikipedia: Full-Time Equivalent", "href": "https://en.wikipedia.org/wiki/Full-time_equivalent", "body": "A full-time equivalent (FTE) is a unit that indicates the workload of an employed person. FTE of 1.0 means a person is equivalent to a full-time worker."},
            {"title": "Wikipedia: Managed Services", "href": "https://en.wikipedia.org/wiki/Managed_services", "body": "Managed services is the practice of outsourcing responsibility for maintaining, and anticipating need for, a range of processes and functions."},
            {"title": "Wikipedia: IT Outsourcing", "href": "https://en.wikipedia.org/wiki/IT_outsourcing", "body": "IT outsourcing is the use of external service providers to effectively deliver IT-enabled business process, application service, and infrastructure solutions."}
        ],
    }
    for keyword, entries in knowledge_base.items():
        if keyword in query_lower:
            return entries
    return [
        {"title": "Wikipedia: IT Infrastructure", "href": "https://en.wikipedia.org/wiki/IT_infrastructure", "body": "IT infrastructure refers to the composite hardware, software, network resources and services required for the existence, operation and management of an enterprise IT environment."},
        {"title": "Wikipedia: Request for Proposal", "href": "https://en.wikipedia.org/wiki/Request_for_proposal", "body": "A Request for Proposal (RFP) is a business document that announces a project and solicits bids from qualified contractors."},
        {"title": "Wikipedia: IT Service Management", "href": "https://en.wikipedia.org/wiki/IT_service_management", "body": "IT Service Management (ITSM) refers to the entirety of activities directed by policies to plan, design, deliver, operate and control IT services."}
    ]


# ── ROUGE Score ──
def compute_rouge(hypothesis: str, reference: str):
    try:
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        scores = scorer.score(reference, hypothesis)
        r1 = round(scores['rouge1'].fmeasure * 100, 2)
        r2 = round(scores['rouge2'].fmeasure * 100, 2)
        rl = round(scores['rougeL'].fmeasure * 100, 2)
        overall = round((r1 + r2 + rl) / 3, 2)
        return {"R1": r1, "R2": r2, "RL": rl, "Overall": overall}
    except:
        return {"R1": 0, "R2": 0, "RL": 0, "Overall": 0}


def score_color(score):
    if score >= 50:
        return "#00b894"
    elif score >= 25:
        return "#fdcb6e"
    return "#ff6b6b"


# ── Export Chat ──
def export_chat_txt(messages):
    lines = ["DOMO RFP BOT - CHAT HISTORY", "="*50, ""]
    for msg in messages:
        if msg["role"] == "user":
            lines.append("USER: " + msg["content"])
        else:
            lines.append("BOT: " + msg["content"])
        lines.append("-"*40)
    return "\n".join(lines)


def export_chat_csv(messages):
    rows = []
    for msg in messages:
        rows.append({
            "Role": msg["role"],
            "Message": msg["content"],
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    return pd.DataFrame(rows).to_csv(index=False)


# ── Key Info Extractor ──
def extract_key_info(query_engine):
    info = {}
    questions = {
        "deadline": "What is the proposal submission deadline?",
        "contacts": "Who are the contact persons at Domo Chemicals with their email?",
        "fte_section5": "How many FTEs are needed for Section 5?",
        "fte_section6": "How many FTEs are needed for Section 6?",
        "work_model": "Is this remote work or onsite work?",
        "pricing": "What type of pricing model is required - fixed cost or variable?",
        "duration": "What is the project duration or timeline?",
    }
    for key, question in questions.items():
        try:
            response = query_engine.query(question)
            info[key] = str(response)
            time.sleep(1)
        except:
            info[key] = "Could not extract"
    return info


# ── Multilingual prompt wrapper ──
def get_language_prompt(language: str) -> str:
    prompts = {
        "English": "",
        "French": " Please respond in French.",
        "Spanish": " Please respond in Spanish.",
        "German": " Please respond in German.",
        "Hindi": " Please respond in Hindi.",
        "Arabic": " Please respond in Arabic.",
    }
    return prompts.get(language, "")


# ── SIDEBAR ──
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:15px 0;'>
        <div style='font-size:2.5rem'>🤖</div>
        <div style='font-size:1.1rem; font-weight:700;
                    background:linear-gradient(135deg,#667eea,#764ba2);
                    -webkit-background-clip:text;
                    -webkit-text-fill-color:transparent;'>
            Domo RFP Intelligence
        </div>
        <div style='font-size:0.7rem; color:#8892b0;'>
            Mistral-7B · LlamaIndex · FAISS
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("""
    <div style='background:#1e3a5f; border-radius:10px;
                padding:14px; border:1px solid #0f3460;
                font-size:0.8rem; line-height:2; color:#ccd6f6;'>
        🤖 <b>LLM:</b> Mistral-7B-Instruct-v0.2<br>
        🔢 <b>Embeddings:</b> all-MiniLM-L6-v2<br>
        💾 <b>Vector DB:</b> FAISS (384 dims)<br>
        🌐 <b>Web Search:</b> Wikipedia KB<br>
        📊 <b>Accuracy:</b> ROUGE Score
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # Upload PDF
    st.markdown("### 📄 Upload Document")
    pdf = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
    if pdf:
        save_path = f"temp_{pdf.name}"
        with open(save_path, "wb") as f:
            f.write(pdf.getbuffer())
        st.success(f"✅ {pdf.name} uploaded")

        if st.button("🚀 Process & Build Vector DB"):
            from ingest import ingest
            prog = st.progress(0, "Loading PDF...")
            time.sleep(0.3); prog.progress(25, "Chunking...")
            time.sleep(0.3); prog.progress(50, "Generating vectors...")
            time.sleep(0.3); prog.progress(75, "Saving FAISS...")
            start = time.time()
            index, total = ingest(save_path)
            elapsed = round(time.time() - start, 2)
            prog.progress(90, "Loading Mistral...")
            from bot import load_bot
            query_engine, _ = load_bot()
            prog.progress(100, "Done!"); time.sleep(0.3); prog.empty()
            st.session_state.query_engine = query_engine
            st.session_state.ready = True
            st.session_state.chunks = total
            st.session_state.process_time = elapsed
            st.session_state.messages = []
            st.session_state.summary = ""
            st.session_state.key_info = {}
            st.success(f"✅ Ready in {elapsed}s!")

    if os.path.exists("storage") and not st.session_state.ready:
        if st.button("📂 Load Existing Vector DB"):
            from bot import load_bot
            with st.spinner("Loading..."):
                query_engine, _ = load_bot()
                st.session_state.query_engine = query_engine
                st.session_state.ready = True
            st.success("✅ Loaded!")

    st.divider()

    # Language Selector
    st.markdown("### 🌍 Response Language")
    st.session_state.language = st.selectbox(
        "Language",
        ["English", "French", "Spanish", "German", "Hindi", "Arabic"],
        label_visibility="collapsed"
    )

    st.divider()

    # Section Filter
    if st.session_state.ready:
        st.markdown("### 🔍 Filter by Section")
        st.session_state.selected_section = st.selectbox(
            "Section",
            ["All", "Section 5 - L2/L3 IT Infra", "Section 6 - Governance", "Section 7 - Supplier Mgmt"],
            label_visibility="collapsed"
        )
        st.divider()

    # Stats
    if st.session_state.ready:
        st.markdown("### 📊 Stats")
        st.markdown(f"""
        <div style='font-size:0.82rem; color:#8892b0; line-height:2;'>
            📦 Chunks: <b style='color:white'>{st.session_state.chunks}</b><br>
            ⏱️ Time: <b style='color:white'>{st.session_state.process_time}s</b><br>
            💬 Queries: <b style='color:white'>{st.session_state.query_count}</b>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Export Buttons
        if st.session_state.messages:
            st.markdown("### 📥 Export Chat")
            chat_txt = export_chat_txt(st.session_state.messages)
            st.download_button(
                "📄 Export as TXT",
                data=chat_txt,
                file_name="chat_history.txt",
                mime="text/plain",
                use_container_width=True
            )
            chat_csv = export_chat_csv(st.session_state.messages)
            st.download_button(
                "📊 Export as CSV",
                data=chat_csv,
                file_name="chat_history.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.query_count = 0
            st.session_state.analytics = []
            st.rerun()


# ── MAIN AREA ──
st.markdown("""
<div style='text-align:center; padding:10px 0 20px 0;'>
    <h1 style='background:linear-gradient(135deg,#667eea,#764ba2);
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;
               font-size:2rem; margin:0;'>
        🤖 Domo RFP Intelligence Bot
    </h1>
    <p style='color:#8892b0; margin:5px 0; font-size:0.88rem;'>
        Mistral-7B · LlamaIndex · FAISS · ROUGE Accuracy · Multi-Language
    </p>
</div>
""", unsafe_allow_html=True)

# Stat Cards
c1, c2, c3, c4, c5 = st.columns(5)
for val, lbl, col in [
    ("Mistral-7B", "LLM Model", c1),
    ("FAISS", "Vector DB", c2),
    ("ROUGE", "Accuracy", c3),
    (str(st.session_state.query_count), "Queries", c4),
    (st.session_state.language[:3], "Language", c5),
]:
    with col:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-val'>{val}</div>
            <div class='stat-lbl'>{lbl}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if not st.session_state.ready:
    st.markdown("""
    <div style='text-align:center; padding:50px 20px;'>
        <div style='font-size:3rem'>📄</div>
        <div style='font-size:1.3rem; color:#667eea; font-weight:600; margin:15px 0;'>
            Upload your RFP PDF to get started
        </div>
        <div style='color:#8892b0;'>Upload PDF → Process → Ask Questions</div>
    </div>
    """, unsafe_allow_html=True)

else:
    # ── TABS ──
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Chat",
        "📋 Summary",
        "🔑 Key Info",
        "📅 Deadlines & Contacts",
        "📊 Analytics"
    ])

    # ── TAB 1: CHAT ──
    with tab1:
        for idx, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                st.markdown(f"""
                <div style='display:flex; justify-content:flex-end; margin:10px 0;'>
                    <div class='user-bubble'>👤 {msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                col_m, col_w = st.columns(2)

                with col_m:
                    st.markdown("""
                    <div class='col-header-mistral'>
                        🤖 Mistral Approach
                        <span style='font-size:0.72rem; color:#8892b0; font-weight:400;'>
                        (PDF-based RAG)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class='col-body-mistral'>{msg["content"]}</div>
                    """, unsafe_allow_html=True)

                    if st.button("📊 Check Mistral Accuracy", key=f"m_acc_{idx}"):
                        if msg.get("sources"):
                            ref = " ".join([s["text"] for s in msg["sources"]])
                            sc = compute_rouge(msg["content"], ref)
                            clr = score_color(sc['Overall'])
                            st.markdown(f"""
                            <div class='accuracy-box-mistral'>
                                <b>📊 Mistral ROUGE Accuracy</b><br><br>
                                ROUGE-1: <b style='color:#667eea'>{sc['R1']}%</b><br>
                                ROUGE-2: <b style='color:#667eea'>{sc['R2']}%</b><br>
                                ROUGE-L: <b style='color:#667eea'>{sc['RL']}%</b><br><br>
                                Overall: <b style='color:{clr}; font-size:1.3rem'>{sc['Overall']}%</b><br>
                                <small style='color:#8892b0'>
                                🟢 50%+ Good | 🟡 25-50% Moderate | 🔴 &lt;25% Low
                                </small>
                            </div>
                            """, unsafe_allow_html=True)

                    if msg.get("sources"):
                        with st.expander("📄 View PDF Source Chunks"):
                            for i, src in enumerate(msg["sources"]):
                                st.markdown(f"""
                                <div style='background:#1a1a3e; border-left:3px solid #667eea;
                                            border-radius:8px; padding:10px; margin:6px 0;
                                            font-size:0.8rem; color:#ccd6f6;'>
                                    <b>Chunk {i+1}</b> | Score: {src['score']}<br><br>
                                    {src['text'][:300]}...
                                </div>
                                """, unsafe_allow_html=True)

                with col_w:
                    st.markdown("""
                    <div class='col-header-web'>
                        🌐 Trusted External Sources
                        <span style='font-size:0.72rem; color:#8892b0; font-weight:400;'>
                        (Wikipedia Knowledge Base)</span>
                    </div>
                    """, unsafe_allow_html=True)

                    web_results = msg.get("web_results", [])
                    if web_results:
                        for i, r in enumerate(web_results):
                            st.markdown(f"""
<div style='background:#0f2a1e; border-left:3px solid #00b894;
            border-radius:8px; padding:12px 14px; margin:8px 0;
            font-size:0.85rem; color:#ccd6f6;'>
    <div style='color:#00b894; font-weight:700; margin-bottom:6px;'>
        📰 Source {i+1}: {r.get('title','')}
    </div>
    <div style='font-size:0.75rem; margin-bottom:8px;'>
        🔗 <a href='{r.get("href","#")}' target='_blank'
             style='color:#55efc4;'>{r.get("href","")}</a>
    </div>
    <div style='line-height:1.6;'>{r.get("body","")}</div>
</div>
                            """, unsafe_allow_html=True)

                    if web_results and msg.get("sources"):
                        if st.button("🌐 Check Web Accuracy", key=f"w_acc_{idx}"):
                            ref = " ".join([s["text"] for s in msg["sources"]])
                            combined = " ".join([r.get('body', '') for r in web_results])
                            sc = compute_rouge(combined, ref)
                            clr = score_color(sc['Overall'])
                            st.markdown(f"""
                            <div class='accuracy-box-web'>
                                <b>🌐 Web ROUGE Accuracy</b><br><br>
                                ROUGE-1: <b style='color:#00b894'>{sc['R1']}%</b><br>
                                ROUGE-2: <b style='color:#00b894'>{sc['R2']}%</b><br>
                                ROUGE-L: <b style='color:#00b894'>{sc['RL']}%</b><br><br>
                                Overall: <b style='color:{clr}; font-size:1.3rem'>{sc['Overall']}%</b>
                            </div>
                            """, unsafe_allow_html=True)

                st.markdown("<hr style='border-color:#0f3460; margin:20px 0;'>", unsafe_allow_html=True)

        # Chat Input
        user_input = st.chat_input("Ask anything about the Domo RFP...")

        if user_input:
            # Add section filter to query
            section_context = ""
            if st.session_state.selected_section != "All":
                section_context = " Focus on " + st.session_state.selected_section + "."

            lang_prompt = get_language_prompt(st.session_state.language)
            full_query = user_input + section_context + lang_prompt

            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.query_count += 1
            st.session_state.analytics.append({
                "question": user_input,
                "time": datetime.now().strftime("%H:%M:%S"),
                "section": st.session_state.selected_section
            })

            with st.spinner("Searching PDF + Web..."):
                mistral_answer = ""
                sources = []
                for attempt in range(3):
                    try:
                        response = st.session_state.query_engine.query(full_query)
                        mistral_answer = str(response)
                        if not mistral_answer.strip():
                            mistral_answer = "Could not find a specific answer. Please rephrase."
                        if hasattr(response, "source_nodes"):
                            for node in response.source_nodes:
                                sources.append({
                                    "text": node.text,
                                    "score": round(node.score, 4) if node.score else "N/A"
                                })
                        break
                    except Exception:
                        if attempt < 2:
                            time.sleep(5)
                        else:
                            mistral_answer = "Mistral temporarily unavailable. Please try again."

                web_results = search_web(user_input)

            st.session_state.messages.append({
                "role": "assistant",
                "content": mistral_answer,
                "sources": sources,
                "web_results": web_results
            })
            st.rerun()

    # ── TAB 2: SUMMARY ──
    with tab2:
        st.markdown("### 📋 Document Summary Generator")

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("📋 Generate Full Summary", use_container_width=True):
                with st.spinner("Generating summary..."):
                    try:
                        response = st.session_state.query_engine.query(
                            "Give a comprehensive summary of this entire RFP document. "
                            "Include the main objectives, sections, FTE requirements, "
                            "timeline, and key deliverables."
                        )
                        st.session_state.summary = str(response)
                    except:
                        st.session_state.summary = "Could not generate summary. Please try again."

        with col_s2:
            if st.button("📌 Generate Executive Summary", use_container_width=True):
                with st.spinner("Generating executive summary..."):
                    try:
                        response = st.session_state.query_engine.query(
                            "Generate a brief 3-5 sentence executive summary of this RFP "
                            "suitable for senior management."
                        )
                        st.session_state.summary = str(response)
                    except:
                        st.session_state.summary = "Could not generate summary. Please try again."

        if st.session_state.summary:
            st.markdown(f"""
            <div class='summary-box'>
                <b style='color:#667eea; font-size:1rem;'>📋 Summary</b><br><br>
                {st.session_state.summary}
            </div>
            """, unsafe_allow_html=True)

            st.download_button(
                "📥 Download Summary",
                data=st.session_state.summary,
                file_name="rfp_summary.txt",
                mime="text/plain",
                use_container_width=True
            )

        # Section Summaries
        st.markdown("### 📂 Section-wise Summary")
        sections = {
            "Section 5 - L2/L3 IT Infrastructure": "Summarize Section 5 about L2/L3 IT Infrastructure capabilities including FTE requirements and tasks.",
            "Section 6 - Governance Support": "Summarize Section 6 about Governance Support including FTE requirements and deliverables.",
            "Section 7 - Supplier Relationship": "Summarize Section 7 about Supplier Relationship Management and cybersecurity requirements."
        }
        for section_name, question in sections.items():
            if st.button(f"📄 {section_name}", use_container_width=True):
                with st.spinner(f"Summarizing {section_name}..."):
                    try:
                        response = st.session_state.query_engine.query(question)
                        st.markdown(f"""
                        <div class='summary-box'>
                            <b style='color:#667eea'>{section_name}</b><br><br>
                            {str(response)}
                        </div>
                        """, unsafe_allow_html=True)
                    except:
                        st.error("Could not generate section summary.")

    # ── TAB 3: KEY INFO ──
    with tab3:
        st.markdown("### 🔑 Key Information Extractor")
        st.markdown("<p style='color:#8892b0;'>Auto-extract important details from the RFP document</p>", unsafe_allow_html=True)

        if st.button("🔍 Extract All Key Information", use_container_width=True):
            with st.spinner("Extracting key information... This takes 1-2 mins..."):
                st.session_state.key_info = extract_key_info(st.session_state.query_engine)

        if st.session_state.key_info:
            info = st.session_state.key_info
            labels = {
                "deadline": ("📅 Proposal Deadline", "#ff6b6b"),
                "contacts": ("👤 Contact Persons", "#00b894"),
                "fte_section5": ("👥 FTEs - Section 5", "#667eea"),
                "fte_section6": ("👥 FTEs - Section 6", "#667eea"),
                "work_model": ("🏠 Work Model", "#fdcb6e"),
                "pricing": ("💰 Pricing Model", "#a29bfe"),
                "duration": ("⏱️ Project Duration", "#74b9ff"),
            }

            for key, (label, color) in labels.items():
                if key in info:
                    st.markdown(f"""
                    <div style='background:#1a1a3e; border-left:4px solid {color};
                                border-radius:10px; padding:14px; margin:8px 0;
                                color:#ccd6f6; font-size:0.88rem;'>
                        <b style='color:{color}'>{label}</b><br><br>
                        {info[key]}
                    </div>
                    """, unsafe_allow_html=True)

            # Export Key Info
            if st.session_state.key_info:
                info_text = "\n".join([
                    f"{labels.get(k, (k,''))[0]}: {v}"
                    for k, v in st.session_state.key_info.items()
                ])
                st.download_button(
                    "📥 Download Key Information",
                    data=info_text,
                    file_name="rfp_key_info.txt",
                    mime="text/plain",
                    use_container_width=True
                )

        # Quick Questions
        st.markdown("### ⚡ Quick Questions")
        quick_questions = [
            "What is the proposal deadline?",
            "Who are the Domo contacts?",
            "How many total FTEs are needed?",
            "Is this remote or onsite work?",
            "What is the pricing model?",
            "What technologies are mentioned?",
        ]
        q1, q2 = st.columns(2)
        for i, q in enumerate(quick_questions):
            with (q1 if i % 2 == 0 else q2):
                if st.button(q, use_container_width=True, key=f"qq_{i}"):
                    with st.spinner("Fetching answer..."):
                        try:
                            response = st.session_state.query_engine.query(q)
                            st.markdown(f"""
                            <div class='summary-box'>
                                <b style='color:#667eea'>Q: {q}</b><br><br>
                                {str(response)}
                            </div>
                            """, unsafe_allow_html=True)
                        except:
                            st.error("Could not get answer.")

    # ── TAB 4: DEADLINES & CONTACTS ──
    with tab4:
        st.markdown("### 📅 Deadlines & Important Dates")

        if st.button("🔍 Find All Deadlines", use_container_width=True):
            with st.spinner("Extracting deadlines..."):
                try:
                    response = st.session_state.query_engine.query(
                        "List all deadlines, dates, and timelines mentioned in this RFP document."
                    )
                    st.markdown(f"""
                    <div class='deadline-card'>
                        <b>📅 Deadlines & Dates</b><br><br>
                        {str(response)}
                    </div>
                    """, unsafe_allow_html=True)
                except:
                    st.error("Could not extract deadlines.")

        st.markdown("### 👤 Contact Information")

        if st.button("🔍 Find All Contacts", use_container_width=True):
            with st.spinner("Extracting contacts..."):
                try:
                    response = st.session_state.query_engine.query(
                        "List all contact persons, their names, email addresses, "
                        "and roles mentioned in the RFP document."
                    )
                    st.markdown(f"""
                    <div class='contact-card'>
                        <b>👤 Contacts</b><br><br>
                        {str(response)}
                    </div>
                    """, unsafe_allow_html=True)
                except:
                    st.error("Could not extract contacts.")

        st.markdown("### 📧 Generate Response Email")

        if st.button("✉️ Generate Proposal Response Email", use_container_width=True):
            with st.spinner("Generating email..."):
                try:
                    response = st.session_state.query_engine.query(
                        "Draft a professional response email to this RFP from a vendor perspective. "
                        "Include: subject line, opening, brief capability overview, "
                        "and request for further discussion."
                    )
                    email_text = str(response)
                    st.markdown(f"""
                    <div class='summary-box'>
                        <b style='color:#667eea'>✉️ Draft Email</b><br><br>
                        {email_text}
                    </div>
                    """, unsafe_allow_html=True)
                    st.download_button(
                        "📥 Download Email Draft",
                        data=email_text,
                        file_name="rfp_response_email.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                except:
                    st.error("Could not generate email.")

        st.markdown("### 📊 Generate Proposal Checklist")

        if st.button("✅ Generate Proposal Checklist", use_container_width=True):
            with st.spinner("Generating checklist..."):
                try:
                    response = st.session_state.query_engine.query(
                        "Create a checklist of all requirements a vendor must fulfill "
                        "to respond to this RFP successfully."
                    )
                    st.markdown(f"""
                    <div class='summary-box'>
                        <b style='color:#667eea'>✅ Proposal Checklist</b><br><br>
                        {str(response)}
                    </div>
                    """, unsafe_allow_html=True)
                except:
                    st.error("Could not generate checklist.")

    # ── TAB 5: ANALYTICS ──
    with tab5:
        st.markdown("### 📊 Usage Analytics")

        if st.session_state.analytics:
            df = pd.DataFrame(st.session_state.analytics)

            col_a1, col_a2, col_a3 = st.columns(3)
            with col_a1:
                st.markdown(f"""
                <div class='stat-card'>
                    <div class='stat-val'>{len(df)}</div>
                    <div class='stat-lbl'>Total Queries</div>
                </div>
                """, unsafe_allow_html=True)
            with col_a2:
                most_section = df["section"].mode()[0] if len(df) > 0 else "N/A"
                st.markdown(f"""
                <div class='stat-card'>
                    <div class='stat-val' style='font-size:0.9rem'>{most_section[:10]}</div>
                    <div class='stat-lbl'>Most Used Section</div>
                </div>
                """, unsafe_allow_html=True)
            with col_a3:
                st.markdown(f"""
                <div class='stat-card'>
                    <div class='stat-val'>{st.session_state.language[:3]}</div>
                    <div class='stat-lbl'>Current Language</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📋 Query History")
            st.dataframe(
                df[["time", "question", "section"]].rename(columns={
                    "time": "Time",
                    "question": "Question",
                    "section": "Section"
                }),
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "📥 Download Analytics Report",
                data=df.to_csv(index=False),
                file_name="rfp_analytics.csv",
                mime="text/csv",
                use_container_width=True
            )

            # Most frequent keywords
            st.markdown("### 🏷️ Frequent Keywords")
            all_questions = " ".join(df["question"].tolist()).lower()
            keywords = ["sccm", "fte", "deadline", "contact", "governance",
                        "azure", "cybersecurity", "section 5", "section 6",
                        "intune", "backup", "active directory"]
            found = [k for k in keywords if k in all_questions]
            if found:
                tags = " ".join([f"<span class='keyword-tag'>{k}</span>" for k in found])
                st.markdown(tags, unsafe_allow_html=True)

        else:
            st.markdown("""
            <div style='text-align:center; padding:40px; color:#8892b0;'>
                <div style='font-size:2rem'>📊</div>
                <p>No queries yet. Start chatting to see analytics!</p>
            </div>
            """, unsafe_allow_html=True)