import os
import tempfile
import streamlit as st
from pathlib import Path
import shutil
from typing import Union, List
import hashlib
import json
from datetime import datetime
import pandas as pd

def setup_directories():
    """Create necessary directories for the application"""
    
    directories = [
        "data",
        "data/uploads",
        "data/processed", 
        "data/vectorstore",
        "templates",
        "assets",
        "assets/images",
        "assets/css"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def save_uploaded_file(uploaded_file) -> str:
    """Save uploaded file to temporary location and return path"""
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error saving uploaded file: {str(e)}")
        return None

def get_file_hash(file_path: str) -> str:
    """Generate MD5 hash of file for caching purposes"""
    
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5()
            chunk = f.read(8192)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(8192)
        return file_hash.hexdigest()
    except Exception as e:
        return None

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def clean_filename(filename: str) -> str:
    """Clean filename by removing invalid characters"""
    
    import re
    # Remove invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    cleaned = re.sub(r'_{2,}', '_', cleaned)
    # Remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    
    return cleaned

def save_session_data(session_id: str, data: dict):
    """Save session data to file"""
    
    try:
        session_dir = Path("data/sessions")
        session_dir.mkdir(exist_ok=True)
        
        session_file = session_dir / f"{session_id}.json"
        
        with open(session_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        st.error(f"Error saving session data: {str(e)}")

def load_session_data(session_id: str) -> dict:
    """Load session data from file"""
    
    try:
        session_file = Path("data/sessions") / f"{session_id}.json"
        
        if session_file.exists():
            with open(session_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading session data: {str(e)}")
    
    return {}

def export_quiz_results(quiz_data: List[dict], user_answers: dict, statistics: dict) -> str:
    """Export quiz results as formatted text"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    results = f"""# Quiz Results Report
Generated: {timestamp}

## Summary
- Total Questions: {statistics['total_questions']}
- Correct Answers: {statistics['correct_answers']}
- Score: {statistics['score_percentage']:.1f}%
- Completion Rate: {statistics['completion_rate']:.1f}%

## Detailed Results

"""
    
    for i, question in enumerate(quiz_data):
        user_answer = user_answers.get(i, "Not answered")
        correct_answer = question['correct_answer']
        is_correct = user_answer == correct_answer
        
        results += f"""### Question {i+1}
**Question:** {question['question']}
**Your Answer:** {user_answer}
**Correct Answer:** {correct_answer}
**Status:** {"✅ Correct" if is_correct else "❌ Incorrect"}

"""
        if 'explanation' in question:
            results += f"**Explanation:** {question['explanation']}\n\n"
        
        results += "---\n\n"
    
    return results

def create_study_schedule(topics: List[str], days: int = 7) -> dict:
    """Create a study schedule for the given topics"""
    
    if not topics or days <= 0:
        return {}
    
    topics_per_day = max(1, len(topics) // days)
    schedule = {}
    
    current_day = 1
    topic_index = 0
    
    while topic_index < len(topics) and current_day <= days:
        day_key = f"Day {current_day}"
        schedule[day_key] = []
        
        # Assign topics to current day
        for _ in range(topics_per_day):
            if topic_index < len(topics):
                schedule[day_key].append(topics[topic_index])
                topic_index += 1
        
        current_day += 1
    
    # Distribute remaining topics
    if topic_index < len(topics):
        for remaining_topic in topics[topic_index:]:
            # Add to the day with fewest topics
            min_day = min(schedule.keys(), key=lambda k: len(schedule[k]))
            schedule[min_day].append(remaining_topic)
    
    return schedule

def generate_progress_report(session_data: dict) -> str:
    """Generate a progress report based on session data"""
    
    report = "# Learning Progress Report\n\n"
    
    if 'quiz_history' in session_data:
        quiz_scores = [quiz['score'] for quiz in session_data['quiz_history']]
        if quiz_scores:
            avg_score = sum(quiz_scores) / len(quiz_scores)
            best_score = max(quiz_scores)
            report += f"## Quiz Performance\n"
            report += f"- Quizzes taken: {len(quiz_scores)}\n"
            report += f"- Average score: {avg_score:.1f}%\n"
            report += f"- Best score: {best_score:.1f}%\n\n"
    
    if 'study_time' in session_data:
        total_minutes = session_data['study_time']
        hours = total_minutes // 60
        minutes = total_minutes % 60
        report += f"## Study Time\n"
        report += f"- Total study time: {hours}h {minutes}m\n\n"
    
    if 'topics_covered' in session_data:
        report += f"## Topics Covered\n"
        for topic in session_data['topics_covered']:
            report += f"- {topic}\n"
        report += "\n"
    
    return report

def validate_api_key(api_key: str) -> bool:
    """Validate Google API key format"""
    
    if not api_key:
        return False
    
    # Basic validation - Google API keys typically start with certain patterns
    if not api_key.startswith(('AIza', 'BIza')):
        return False
    
    # Check length (Google API keys are usually 39 characters)
    if len(api_key) != 39:
        return False
    
    return True

def create_backup(data: dict, backup_name: str = None):
    """Create backup of important data"""
    
    try:
        backup_dir = Path("data/backups")
        backup_dir.mkdir(exist_ok=True)
        
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.json"
        
        backup_file = backup_dir / backup_name
        
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return str(backup_file)
        
    except Exception as e:
        st.error(f"Error creating backup: {str(e)}")
        return None

def load_backup(backup_file: str) -> dict:
    """Load data from backup file"""
    
    try:
        with open(backup_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading backup: {str(e)}")
        return {}

def cleanup_temp_files():
    """Clean up temporary files older than 1 day"""
    
    try:
        import time
        temp_dir = Path("data/uploads")
        
        if temp_dir.exists():
            current_time = time.time()
            
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    # Delete files older than 24 hours
                    if file_age > 86400:
                        file_path.unlink()
    except Exception as e:
        pass  # Silently ignore cleanup errors

def get_system_info() -> dict:
    """Get system information for debugging"""
    
    import platform
    import sys
    
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": sys.version,
        "streamlit_version": st.__version__,
        "working_directory": os.getcwd()
    }

def log_error(error: Exception, context: str = ""):
    """Log error with context information"""
    
    try:
        log_dir = Path("data/logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / "errors.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {context}: {str(error)}\n")
    except Exception:
        pass  # Don't error on logging errors

def convert_to_dataframe(data: List[dict], columns: List[str] = None) -> pd.DataFrame:
    """Convert data to pandas DataFrame for analysis"""
    
    try:
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        if columns:
            # Select only specified columns if they exist
            available_columns = [col for col in columns if col in df.columns]
            df = df[available_columns]
        
        return df
    except Exception as e:
        return pd.DataFrame()

def generate_word_cloud_data(text: str, max_words: int = 100) -> List[dict]:
    """Generate word frequency data for word cloud visualization"""
    
    try:
        import re
        from collections import Counter
        
        # Clean and tokenize text
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'shall', 'not', 'no', 'yes'
        }
        
        # Filter out stop words
        filtered_words = [word for word in words if word not in stop_words]
        
        # Count frequencies
        word_freq = Counter(filtered_words)
        
        # Convert to format suitable for visualization
        word_data = [
            {"text": word, "value": freq} 
            for word, freq in word_freq.most_common(max_words)
        ]
        
        return word_data
        
    except Exception as e:
        return []

def calculate_readability_score(text: str) -> dict:
    """Calculate basic readability metrics for the text"""
    
    try:
        import re
        
        # Count sentences (rough approximation)
        sentences = len(re.findall(r'[.!?]+', text))
        if sentences == 0:
            sentences = 1
        
        # Count words
        words = len(text.split())
        if words == 0:
            return {"error": "No text to analyze"}
        
        # Count syllables (approximation)
        syllable_pattern = r'[aeiouyAEIOUY]+'
        syllables = len(re.findall(syllable_pattern, text))
        
        # Calculate metrics
        avg_words_per_sentence = words / sentences
        avg_syllables_per_word = syllables / words if words > 0 else 0
        
        # Simple readability assessment
        if avg_words_per_sentence < 15 and avg_syllables_per_word < 2:
            difficulty = "Easy"
        elif avg_words_per_sentence < 20 and avg_syllables_per_word < 2.5:
            difficulty = "Medium"
        else:
            difficulty = "Hard"
        
        return {
            "word_count": words,
            "sentence_count": sentences,
            "avg_words_per_sentence": round(avg_words_per_sentence, 2),
            "avg_syllables_per_word": round(avg_syllables_per_word, 2),
            "difficulty_level": difficulty
        }
        
    except Exception as e:
        return {"error": f"Error analyzing text: {str(e)}"}

def generate_learning_tips(content_type: str, difficulty: str) -> List[str]:
    """Generate contextual learning tips based on content and difficulty"""
    
    tips = []
    
    # Base tips for all content
    base_tips = [
        "Take breaks every 25-30 minutes to maintain focus",
        "Create your own examples to reinforce understanding",
        "Teach the concept to someone else or explain it aloud"
    ]
    
    # Content-specific tips
    if content_type == "pdf":
        tips.extend([
            "Use the search function to quickly find specific topics",
            "Take notes on key definitions and concepts",
            "Create visual diagrams for complex processes"
        ])
    elif content_type == "youtube":
        tips.extend([
            "Watch at different speeds to match your learning pace",
            "Pause frequently to process information",
            "Take timestamps of important sections for review"
        ])
    elif content_type == "powerpoint":
        tips.extend([
            "Focus on slide titles and bullet points for main ideas",
            "Pay attention to diagrams and visual elements",
            "Review slides multiple times for better retention"
        ])
    
    # Difficulty-specific tips
    if difficulty == "Easy":
        tips.extend([
            "Focus on understanding basic definitions first",
            "Use flashcards for key terms",
            "Connect new concepts to things you already know"
        ])
    elif difficulty == "Medium":
        tips.extend([
            "Practice explaining concepts in your own words",
            "Look for connections between different topics",
            "Create concept maps to visualize relationships"
        ])
    elif difficulty == "Hard":
        tips.extend([
            "Break complex topics into smaller, manageable parts",
            "Use multiple sources to understand difficult concepts",
            "Practice application problems and real-world examples",
            "Schedule multiple review sessions over several days"
        ])
    
    # Combine and randomize
    all_tips = base_tips + tips
    import random
    random.shuffle(all_tips)
    
    return all_tips[:6]  # Return 6 random tips