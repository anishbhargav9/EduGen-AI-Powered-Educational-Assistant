import os
import streamlit as st

def get_api_key() -> str:
    # First try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass
    # Fallback to environment variable (for local development)
    key = os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        raise ValueError(
            "GOOGLE_API_KEY not found. "
            "Add it to .streamlit/secrets.toml or set as environment variable."
        )
    return key

GOOGLE_API_KEY = get_api_key()
GEMINI_MODEL = "gemini-2.0-flash"
EMBEDDING_MODEL = "models/text-embedding-004"
CHROMA_DB_PATH = "./chroma_db"
MAX_CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200