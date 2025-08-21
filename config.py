import os
from pathlib import Path

# Project configuration
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads" 
PROCESSED_DIR = DATA_DIR / "processed"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Model Configuration
GEMINI_MODEL = "gemini-1.5-flash"
EMBEDDING_MODEL = "models/embedding-001"

# Text Processing Configuration
MAX_CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_FILE_SIZE_MB = 50

# Quiz Generation Configuration
DEFAULT_QUIZ_SETTINGS = {
    'difficulty': 'Medium',
    'num_questions': 15,
    'question_types': ['Multiple Choice', 'True/False']
}

# Note Generation Configuration  
DEFAULT_NOTE_SETTINGS = {
    'style': 'Detailed',
    'include_examples': True
}

# RAG Configuration
SIMILARITY_TOP_K = 5
TEMPERATURE = 0.3

# Supported file types
SUPPORTED_EXTENSIONS = {
    'pdf': ['.pdf'],
    'powerpoint': ['.pptx', '.ppt'], 
    'text': ['.txt', '.md']
}

# UI Configuration
STREAMLIT_CONFIG = {
    'theme': {
        'primaryColor': '#667eea',
        'backgroundColor': '#ffffff',
        'secondaryBackgroundColor': '#f0f2f6',
        'textColor': '#262730'
    }
}