import csv
import os
from datetime import datetime

FEEDBACK_FILE = "feedback.csv"

def _ensure_file_exists():
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "session_id",
                "message_id",
                "question",
                "answer",
                "helpful",
                "improve_text",
                "sources",
                "end_rating",
                "end_text",
            ])

def log_answer_feedback(session_id: str, message_id: str, question: str, answer: str,
                        helpful, improve_text: str, sources):
    """
    helpful: True / False / None
    sources: list of dicts like [{"source": "...", "page": 1}, ...]
    """
    _ensure_file_exists()
    ts = datetime.now().isoformat(timespec="seconds")

    # make sources a small string: "file.pdf:3; other.pdf:1"
    src_str = ""
    try:
        compact = []
        for s in (sources or []):
            name = str(s.get("source", "")).replace("\\", "/").split("/")[-1]
            page = int(s.get("page", 0)) + 1
            compact.append(f"{name}:{page}")
        src_str = "; ".join(compact)
    except Exception:
        src_str = ""

    with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            ts,
            session_id,
            message_id,
            question,
            answer,
            helpful,
            improve_text or "",
            src_str,
            "",   # end_rating empty here
            "",   # end_text empty here
        ])
    print("✅ Feedback saved to feedback.csv")
def log_end_chat_feedback(session_id: str, end_rating: int, end_text: str):
    _ensure_file_exists()
    ts = datetime.now().isoformat(timespec="seconds")

    with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            ts,
            session_id,
            "",     # message_id
            "",     # question
            "",     # answer
            "",     # helpful
            "",     # improve_text
            "",     # sources
            end_rating,
            end_text or "",
        ])
    print("✅ End-chat feedback saved")