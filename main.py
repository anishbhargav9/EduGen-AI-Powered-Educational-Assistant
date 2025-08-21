import streamlit as st
import os
from dotenv import load_dotenv
import tempfile
from pathlib import Path

# Load environment variables
load_dotenv()

# Import custom modules
from src.document_processor import DocumentProcessor
from src.quiz_generator import QuizGenerator  
from src.note_generator import NoteGenerator
from src.flashcard_generator import FlashcardGenerator
from src.rag_chat import RAGChat
from src.utils import setup_directories, save_uploaded_file

# Page configuration
st.set_page_config(
    page_title="🎓 EduGen: AI Learning Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎓 EduGen: AI Learning Assistant</h1>
        <p>Transform your lecture materials into structured notes, quizzes, and flashcards using AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'processed_docs' not in st.session_state:
        st.session_state.processed_docs = []
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Setup directories
    setup_directories()
    
    # Initialize processors
    doc_processor = DocumentProcessor()
    quiz_gen = QuizGenerator()
    note_gen = NoteGenerator()  
    flashcard_gen = FlashcardGenerator()
    rag_chat = RAGChat()
    
    # Sidebar for file upload and settings
    with st.sidebar:
        st.header("📁 Upload Learning Materials")
        
        # File upload options
        upload_type = st.selectbox(
            "Choose input type:",
            ["📄 PDF Document", "📊 PowerPoint", "🎥 YouTube Video", "📝 Direct Text"]
        )
        
        uploaded_files = []
        text_content = ""
        
        if upload_type == "📄 PDF Document":
            uploaded_files = st.file_uploader(
                "Upload PDF files",
                type=['pdf'],
                accept_multiple_files=True,
                help="Upload one or more PDF documents"
            )
            
        elif upload_type == "📊 PowerPoint":
            uploaded_files = st.file_uploader(
                "Upload PowerPoint files", 
                type=['pptx', 'ppt'],
                accept_multiple_files=True,
                help="Upload PowerPoint presentations"
            )
            
        elif upload_type == "🎥 YouTube Video":
            youtube_url = st.text_input(
                "Enter YouTube URL:",
                placeholder="https://www.youtube.com/watch?v=..."
            )
            if youtube_url and st.button("📥 Download Transcript"):
                with st.spinner("Downloading transcript..."):
                    try:
                        text_content = doc_processor.process_youtube(youtube_url)
                        st.success("✅ Transcript downloaded successfully!")
                        st.text_area("Preview:", text_content[:500] + "...", height=150)
                    except Exception as e:
                        st.error(f"Error downloading transcript: {str(e)}")
                        
        elif upload_type == "📝 Direct Text":
            text_content = st.text_area(
                "Paste your lecture content:",
                height=300,
                placeholder="Paste your lecture notes, transcripts, or any educational content here..."
            )
        
        # Processing button
        if st.button("🚀 Process & Generate"):
            if uploaded_files or text_content:
                process_content(uploaded_files, text_content, upload_type, doc_processor, rag_chat)
            else:
                st.warning("Please upload files or enter text content first!")
        
        # Settings
        st.header("⚙️ Settings")
        
        # Quiz settings
        with st.expander("🧩 Quiz Settings"):
            quiz_difficulty = st.selectbox("Difficulty Level:", ["Easy", "Medium", "Hard"])
            num_questions = st.slider("Number of Questions:", 5, 50, 15)
            question_types = st.multiselect(
                "Question Types:",
                ["Multiple Choice", "True/False", "Short Answer"],
                default=["Multiple Choice", "True/False"]
            )
        
        # Note settings  
        with st.expander("📝 Note Settings"):
            note_style = st.selectbox("Note Style:", ["Detailed", "Summary", "Bullet Points"])
            include_examples = st.checkbox("Include Examples", value=True)
            
        # Store settings in session state
        st.session_state.quiz_settings = {
            'difficulty': quiz_difficulty,
            'num_questions': num_questions, 
            'question_types': question_types
        }
        st.session_state.note_settings = {
            'style': note_style,
            'include_examples': include_examples
        }

    # Main content area with tabs
    if st.session_state.processed_docs:
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Generated Notes", "🧩 Interactive Quiz", "🎯 Flashcards", "💬 RAG Chat"])
        
        with tab1:
            display_notes(note_gen)
            
        with tab2:
            display_quiz(quiz_gen)
            
        with tab3:
            display_flashcards(flashcard_gen)
            
        with tab4:
            display_rag_chat(rag_chat)
    else:
        # Welcome screen
        display_welcome_screen()

def process_content(uploaded_files, text_content, upload_type, doc_processor, rag_chat):
    """Process uploaded content and create vector store"""
    
    with st.spinner("🔄 Processing your content..."):
        try:
            all_text = ""
            processed_files = []
            
            # Process uploaded files
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    # Save uploaded file temporarily
                    temp_path = save_uploaded_file(uploaded_file)
                    
                    # Process based on file type
                    if upload_type == "📄 PDF Document":
                        text = doc_processor.process_pdf(temp_path)
                    elif upload_type == "📊 PowerPoint":
                        text = doc_processor.process_ppt(temp_path)
                    
                    all_text += f"\n\n--- {uploaded_file.name} ---\n\n{text}"
                    processed_files.append(uploaded_file.name)
                    
                    # Clean up temp file
                    os.unlink(temp_path)
            
            # Add direct text content
            if text_content:
                all_text += f"\n\n--- Direct Input ---\n\n{text_content}"
                processed_files.append("Direct Input")
            
            # Create vector store for RAG
            if all_text.strip():
                vector_store = rag_chat.create_vector_store(all_text)
                
                # Update session state
                st.session_state.processed_docs = processed_files
                st.session_state.vector_store = vector_store
                st.session_state.processed_text = all_text
                
                st.success(f"✅ Successfully processed {len(processed_files)} document(s)!")
                st.rerun()
            else:
                st.error("No content found to process!")
                
        except Exception as e:
            st.error(f"Error processing content: {str(e)}")

def display_welcome_screen():
    """Display welcome screen with feature overview"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📝 Smart Notes</h3>
            <p>Generate comprehensive, well-structured study notes from your lecture materials using advanced AI.</p>
            <ul>
                <li>Topic-wise organization</li>
                <li>Key concepts highlighting</li>
                <li>Summary and detailed views</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🧩 Interactive Quizzes</h3>
            <p>Auto-generated quizzes to test your understanding with multiple question types.</p>
            <ul>
                <li>Multiple choice questions</li>
                <li>True/False questions</li>
                <li>Short answer questions</li>
                <li>Instant explanations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 Smart Flashcards</h3>
            <p>Create flashcards for quick revision and memory reinforcement.</p>
            <ul>
                <li>Key term definitions</li>
                <li>Concept explanations</li>
                <li>Interactive review</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <h3>💬 RAG-Powered Chat</h3>
        <p>Ask questions about your uploaded content and get intelligent, context-aware answers.</p>
        <ul>
            <li>Natural language queries</li>
            <li>Context-aware responses</li>
            <li>Source citations</li>
            <li>Follow-up conversations</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Getting started section
    st.markdown("---")
    st.markdown("### 🚀 Getting Started")
    st.markdown("""
    1. **Upload your materials** using the sidebar (PDF, PowerPoint, YouTube videos, or direct text)
    2. **Configure settings** for quiz difficulty and note style
    3. **Click 'Process & Generate'** to create your learning materials
    4. **Explore the tabs** to access notes, quizzes, flashcards, and chat features
    """)

def display_notes(note_gen):
    """Display generated notes"""
    st.header("📝 AI-Generated Study Notes")
    
    if st.button("🔄 Generate Fresh Notes"):
        with st.spinner("Generating comprehensive study notes..."):
            try:
                notes = note_gen.generate_notes(
                    st.session_state.processed_text,
                    st.session_state.note_settings
                )
                st.session_state.generated_notes = notes
            except Exception as e:
                st.error(f"Error generating notes: {str(e)}")
                return
    
    if hasattr(st.session_state, 'generated_notes'):
        # Display notes with formatting
        st.markdown("### 📚 Study Notes")
        
        # Add download button
        col1, col2 = st.columns([3, 1])
        with col2:
            st.download_button(
                "📥 Download Notes",
                st.session_state.generated_notes,
                file_name="study_notes.md",
                mime="text/markdown"
            )
        
        # Display the notes
        st.markdown(st.session_state.generated_notes)
    else:
        st.info("Click 'Generate Fresh Notes' to create comprehensive study notes from your content.")

def display_quiz(quiz_gen):
    """Display interactive quiz"""
    st.header("🧩 Interactive Quiz")
    
    if st.button("🎯 Generate New Quiz"):
        with st.spinner("Creating personalized quiz questions..."):
            try:
                quiz_data = quiz_gen.generate_quiz(
                    st.session_state.processed_text,
                    st.session_state.quiz_settings
                )
                st.session_state.quiz_data = quiz_data
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
            except Exception as e:
                st.error(f"Error generating quiz: {str(e)}")
                return
    
    if hasattr(st.session_state, 'quiz_data'):
        display_interactive_quiz()
    else:
        st.info("Click 'Generate New Quiz' to create a personalized quiz based on your content.")

def display_interactive_quiz():
    """Display interactive quiz interface"""
    quiz_data = st.session_state.quiz_data
    
    st.markdown(f"### 📊 Quiz: {len(quiz_data)} Questions")
    
    # Progress bar
    if 'user_answers' in st.session_state:
        progress = len(st.session_state.user_answers) / len(quiz_data)
        st.progress(progress, text=f"Progress: {len(st.session_state.user_answers)}/{len(quiz_data)} questions answered")
    
    # Display quiz questions
    for i, question in enumerate(quiz_data):
        st.markdown(f"---")
        st.markdown(f"**Question {i+1}:** {question['question']}")
        
        if question['type'] == 'multiple_choice':
            answer = st.radio(
                f"Select your answer for question {i+1}:",
                question['options'],
                key=f"q_{i}",
                index=None
            )
            if answer:
                st.session_state.user_answers[i] = answer
                
        elif question['type'] == 'true_false':
            answer = st.radio(
                f"Select your answer for question {i+1}:",
                ['True', 'False'],
                key=f"q_{i}",
                index=None
            )
            if answer:
                st.session_state.user_answers[i] = answer
                
        elif question['type'] == 'short_answer':
            answer = st.text_input(
                f"Your answer for question {i+1}:",
                key=f"q_{i}"
            )
            if answer:
                st.session_state.user_answers[i] = answer
    
    # Submit quiz button
    if len(st.session_state.user_answers) == len(quiz_data):
        if st.button("📊 Submit Quiz", type="primary"):
            st.session_state.quiz_submitted = True
            st.rerun()
    else:
        remaining = len(quiz_data) - len(st.session_state.user_answers)
        st.info(f"Please answer {remaining} more question(s) to submit the quiz.")
    
    # Show results if quiz is submitted
    if st.session_state.get('quiz_submitted', False):
        display_quiz_results()

def display_quiz_results():
    """Display quiz results and explanations"""
    st.markdown("---")
    st.header("🎯 Quiz Results")
    
    quiz_data = st.session_state.quiz_data
    user_answers = st.session_state.user_answers
    
    correct_answers = 0
    total_questions = len(quiz_data)
    
    for i, question in enumerate(quiz_data):
        user_answer = user_answers.get(i, "")
        correct_answer = question['correct_answer']
        
        if question['type'] in ['multiple_choice', 'true_false']:
            is_correct = user_answer == correct_answer
            if is_correct:
                correct_answers += 1
        else:  # short_answer - simplified check
            is_correct = correct_answer.lower() in user_answer.lower() if user_answer else False
            if is_correct:
                correct_answers += 1
        
        # Display result for each question
        with st.expander(f"Question {i+1}: {'✅ Correct' if is_correct else '❌ Incorrect'}"):
            st.write(f"**Question:** {question['question']}")
            st.write(f"**Your Answer:** {user_answer}")
            st.write(f"**Correct Answer:** {correct_answer}")
            if 'explanation' in question:
                st.write(f"**Explanation:** {question['explanation']}")
    
    # Overall score
    score_percentage = (correct_answers / total_questions) * 100
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Score", f"{correct_answers}/{total_questions}")
    with col2:
        st.metric("Percentage", f"{score_percentage:.1f}%")
    with col3:
        if score_percentage >= 80:
            st.success("🌟 Excellent!")
        elif score_percentage >= 60:
            st.warning("👍 Good job!")
        else:
            st.info("📚 Keep studying!")

def display_flashcards(flashcard_gen):
    """Display flashcards interface"""
    st.header("🎯 AI-Generated Flashcards")
    
    if st.button("🎴 Generate Flashcards"):
        with st.spinner("Creating flashcards for key concepts..."):
            try:
                flashcards = flashcard_gen.generate_flashcards(st.session_state.processed_text)
                st.session_state.flashcards = flashcards
                st.session_state.current_card = 0
                st.session_state.show_answer = False
            except Exception as e:
                st.error(f"Error generating flashcards: {str(e)}")
                return
    
    if hasattr(st.session_state, 'flashcards'):
        display_flashcard_interface()
    else:
        st.info("Click 'Generate Flashcards' to create flashcards from your content.")

def display_flashcard_interface():
    """Display interactive flashcard interface"""
    flashcards = st.session_state.flashcards
    current_card = st.session_state.current_card
    
    if not flashcards:
        st.warning("No flashcards generated.")
        return
    
    # Card counter
    st.markdown(f"### Card {current_card + 1} of {len(flashcards)}")
    
    # Progress bar
    progress = (current_card + 1) / len(flashcards)
    st.progress(progress)
    
    # Flashcard display
    card = flashcards[current_card]
    
    # Card container
    with st.container():
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin: 1rem 0;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        ">
        """, unsafe_allow_html=True)
        
        if not st.session_state.show_answer:
            st.markdown(f"<h3>🤔 Question</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 1.2em;'>{card['question']}</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h3>✅ Answer</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 1.2em;'>{card['answer']}</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Control buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("⬅️ Previous", disabled=(current_card == 0)):
            st.session_state.current_card = max(0, current_card - 1)
            st.session_state.show_answer = False
            st.rerun()
    
    with col2:
        if st.button("🔄 Flip Card"):
            st.session_state.show_answer = not st.session_state.show_answer
            st.rerun()
    
    with col3:
        if st.button("➡️ Next", disabled=(current_card == len(flashcards) - 1)):
            st.session_state.current_card = min(len(flashcards) - 1, current_card + 1)
            st.session_state.show_answer = False
            st.rerun()
    
    with col4:
        if st.button("📥 Download All"):
            flashcard_text = "\n".join([
                f"Q: {card['question']}\nA: {card['answer']}\n---\n" 
                for card in flashcards
            ])
            st.download_button(
                "📥 Download",
                flashcard_text,
                file_name="flashcards.txt",
                mime="text/plain"
            )

def display_rag_chat(rag_chat):
    """Display RAG chat interface"""
    st.header("💬 Ask Questions About Your Content")
    
    # Chat input
    user_question = st.text_input(
        "Ask a question about your uploaded content:",
        placeholder="What are the main topics covered in the material?"
    )
    
    if user_question and st.button("🚀 Ask"):
        with st.spinner("🤔 Thinking and searching through your content..."):
            try:
                response = rag_chat.get_response(user_question, st.session_state.vector_store)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    'question': user_question,
                    'answer': response,
                    'timestamp': st.empty()  # Placeholder for timestamp
                })
                
            except Exception as e:
                st.error(f"Error getting response: {str(e)}")
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown("### 💬 Chat History")
        
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            with st.expander(f"Q: {chat['question'][:50]}...", expanded=(i == 0)):
                st.markdown(f"**Question:** {chat['question']}")
                st.markdown(f"**Answer:** {chat['answer']}")
                
        # Clear chat history button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
    else:
        st.info("Start asking questions about your uploaded content to see the conversation history here.")

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # Load local .env for development if present
    load_dotenv()

    # Prefer Streamlit secrets (on cloud), fallback to OS env / .env (local)
    GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))

    if not GOOGLE_API_KEY:
        st.error(
            "🔑 Google API Key not found! Please add your GOOGLE_API_KEY to "
            "`.streamlit/secrets.toml` (Streamlit Cloud) or to a local `.env` file."
        )
        st.info("Get your API key: https://makersuite.google.com/app/apikey")
        st.stop()

    # Make key available to libraries that read from environment
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

    # Run the app
    main()
