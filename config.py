import os
import streamlit as st

def get_api_key() -> str:
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        raise ValueError(
            "GROQ_API_KEY not found. "
            "Add it to .streamlit/secrets.toml or set as environment variable."
        )
    return key

GROQ_API_KEY = get_api_key()
GROQ_MODEL = "llama-3.3-70b-versatile"
CHROMA_DB_PATH = "./chroma_db"
MAX_CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200