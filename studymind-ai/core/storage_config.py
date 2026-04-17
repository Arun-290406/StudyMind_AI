import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv("STUDYMIND_DATA_DIR", "./data"))
DB_DIR = DATA_DIR / "db"
VECTOR_DIR = DATA_DIR / "vector_db"

SQLITE_DB_PATH = Path(os.getenv("SQLITE_DB_PATH", str(DB_DIR / "studymind.db")))
VECTOR_STORE_BACKEND = os.getenv("VECTOR_STORE_BACKEND", "faiss").lower()
FAISS_INDEX_PATH = Path(os.getenv("FAISS_INDEX_PATH", str(VECTOR_DIR / "faiss_index")))
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", str(VECTOR_DIR / "chroma")))

for path in (DATA_DIR, DB_DIR, VECTOR_DIR, SQLITE_DB_PATH.parent, FAISS_INDEX_PATH.parent, CHROMA_PERSIST_DIR):
    path.mkdir(parents=True, exist_ok=True)