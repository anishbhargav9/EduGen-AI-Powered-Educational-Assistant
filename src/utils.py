import re


def clean_text(text: str) -> str:
    """Remove excessive whitespace and clean text."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def truncate_text(text: str, max_chars: int = 8000) -> str:
    """Truncate text to a maximum character count."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "...\n[Content truncated for processing]"


def format_source_name(file_name: str) -> str:
    """Create a clean display name from a file name."""
    return file_name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()


def count_words(text: str) -> int:
    """Count words in a text string."""
    return len(text.split())