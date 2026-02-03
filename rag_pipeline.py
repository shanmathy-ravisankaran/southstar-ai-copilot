import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_PATH = "vector_db"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings
)
def answer_with_citations(question: str, chat_history=None, k: int = 4):
    docs = db.similarity_search(question, k=k)

    # remove duplicates (same pdf + same page)
    unique_sources = []
    seen = set()
    for d in docs:
        src = d.metadata.get("source", "unknown").replace("\\", "/")
        page = int(d.metadata.get("page", 0))
        key = (src, page)
        if key not in seen:
            seen.add(key)
            unique_sources.append({"source": src, "page": page})

    context = "\n\n".join(
        [f"[SOURCE {i+1}] {d.page_content}" for i, d in enumerate(docs)]
    )

    prompt = f"""
You are a policy assistant. Answer ONLY using the provided SOURCES.
If the answer is not explicitly in the sources, say: "Not found in the provided documents."

Return ONLY:
ANSWER: <your answer in 3-4 lines>

SOURCES:
{context}

QUESTION:
{question}
"""

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    return resp.output_text, unique_sources


def suggest_related_questions(question: str, sources: list, n: int = 3):
    """
    Suggest follow-up questions based on the user's question and the retrieved sources.
    Returns: list[str]
    """

    # Build small context using the sources (file + page)
    short_context = "\n".join(
        [f"- {s.get('source', 'unknown')} (page {int(s.get('page', 0)) + 1})"
         for s in sources]
    )

    prompt = f"""
You are helping a user explore internal policy documents.

User asked:
{question}

The documents used were:
{short_context}

Suggest {n} short, relevant follow-up questions the user can ask next.
Rules:
- Must be related to company policies / security / IT procedures.
- Must be phrased as questions.
- Return ONLY the questions, one per line.
- No numbering, no bullets, no extra text.
"""

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    # Convert output text -> list of questions
    lines = [ln.strip() for ln in resp.output_text.split("\n") if ln.strip()]
    return lines[:n]

