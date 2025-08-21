"""
EduGen - AI-Powered Educational Assistant

This package contains modules for processing educational content and generating
learning materials using advanced AI techniques.

Modules:
- document_processor: Handle various document formats (PDF, PPT, YouTube)
- quiz_generator: Generate interactive quizzes with multiple question types
- note_generator: Create structured study notes in different formats
- flashcard_generator: Generate flashcards for key concepts and definitions
- rag_chat: RAG-powered chat system for content-based Q&A
- utils: Utility functions for file handling and data processing
"""

__version__ = "1.0.0"
__author__ = "EduGen Development Team"
__email__ = "contact@edugen.ai"

# Import main classes for easy access
from .document_processor import DocumentProcessor
from .quiz_generator import QuizGenerator
from .note_generator import NoteGenerator
from .flashcard_generator import FlashcardGenerator
from .rag_chat import RAGChat

# Import utility functions
from .utils import (
    setup_directories,
    save_uploaded_file,
    get_file_hash,
    format_file_size,
    clean_filename,
    validate_api_key,
    cleanup_temp_files
)

__all__ = [
    "DocumentProcessor",
    "QuizGenerator", 
    "NoteGenerator",
    "FlashcardGenerator",
    "RAGChat",
    "setup_directories",
    "save_uploaded_file",
    "get_file_hash",
    "format_file_size",
    "clean_filename",
    "validate_api_key",
    "cleanup_temp_files"
]