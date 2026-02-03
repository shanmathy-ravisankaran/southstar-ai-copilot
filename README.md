🤖 Southstar Tech AI Copilot – Enterprise RAG Assistant

This project delivers an AI-powered internal copilot built using Retrieval-Augmented Generation (RAG). It enables users to ask natural language questions and receive grounded answers from company documents, along with source citations and feedback tracking.
The system simulates an enterprise knowledge assistant used for policy lookup, compliance questions, and operational support.

📌 Architecture Overview

<img width="1337" height="625" alt="image" src="https://github.com/user-attachments/assets/594a8644-63a3-4e4c-b89a-92d8cdf6ad76" />

<img width="1007" height="638" alt="image" src="https://github.com/user-attachments/assets/693893da-4d98-47a8-9aff-c0a9893ce63a" />


Workflow Summary
1.Document Source
    Internal PDFs and files (policies, onboarding docs, checklists)

2.Vectorization Layer
    a)Documents are chunked
    b)Text embeddings generated using HuggingFace models
    c)Stored in a Chroma vector database

3.Retrieval Layer (RAG)
    
    a)User question converted to embedding
    b)Top relevant document chunks retrieved
    c)Context sent to LLM for grounded answer

4.LLM Response Generation

    a)LLM answers only using retrieved context 
    b)Returns answer + source citations

5.UI Layer
    
    a)Built with Streamlit chat interface
    b)Real-time Q&A experience
    c)Feedback & Analytics Layer

6.User ratings stored

    a)Helpful / Not helpful tracking
    b)Feedback saved to feedback.csv for analysis

📊 Capabilities
    
📄 Enterprise Knowledge Search

    a)Ask questions about policies and procedures
    b)Find specific rules or compliance info
    c)Get answers grounded in documents

🔎 Source Transparency

    a)Every answer shows document name and page number
    b)Prevents hallucinations
    c)Builds trust in AI outputs

⭐ Feedback System

    a)Users rate answer
    b)Suggest improvements
    c)End-of-chat experience rating
    d)Feedback logged with timestamp & session ID

🚀 Key Features

    a)RAG-based AI assistant
    b)Vector search using Chroma
    c)Grounded LLM responses
    d)Streamlit chat UI
    e)Feedback logging system
    f)Session tracking

🛠 Tools & Technologies
Layer	           Technology
LLM Framework	   LangChain
Vector DB	        Chroma
Embeddings	       HuggingFace
UI	                Streamlit
Language	         Python
Architecture	      RAG

⚙️ How to Run
pip install -r requirements.txt
streamlit run app.py

📂 Project Structure
southstar-ai-copilot/
│
├── app.py
├── rag_pipeline.py
├── feedback_store.py
├── ingest.py
├── vector_db/
├── docs/
├── feedback.csv
├── requirements.txt
└── README.md

📈 Results & Learnings

    a)Built full RAG pipeline
    b)Implemented semantic vector search
    c)Designed enterprise AI copilot
    d)Created AI feedback loop

🔮 Future Improvements

    a)Feedback dashboard
    b)Role-based access
    c)API deployment
    d)Multi-document scaling

📜 License

MIT License
