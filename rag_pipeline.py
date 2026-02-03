import os
from dotenv import load_dotenv
import streamlit as st

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from openai import OpenAI

load_dotenv()

DB_PATH = "vector_db"
HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@st.cache_resource(show_spinner=False)
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing in environment variables.")
    return OpenAI(api_key=api_key)


@st.cache_resource(show_spinner=False)
def get_embeddings():
    # os.environ.setdefault("HF_HOME", ".cache/huggingface")
    return HuggingFaceEmbeddings(model_name=HF_MODEL)


@st.cache_resource(show_spinner=False)
def get_db():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Vector DB not found at: {DB_PATH}")

    embeddings = get_embeddings()
    return Chroma(persist_directory=DB_PATH, embedding_function=embeddings)


def answer_with_citations(question: str, chat_history=None, k: int = 4):
    db = get_db()
    client = get_openai_client()

    docs = db.similarity_search(question, k=k)

    # Build unique sources (same pdf + same page)
    unique_sources = []
    seen = set()
    for d in docs:
        src = d.metadata.get("source", "unknown").replace("\\", "/")
        page = int(d.metadata.get("page", 0))
        key = (src, page)
        if key not in seen:
            seen.add(key)
            unique_sources.append({"source": src, "page": page})

    # Build context with explicit source blocks
    sources_text = []
    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source", "unknown").replace("\\", "/")
        page = int(d.metadata.get("page", 0)) + 1
        sources_text.append(
            f"[SOURCE {i}] ({os.path.basename(src)}, page {page})\n{d.page_content}"
        )
    context = "\n\n".join(sources_text)

    prompt = f"""
You are a policy assistant. Use ONLY the text inside SOURCES.
If the answer is not explicitly present, reply exactly:
Not found in the provided documents.

Write a clear answer in 3–5 lines.

SOURCES:
{context}

QUESTION:
{question}
""".strip()

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    return resp.output_text.strip(), unique_sources


def suggest_related_questions(question: str, sources: list, n: int = 3):
    client = get_openai_client()

    short_context = "\n".join(
        [f"- {os.path.basename(s.get('source', 'unknown'))} (page {int(s.get('page', 0)) + 1})"
         for s in sources]
    )

    prompt = f"""
You are helping a user explore internal policy documents.

User asked:
{question}

Docs used:
{short_context}

Suggest {n} short follow-up questions.
Rules:
- Must relate to company policies / security / IT procedures.
- Must be phrased as questions.
- Output ONLY questions, one per line.
""".strip()

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    lines = [ln.strip() for ln in resp.output_text.split("\n") if ln.strip()]
    return lines[:n]
