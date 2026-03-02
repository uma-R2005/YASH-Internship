import streamlit as st
import json
import os
from dotenv import load_dotenv
from engine import (
    build_system_prompt,
    get_opening_question,
    react_prompt,
    generate_session_summary
)

load_dotenv()

st.set_page_config(page_title="PlacementBot 🎯", page_icon="🎯", layout="wide")

st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .stChatMessage { border-radius: 12px; margin-bottom: 8px; }
    .summary-box {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #0f3460;
        border-radius: 16px;
        padding: 24px;
        margin: 12px 0;
    }
    .end-btn { margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Question limits per mode ──
MODE_LIMITS = {"DSA": 12, "HR": 8, "Company": 10, "Resume": 7}

@st.cache_data
def load_companies():
    path = os.path.join(os.path.dirname(__file__), "data", "companies.json")
    with open(path) as f:
        return json.load(f)

companies = load_companies()

# ── Session state init ──
for key, default in {
    "chat_history": [],
    "llm_history": [],
    "session_started": False,
    "system_prompt": "",
    "profile": {},
    "show_summary": False,
    "summary_content": "",
    "current_mode": "DSA",
    "current_company": "",
    "interview_ended": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── SIDEBAR ──
with st.sidebar:
    st.title("🎯 PlacementBot")
    st.markdown("*React Prompting-Powered Interview Coach*")
    st.divider()

    st.subheader("👤 Your Profile")
    name   = st.text_input("Name", placeholder="Rahul Sharma")
    branch = st.selectbox("Branch", ["CSE", "ECE", "IT", "EEE", "Mechanical", "Civil"])
    year   = st.selectbox("Year", ["2nd Year", "3rd Year", "Final Year"])
    cgpa   = st.slider("CGPA", 5.0, 10.0, 7.5, 0.1)
    skills = st.text_input("Top Skills", placeholder="Python, DSA, SQL")

    st.divider()
    st.subheader("🎮 Session Settings")
    mode    = st.selectbox("Prep Mode", ["DSA", "HR", "Company", "Resume"])
    company = st.selectbox("Target Company", list(companies.keys()))

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("🚀 Start", use_container_width=True, type="primary")
    with col2:
        reset_btn = st.button("🔄 Reset", use_container_width=True)

    if reset_btn:
        for key in ["chat_history", "llm_history", "session_started",
                    "show_summary", "summary_content", "interview_ended"]:
            st.session_state[key] = [] if key in ["chat_history", "llm_history"] else False
        st.session_state.summary_content = ""
        st.rerun()

    # ── Live progress + End Interview button ──
    if st.session_state.get('session_started', False):
        st.divider()
        max_q      = MODE_LIMITS.get(st.session_state.current_mode, 10)
        user_turns = sum(1 for m in st.session_state.chat_history if m["role"] == "user")
        remaining  = max(0, max_q - user_turns)

        st.markdown(f"**📊 Progress:** {user_turns}/{max_q} questions")
        st.progress(min(user_turns / max_q, 1.0))
        st.caption(f"⏳ {remaining} question(s) remaining")

        st.divider()
        # ── END INTERVIEW BUTTON ──
        if not st.session_state.get('interview_ended', False):
            if st.button("🔴 End Interview", use_container_width=True, type="primary"):
                st.session_state.interview_ended = True
                st.session_state.show_summary    = True
                st.rerun()
        else:
            st.success("✅ Interview Ended")

    if company:
        st.divider()
        st.subheader(f"📌 {company} Info")
        cdata = companies[company]
        st.markdown(f"**Difficulty:** {cdata['difficulty']}")
        st.markdown(f"**Rounds:** {' → '.join(cdata['rounds'])}")
        st.markdown(f"**Focus:** {', '.join(cdata['focus'][:3])}")
        st.info(f"💡 {cdata['tip']}")

# ── MAIN ──
st.title("🎯 Smart Placement Prep Bot")
st.markdown(
    f"**Mode:** `{mode}` &nbsp;|&nbsp; **Company:** `{company}` "
    f"&nbsp;|&nbsp; *Powered by Groq + Llama3* &nbsp;|&nbsp; `v2.1`"
)
st.divider()

# ── START SESSION ──
if start_btn:
    if not name:
        st.warning("Please enter your name in the sidebar first!")
    else:
        st.session_state.profile = {
            "name": name, "branch": branch,
            "year": year, "cgpa": cgpa, "skills": skills
        }
        st.session_state.current_mode    = mode
        st.session_state.current_company = company
        cdata = companies[company]
        st.session_state.system_prompt   = build_system_prompt(
            mode, st.session_state.profile, company, cdata
        )
        opening = get_opening_question(mode, company, cdata)
        st.session_state.chat_history    = [{"role": "assistant", "content": opening}]
        st.session_state.llm_history     = [{"role": "assistant", "content": opening}]
        st.session_state.session_started = True
        st.session_state.interview_ended = False
        st.session_state.show_summary    = False
        st.session_state.summary_content = ""
        st.rerun()

# ── WELCOME SCREEN ──
if not st.session_state.session_started:
    st.markdown("""
    ### 👋 Welcome to PlacementBot!
    Fill your **profile** in the sidebar and hit **🚀 Start** to begin.

    **4 Modes:**
    - 🧠 **DSA** — Drill data structures & algorithms
    - 🎤 **HR** — Mock HR interview with real feedback
    - 🏢 **Company** — Simulate your target company's exact interview
    - 📄 **Resume** — Turn weak bullets into strong ones

    **Question Limits:** DSA: 12 | HR: 8 | Company: 10 | Resume: 7

    **Powered by Groq (Free) + Llama3 🦙**
    """)

else:
    max_q        = MODE_LIMITS.get(st.session_state.current_mode, 10)
    user_turns   = sum(1 for m in st.session_state.chat_history if m["role"] == "user")
    auto_complete = user_turns >= max_q
    ended         = st.session_state.interview_ended or auto_complete

    # ── RENDER CHAT HISTORY ──
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── SESSION ENDED (button OR auto-complete) ──
    if ended:
        if auto_complete:
            st.success(f"🎉 Interview complete! You answered all **{max_q} questions**.")
        else:
            user_turns_done = sum(1 for m in st.session_state.chat_history if m["role"] == "user")
            st.warning(f"🔴 Interview ended early after **{user_turns_done} questions**.")

        # Generate summary only once
        if not st.session_state.summary_content:
            with st.spinner("📊 Analyzing your performance... please wait"):
                st.session_state.summary_content = generate_session_summary(
                    st.session_state.llm_history,
                    st.session_state.profile,
                    st.session_state.current_company,
                    st.session_state.current_mode
                )

        # ── RENDER SUMMARY REPORT ──
        st.markdown("---")
        st.markdown("## 📋 Interview Performance Report")
        st.markdown(
            f"**Candidate:** {st.session_state.profile.get('name', 'Student')} &nbsp;|&nbsp; "
            f"**Company:** {st.session_state.current_company} &nbsp;|&nbsp; "
            f"**Mode:** {st.session_state.current_mode} &nbsp;|&nbsp; "
            f"**Questions Attempted:** {user_turns}"
        )
        st.markdown("---")
        st.markdown(st.session_state.summary_content)
        st.markdown("---")

        # ── ACTION BUTTONS after summary ──
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 New Session", use_container_width=True, type="primary"):
                for key in ["chat_history", "llm_history"]:
                    st.session_state[key] = []
                st.session_state.session_started = False
                st.session_state.interview_ended = False
                st.session_state.show_summary    = False
                st.session_state.summary_content = ""
                st.rerun()
        with col2:
            if st.button("🔁 Retry Same Company", use_container_width=True):
                cdata   = companies[st.session_state.current_company]
                opening = get_opening_question(
                    st.session_state.current_mode,
                    st.session_state.current_company,
                    cdata
                )
                st.session_state.chat_history    = [{"role": "assistant", "content": opening}]
                st.session_state.llm_history     = [{"role": "assistant", "content": opening}]
                st.session_state.interview_ended = False
                st.session_state.show_summary    = False
                st.session_state.summary_content = ""
                st.rerun()
        with col3:
            # Download summary as text
            st.download_button(
                label="⬇️ Download Report",
                data=st.session_state.summary_content,
                file_name=f"{st.session_state.profile.get('name','student')}_{st.session_state.current_company}_{st.session_state.current_mode}_report.txt",
                mime="text/plain",
                use_container_width=True
            )

    # ── ACTIVE CHAT ──
    else:
        # ── SUBMIT TEST BUTTON ──
        st.markdown("---")
        col_info, col_submit = st.columns([3, 1])
        with col_info:
            st.markdown(f"🟢 **Interview in progress** — {max_q - user_turns} question(s) remaining")
        with col_submit:
            if st.button("✅ Submit Test", use_container_width=True, type="primary"):
                st.session_state.interview_ended = True
                st.session_state.show_summary    = True
                st.rerun()
        st.markdown("---")

        if prompt := st.chat_input(f"Type your answer here... ({max_q - user_turns} questions left)"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.session_state.llm_history.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing your answer..."):
                    response = react_prompt(
                        prompt,
                        st.session_state.llm_history[:-1],
                        st.session_state.system_prompt
                    )
                st.markdown(response)

            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.session_state.llm_history.append({"role": "assistant", "content": response})
            st.rerun()