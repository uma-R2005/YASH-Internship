# ================================================
#  Crime & Case Analyzer - Web UI
#  Built with Streamlit
#  Run: streamlit run app.py
# ================================================

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
from langchain_chroma import Chroma
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_core.documents import Document
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from transformers import pipeline as hf_pipeline

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="🕵️ Crime Case Analyzer",
    page_icon="🕵️",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTextInput > div > div > input {
        background-color: #1e2130;
        color: white;
        border: 1px solid #e74c3c;
        border-radius: 8px;
        font-size: 16px;
    }
    .case-card {
        background-color: #1a1d2e;
        border-left: 4px solid #e74c3c;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }
    .match-badge {
        background-color: #e74c3c;
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: bold;
    }
    .type-badge {
        background-color: #2c3e50;
        color: #e74c3c;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        border: 1px solid #e74c3c;
    }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.markdown("# 🕵️ Crime & Case Analyzer")
st.markdown("**Powered by CrossEncoder Reranking + Multi-Query Retriever**")
st.markdown("---")

# ─────────────────────────────────────────────
# CASE DATA
# ─────────────────────────────────────────────

cases = [
    Document(page_content="""Case #001 - Harbor Robbery
        Date: 2023-11-15 | Location: Dockside Warehouse, Harbor District
        Suspect: Male, dark hoodie, red duffle bag, approximately 6ft tall.
        Witness reported seeing suspect running toward the harbor at 11:45pm.
        Evidence: Broken lock, footprints near dock 7, CCTV footage partial.
        Status: Unsolved.""", metadata={"case_id": "001", "type": "Robbery"}),

    Document(page_content="""Case #002 - Downtown Jewelry Heist
        Date: 2023-10-05 | Location: Goldmark Jewelers, Main Street
        Suspect: Two individuals, black masks, armed with crowbars.
        Alarm triggered at 2:30am. Neighbor heard glass breaking.
        Evidence: Crowbar left at scene, glove print on display case.
        Status: One suspect arrested.""", metadata={"case_id": "002", "type": "Heist"}),

    Document(page_content="""Case #003 - Midnight Smuggling Ring
        Date: 2023-09-20 | Location: Port Authority, Pier 12
        Suspect: Group of 4, seen unloading unmarked crates at midnight.
        Dark clothing, one suspect in hoodie with a large bag.
        Evidence: Contraband goods, shipping manifest discrepancy.
        Status: Under investigation.""", metadata={"case_id": "003", "type": "Smuggling"}),

    Document(page_content="""Case #004 - Residential Burglary
        Date: 2023-08-10 | Location: Elm Street Neighborhood
        Suspect: Unknown, entered through back window during daytime.
        Neighbor saw unfamiliar white sedan parked outside.
        Evidence: Fingerprints on window sill, stolen electronics.
        Status: Unsolved.""", metadata={"case_id": "004", "type": "Burglary"}),

    Document(page_content="""Case #005 - Warehouse Arson
        Date: 2023-07-25 | Location: Industrial Zone, Block 9
        Suspect: Tall male, dark jacket, seen leaving area before fire.
        Fire started near storage room at 1:00am.
        Evidence: Accelerant traces, partial shoe print near exit.
        Status: Suspect identified, warrant issued.""", metadata={"case_id": "005", "type": "Arson"}),

    Document(page_content="""Case #006 - Waterfront Assault
        Date: 2023-06-18 | Location: Riverside Walk, near Docks
        Suspect: Male in dark hoodie, medium build, carrying a bag.
        Victim attacked near the waterfront at 11:00pm.
        Evidence: Victim's phone recovered, witness sketch created.
        Status: Unsolved.""", metadata={"case_id": "006", "type": "Assault"}),

    Document(page_content="""Case #007 - Bank Fraud
        Date: 2023-05-30 | Location: City Central Bank
        Suspect: Well-dressed individual, forged documents used.
        Transactions flagged during morning audit.
        Evidence: Fake ID, digital transaction logs.
        Status: Suspect in custody.""", metadata={"case_id": "007", "type": "Fraud"}),

    Document(page_content="""Case #008 - Vehicle Theft Ring
        Date: 2023-04-12 | Location: Multiple parking lots, East Side
        Suspect: Group using signal jammers to steal high-end cars at night.
        Mostly operated between 10pm and 2am.
        Evidence: Jammer device recovered, tire tracks at lot 3.
        Status: Under investigation.""", metadata={"case_id": "008", "type": "Theft"}),

    Document(page_content="""Case #009 - Cargo Theft at Airport
        Date: 2023-03-08 | Location: City Airport, Cargo Bay B
        Suspect: Airport employee badge used after hours at midnight.
        Suspect seen on CCTV wearing dark uniform and carrying large bag.
        Evidence: Badge logs, CCTV footage, missing cargo manifest.
        Status: Employee suspended, case active.""", metadata={"case_id": "009", "type": "Theft"}),

    Document(page_content="""Case #010 - Drug Operation Bust
        Date: 2023-02-14 | Location: Abandoned Factory, Harbor Road
        Suspect: Multiple individuals, night-time operations near harbor.
        Lookout spotted in dark hoodie near entrance at midnight.
        Evidence: Seized substances, communication devices, maps of dock area.
        Status: 3 arrested, 2 at large.""", metadata={"case_id": "010", "type": "Drugs"}),
]

# ─────────────────────────────────────────────
# LOAD PIPELINE (cached so it loads only once)
# ─────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_pipeline():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vectorstore = Chroma.from_documents(documents=cases, embedding=embeddings)
    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    text_gen = hf_pipeline("text2text-generation", model="google/flan-t5-base", max_new_tokens=128)
    llm = HuggingFacePipeline(pipeline=text_gen)
    multi_query_retriever = MultiQueryRetriever.from_llm(retriever=base_retriever, llm=llm)

    cross_encoder = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    reranker = CrossEncoderReranker(model=cross_encoder, top_n=3)

    final_retriever = ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=multi_query_retriever
    )
    return final_retriever

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🔍 How it works")
    st.markdown("""
    1. **Enter a clue** in the search box
    2. **Multi-Query** expands it into 3 variants
    3. **ChromaDB** searches all case embeddings
    4. **CrossEncoder** reranks by true relevance
    5. **Top 3 cases** are returned
    """)
    st.markdown("---")
    st.markdown("## 💡 Try these queries")
    example_queries = [
        "suspect in dark hoodie near docks at midnight",
        "assault near waterfront at night",
        "illegal goods moved near harbor",
        "vehicle stolen at night with jammer",
        "fraud using forged documents at bank",
    ]
    for q in example_queries:
        if st.button(f"🔎 {q}", use_container_width=True):
            st.session_state["query"] = q

    st.markdown("---")
    st.markdown("**Total Cases in DB:** 10")
    st.markdown("**Vector Store:** ChromaDB")
    st.markdown("**Reranker:** ms-marco-MiniLM")

# ─────────────────────────────────────────────
# MAIN SEARCH
# ─────────────────────────────────────────────

col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input(
        "🔍 Enter your detective clue:",
        value=st.session_state.get("query", ""),
        placeholder="e.g. suspect in dark hoodie seen near docks at midnight carrying a bag...",
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    search_btn = st.button("🕵️ Analyze", use_container_width=True, type="primary")

# ─────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────

if search_btn and query:
    with st.spinner("🔄 Loading AI pipeline (first run takes ~1 min to download models)..."):
        retriever = load_pipeline()

    with st.spinner("🕵️ Analyzing cases..."):
        results = retriever.invoke(query)

    st.markdown("---")
    st.markdown(f"### 📁 Top {len(results)} Matching Cases for:")
    st.markdown(f"> *{query}*")
    st.markdown("")

    for i, doc in enumerate(results, 1):
        case_id   = doc.metadata.get("case_id", "N/A")
        case_type = doc.metadata.get("type", "N/A")
        lines     = doc.page_content.strip().split("\n")
        title     = lines[0].strip()
        body      = "\n".join(lines[1:]).strip()

        st.markdown(f"""
        <div class="case-card">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                <span class="match-badge">Match #{i}</span>
                <span style="color:white; font-weight:bold; font-size:16px;">{title}</span>
                <span class="type-badge">{case_type}</span>
                <span style="color:#888; font-size:13px;">Case #{case_id}</span>
            </div>
            <p style="color:#ccc; font-size:14px; margin:0; white-space:pre-line;">{body}</p>
        </div>
        """, unsafe_allow_html=True)

elif search_btn and not query:
    st.warning("⚠️ Please enter a detective clue to search!")

else:
    st.markdown("### 👆 Enter a clue above to find matching cases")
    st.markdown("")
    cols = st.columns(5)
    icons = ["🔫", "💰", "🚗", "🔥", "💊"]
    types = ["Robbery", "Fraud", "Theft", "Arson", "Drugs"]
    counts = [2, 1, 2, 1, 1]
    for i, col in enumerate(cols):
        with col:
            st.metric(label=f"{icons[i]} {types[i]}", value=f"{counts[i]} cases")