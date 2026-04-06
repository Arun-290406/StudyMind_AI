# 🧠 StudyMind AI — Personal Study Assistant

> AI-powered study assistant using RAG + Vector Search to answer questions from your notes, generate quizzes, create flashcards, and build study plans.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Ask Notes** | RAG Q&A with source citations from your PDFs |
| 🃏 **Flashcards** | Auto-generated cards with SM-2 spaced repetition |
| 📝 **Quiz Me** | MCQ quizzes with scoring and explanations |
| 📋 **Summary** | Structured summaries, TL;DRs, topic focus |
| 📅 **Study Plan** | AI-scheduled exam prep adapted to weak areas |
| 🗺️ **Mind Map** | Interactive knowledge graph from your notes |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/studymind-ai.git
cd studymind-ai
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env .env.local
# Edit .env and add your OpenAI API key
```

```env
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
VECTOR_STORE_BACKEND=faiss
```

> **No API key?** Set `EMBEDDING_MODEL=all-MiniLM-L6-v2` and `LLM_MODEL=llama3` (requires Ollama installed locally — free!)

### 5. Run the app
```bash
streamlit run app/main.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📁 Project Structure

```
studymind-ai/
│
├── app/
│   ├── main.py                   # Streamlit entry point + global CSS + sidebar
│   └── pages/
│       ├── 01_ask_notes.py       # RAG-powered Q&A chat
│       ├── 02_flashcards.py      # Flashcard generation + SM-2 practice
│       ├── 03_quiz.py            # MCQ quiz generation + evaluation
│       ├── 04_summary.py         # Document summarization
│       ├── 05_study_plan.py      # AI study plan generator
│       └── 06_mind_map.py        # Interactive knowledge graph
│
├── core/
│   ├── ingestion.py              # PDF/DOCX loader + text chunker
│   ├── embeddings.py             # OpenAI / HuggingFace embedding wrapper
│   ├── vector_store.py           # FAISS / ChromaDB interface
│   ├── retriever.py              # RAG retrieval + context building
│   └── llm.py                   # LLM wrapper (OpenAI / Ollama)
│
├── features/
│   ├── qa_chain.py               # RAG Q&A with citations
│   ├── flashcard_gen.py          # Flashcard gen + SM-2 algorithm
│   ├── quiz_gen.py               # MCQ generation + evaluation
│   ├── summarizer.py             # Map-reduce summarization
│   ├── study_planner.py          # AI study plan + topic extraction
│   └── mind_map.py               # Knowledge graph + pyvis rendering
│
├── utils/
│   ├── session_state.py          # Streamlit state manager
│   ├── file_handler.py           # Upload, validate, extract text
│   └── formatters.py             # Output parsers and formatters
│
├── data/
│   ├── uploads/                  # User uploaded files
│   └── vector_db/                # Persisted vector indices
│
├── .env                          # Environment variables template
├── requirements.txt              # Python dependencies
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit |
| **LLM** | OpenAI GPT-4o-mini / Ollama (local) |
| **Embeddings** | text-embedding-3-small / all-MiniLM-L6-v2 |
| **Vector DB** | FAISS (local) / ChromaDB (persistent) |
| **RAG Framework** | LangChain |
| **PDF Parsing** | PyMuPDF + pdfplumber |
| **Spaced Repetition** | SM-2 Algorithm |
| **Graph Visualization** | pyvis + networkx |

---

## ⚙️ Configuration

### Switch to Free Local Mode (no API key needed)
```env
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=llama3
```
Install [Ollama](https://ollama.ai) and run: `ollama pull llama3`

### Switch Vector Store to ChromaDB
```env
VECTOR_STORE_BACKEND=chroma
CHROMA_PERSIST_DIR=./data/vector_db/chroma
```

### Tune chunking
```env
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=5
```

---

## 📊 Resume Line

> Built **StudyMind AI**, an end-to-end AI study assistant using RAG + FAISS vector search on user-uploaded PDFs — featuring citation-grounded Q&A, SM-2 spaced repetition flashcards, adaptive MCQ quiz generation, AI-scheduled exam study plans, and an interactive knowledge graph. Deployed with Streamlit supporting both OpenAI and local Ollama LLMs.

---

## 🔮 Roadmap / New Features

- [ ] **Voice Q&A** — Whisper STT + TTS answers
- [ ] **Concept Gap Detector** — identify missing knowledge after quizzes  
- [ ] **Multi-language support** — translate notes and flashcards
- [ ] **Collaborative study rooms** — shared decks via Supabase
- [ ] **PDF annotation viewer** — highlight cited passages inline
- [ ] **Pomodoro timer** — built-in study session timer
- [ ] **Export to Anki** — export flashcards as `.apkg` file

---

## 📄 License

MIT License — free to use, modify, and distribute.