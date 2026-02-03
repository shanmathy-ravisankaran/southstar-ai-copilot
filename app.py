import os
from ingest import ingest_docs 

# Build vector DB automatically on cloud if missing
if not os.path.exists("vector_db"):
    ingest_docs()

import uuid
import streamlit as st
from collections import defaultdict
from rag_pipeline import answer_with_citations, suggest_related_questions


# -------- Policy display names --------
POLICY_TITLES = {
    "Access_Control_Policy_SouthstarTech.pdf": "📄 Access Control Policy",
    "Data_Retention_Backup_Policy_SouthstarTech.pdf": "📄 Data Retention & Backup Policy",
    "Incident_Response_SOP_SouthstarTech.pdf": "📄 Incident Response SOP",
    "Onboarding_Security_Checklist_SouthstarTech.pdf": "📄 Onboarding Security Checklist",
}

st.set_page_config(page_title="Southstar Tech AI Copilot", page_icon="🔒")
st.title("🔒 Southstar Tech AI Copilot")
st.caption("Answers only from internal documents with citations.")

# ---------- session state ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "queued_q" not in st.session_state:
    st.session_state.queued_q = None

if "ended" not in st.session_state:
    st.session_state.ended = False

# store per-assistant-message feedback: {msg_id: {"helpful": True/False/None, "improve": ""}}
if "answer_feedback" not in st.session_state:
    st.session_state.answer_feedback = {}

# end-chat feedback
if "end_rating" not in st.session_state:
    st.session_state.end_rating = 0
if "end_text" not in st.session_state:
    st.session_state.end_text = ""

def queue_question(q: str):
    st.session_state.queued_q = q

def clear_chat():
    st.session_state.messages = []
    st.session_state.queued_q = None
    st.session_state.ended = False
    st.session_state.answer_feedback = {}
    st.session_state.end_rating = 0
    st.session_state.end_text = ""

def end_chat():
    st.session_state.ended = True
    st.session_state.queued_q = None

def _ensure_msg_id(m: dict) -> str:
    if "id" not in m or not m["id"]:
        m["id"] = str(uuid.uuid4())
    return m["id"]

def render_helpfulness_ui(msg_id: str):
    # default state
    if msg_id not in st.session_state.answer_feedback:
        st.session_state.answer_feedback[msg_id] = {"helpful": None, "improve": ""}

    state = st.session_state.answer_feedback[msg_id]

    st.markdown("**Did this answer help?**")
    c1, c2, c3 = st.columns([1, 1, 6])

    with c1:
        if st.button("👍", key=f"up_{msg_id}"):
            state["helpful"] = True
            st.session_state.answer_feedback[msg_id] = state

    with c2:
        if st.button("👎", key=f"down_{msg_id}"):
            state["helpful"] = False
            st.session_state.answer_feedback[msg_id] = state

    # If not helpful → show apology + improvement box
    if state["helpful"] is False:
        st.info("Sorry to hear that — tell me what I should improve (optional):")
        improve = st.text_input(
            "What should I improve?",
            value=state.get("improve", ""),
            key=f"improve_input_{msg_id}",
            label_visibility="collapsed",
            placeholder="Example: answer was unclear / need more detail / wrong doc…",
        )
        save_col1, save_col2 = st.columns([1, 6])
        with save_col1:
            if st.button("Submit", key=f"improve_submit_{msg_id}"):
                state["improve"] = improve
                st.session_state.answer_feedback[msg_id] = state
                st.success("Thanks — feedback saved.")

def render_star_rating_row():
    """
    One-row clickable stars.
    """
    st.markdown("## ⭐ Rate your experience")

    # Show stars as buttons in one row
    cols = st.columns(5)
    current = st.session_state.end_rating

    for i in range(1, 6):
        label = "⭐" if i <= current else "☆"
        with cols[i - 1]:
            if st.button(label, key=f"rate_{i}"):
                st.session_state.end_rating = i

    # Optional feedback box (always visible)
    st.session_state.end_text = st.text_area(
        "Optional feedback (what should be improved?)",
        value=st.session_state.end_text,
        placeholder="Type your feedback here…",
    )

    if st.button("Submit feedback"):
        st.success("Thanks! Your feedback was submitted.")

    st.button("Start new chat", on_click=clear_chat)

# ---------- show chat history ----------
for m in st.session_state.messages:
    _ensure_msg_id(m)
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

        # Feedback UI under each assistant reply
        if m["role"] == "assistant":
            render_helpfulness_ui(m["id"])
            st.markdown("---")

# ---------- if chat ended -> show end rating UI and stop ----------
if st.session_state.ended:
    st.success("✅ Thanks for using Southstar Tech AI Copilot!")
    render_star_rating_row()
    st.stop()

# ✅ ALWAYS render chat_input (textbox never disappears)
typed_q = st.chat_input("Ask a question from Southstar policies...")

# Priority: queued related-question > typed input
q = st.session_state.queued_q if st.session_state.queued_q else typed_q

if q:
    # clear queued once consumed
    st.session_state.queued_q = None

    # user message
    user_msg = {"role": "user", "content": q, "id": str(uuid.uuid4())}
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        st.markdown(q)

    # assistant answer
    with st.chat_message("assistant"):
        with st.spinner("Searching documents and generating answer..."):
            ans, sources = answer_with_citations(q)

        ans_clean = ans.split("EVIDENCE:")[0].strip()
        st.markdown(ans_clean)

        # ---- helpful UI for THIS answer ----
        current_asst_id = str(uuid.uuid4())
        render_helpfulness_ui(current_asst_id)

        # ---------- Sources ----------
        st.markdown("### Sources")
        grouped = defaultdict(set)
        for s in sources:
            src = s.get("source", "unknown").replace("\\", "/")
            page = int(s.get("page", 0))
            filename = src.split("/")[-1]
            grouped[filename].add(page)

        for filename, pages in grouped.items():
            pages_sorted = sorted(pages)
            page_links = []
            for p in pages_sorted:
                url = f"/app/static/docs/{filename}#page={p+1}"
                page_links.append(f"[Page {p+1}]({url})")

            title = POLICY_TITLES.get(filename, f" {filename}")
            st.markdown(f"**{title}**: " + " | ".join(page_links))

        # ---------- Related Questions ----------
        st.markdown("### Related questions")
        with st.spinner("Thinking of follow-up questions..."):
            related = suggest_related_questions(q, sources, n=3)

        for i, rq in enumerate(related):
            st.button(
                rq,
                key=f"rq_{len(st.session_state.messages)}_{i}",
                on_click=queue_question,
                args=(rq,),
            )

        # ---------- Bottom actions (no "Controls" title) ----------
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.button("🧹 Clear chat", on_click=clear_chat)
        with col2:
            st.button("✅ End chat", on_click=end_chat)

    # save assistant message into history (with SAME id used for feedback)
    asst_msg = {"role": "assistant", "content": ans_clean, "id": current_asst_id}
    st.session_state.messages.append(asst_msg)
