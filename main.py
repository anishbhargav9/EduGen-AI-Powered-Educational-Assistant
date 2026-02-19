import streamlit as st
import sys
import os

# Ensure src is importable
sys.path.insert(0, os.path.dirname(__file__))

from src.document_processor import DocumentProcessor
from src.rag_chat import RAGChat
from src.quiz_generator import QuizGenerator
from src.flashcard_generator import FlashcardGenerator
from src.note_generator import NoteGenerator
from src.utils import clean_text, truncate_text, format_source_name, count_words

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EduGen – AI Learning Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme-safe CSS (no hardcoded colors) ─────────────────────────────────────
st.markdown("""
<style>
/* Card component - inherits theme colors */
.edu-card {
    border: 1px solid rgba(128, 128, 128, 0.3);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
    background: rgba(128, 128, 128, 0.05);
}
.edu-card h4 {
    margin-top: 0;
    color: inherit;
}

/* Flashcard styles */
.flashcard-front {
    border-left: 4px solid #4A90D9;
    padding: 1rem 1.2rem;
    border-radius: 0 8px 8px 0;
    background: rgba(74, 144, 217, 0.08);
    margin-bottom: 0.3rem;
    color: inherit;
}
.flashcard-back {
    border-left: 4px solid #50C878;
    padding: 1rem 1.2rem;
    border-radius: 0 8px 8px 0;
    background: rgba(80, 200, 120, 0.08);
    margin-bottom: 1rem;
    color: inherit;
}

/* Quiz option styles */
.quiz-option {
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    margin: 0.2rem 0;
    color: inherit;
}
.correct-answer {
    background: rgba(80, 200, 120, 0.15);
    border-left: 3px solid #50C878;
}
.wrong-answer {
    background: rgba(220, 80, 80, 0.15);
    border-left: 3px solid #DC5050;
}

/* Source badge */
.source-badge {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    font-size: 0.8rem;
    background: rgba(74, 144, 217, 0.15);
    border: 1px solid rgba(74, 144, 217, 0.4);
    color: inherit;
    margin-bottom: 0.5rem;
}

/* Sidebar section header */
.sidebar-section {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    opacity: 0.6;
    margin-top: 1rem;
    margin-bottom: 0.3rem;
    color: inherit;
}

/* Score display */
.score-display {
    text-align: center;
    padding: 1rem;
    border-radius: 12px;
    border: 2px solid rgba(74, 144, 217, 0.4);
    background: rgba(74, 144, 217, 0.08);
    color: inherit;
}
</style>
""", unsafe_allow_html=True)

# ── Session state initialization ──────────────────────────────────────────────
defaults = {
    "extracted_text": "",
    "source_name": "",
    "chat_history": [],
    "quiz_questions": [],
    "quiz_answers": {},
    "quiz_submitted": False,
    "flashcards": [],
    "flashcard_index": 0,
    "flashcard_revealed": False,
    "notes": "",
    "rag_ready": False,
    "page": "Chat",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Cached resource init ───────────────────────────────────────────────────────
@st.cache_resource
def get_processor():
    return DocumentProcessor()

@st.cache_resource
def get_rag():
    return RAGChat()

@st.cache_resource
def get_quiz_gen():
    return QuizGenerator()

@st.cache_resource
def get_flashcard_gen():
    return FlashcardGenerator()

@st.cache_resource
def get_note_gen():
    return NoteGenerator()

processor = get_processor()
rag = get_rag()
quiz_gen = get_quiz_gen()
flashcard_gen = get_flashcard_gen()
note_gen = get_note_gen()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🎓 EduGen")
    st.markdown("*AI-Powered Learning Assistant*")
    st.divider()

    # Navigation
    st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)
    pages = ["💬 Chat", "❓ Quiz", "🃏 Flashcards", "📝 Notes"]
    page_labels = {"💬 Chat": "Chat", "❓ Quiz": "Quiz", "🃏 Flashcards": "Flashcards", "📝 Notes": "Notes"}
    selected = st.radio("", pages, label_visibility="collapsed")
    st.session_state.page = page_labels[selected]

    st.divider()

    # Document Upload
    st.markdown('<div class="sidebar-section">📂 Load Content</div>', unsafe_allow_html=True)

    input_method = st.radio(
        "Input method",
        ["Upload File", "YouTube URL"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if input_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Upload a file",
            type=["pdf", "docx", "pptx", "txt", "md"],
            label_visibility="collapsed",
        )
        if uploaded_file and st.button("⚡ Process File", use_container_width=True):
            with st.spinner("Extracting content..."):
                try:
                    file_bytes = uploaded_file.read()
                    text = processor.process_file(file_bytes, uploaded_file.name)
                    text = clean_text(text)
                    if not text:
                        st.error("No text found in this file.")
                    else:
                        st.session_state.extracted_text = text
                        st.session_state.source_name = format_source_name(uploaded_file.name)
                        # Add to RAG
                        chunks = processor.get_chunks(text)
                        rag.clear_collection()
                        added = rag.add_chunks(chunks, uploaded_file.name)
                        st.session_state.rag_ready = True
                        st.session_state.chat_history = []
                        st.success(f"✅ Loaded! {count_words(text):,} words, {added} chunks indexed.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    else:
        yt_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
        if st.button("⚡ Process Video", use_container_width=True) and yt_url:
            with st.spinner("Fetching transcript..."):
                try:
                    text = processor.process_youtube(yt_url)
                    text = clean_text(text)
                    st.session_state.extracted_text = text
                    st.session_state.source_name = "YouTube Video"
                    chunks = processor.get_chunks(text)
                    rag.clear_collection()
                    added = rag.add_chunks(chunks, "youtube_video")
                    st.session_state.rag_ready = True
                    st.session_state.chat_history = []
                    st.success(f"✅ Transcript loaded! {count_words(text):,} words, {added} chunks indexed.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.divider()

    # Status
    if st.session_state.source_name:
        st.markdown(f'<div class="source-badge">📄 {st.session_state.source_name}</div>', unsafe_allow_html=True)
        words = count_words(st.session_state.extracted_text)
        st.caption(f"{words:,} words loaded • RAG: {'✅' if st.session_state.rag_ready else '❌'}")
        if st.button("🗑️ Clear All", use_container_width=True):
            rag.clear_collection()
            for key, val in defaults.items():
                st.session_state[key] = val
            st.rerun()
    else:
        st.caption("No content loaded yet.\nUpload a file or paste a YouTube URL to get started.")

# ── Main Content ──────────────────────────────────────────────────────────────
page = st.session_state.page

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CHAT
# ══════════════════════════════════════════════════════════════════════════════
if page == "Chat":
    st.header("💬 Chat with Your Content")

    if not st.session_state.source_name:
        st.info("👈 Load a document or YouTube video from the sidebar to chat about it. You can also ask general questions without loading anything!")

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask anything about your document or any topic..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = rag.chat(prompt, st.session_state.chat_history[:-1])
            st.markdown(answer)

        st.session_state.chat_history.append({"role": "assistant", "content": answer})

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: QUIZ
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Quiz":
    st.header("❓ Quiz Generator")

    with st.expander("⚙️ Quiz Settings", expanded=not bool(st.session_state.quiz_questions)):
        col1, col2 = st.columns(2)
        with col1:
            source_type = st.radio(
                "Generate from",
                ["Loaded Document", "Type a Topic"],
                horizontal=True,
                disabled=not st.session_state.extracted_text,
            )
            if source_type == "Type a Topic" or not st.session_state.extracted_text:
                topic_input = st.text_input("Topic", placeholder="e.g., Photosynthesis, World War 2, Python loops...")
            else:
                topic_input = ""

        with col2:
            num_q = st.slider("Number of Questions", 3, 15, 5)
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

        if st.button("🚀 Generate Quiz", use_container_width=True, type="primary"):
            use_text = st.session_state.extracted_text if source_type == "Loaded Document" and st.session_state.extracted_text else ""
            use_topic = topic_input if not use_text else ""

            if not use_text and not use_topic:
                st.warning("Please load a document or type a topic.")
            else:
                with st.spinner("Generating quiz..."):
                    questions = quiz_gen.generate(
                        source_text=truncate_text(use_text, 6000),
                        topic=use_topic,
                        num_questions=num_q,
                        difficulty=difficulty,
                    )
                if questions:
                    st.session_state.quiz_questions = questions
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_submitted = False
                    st.success(f"✅ {len(questions)} questions generated!")
                    st.rerun()
                else:
                    st.error("Could not generate questions. Try again.")

    # Display Quiz
    if st.session_state.quiz_questions:
        st.divider()
        questions = st.session_state.quiz_questions

        for i, q in enumerate(questions):
            st.markdown(f'<div class="edu-card"><h4>Q{i+1}. {q["question"]}</h4>', unsafe_allow_html=True)

            if not st.session_state.quiz_submitted:
                answer = st.radio(
                    f"Select answer for Q{i+1}",
                    q["options"],
                    key=f"quiz_q_{i}",
                    label_visibility="collapsed",
                )
                st.session_state.quiz_answers[i] = answer
            else:
                user_ans = st.session_state.quiz_answers.get(i, "")
                correct_ans = q["answer"]
                for opt in q["options"]:
                    if opt == correct_ans:
                        st.markdown(f'<div class="quiz-option correct-answer">✅ {opt}</div>', unsafe_allow_html=True)
                    elif opt == user_ans and user_ans != correct_ans:
                        st.markdown(f'<div class="quiz-option wrong-answer">❌ {opt}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="quiz-option">{opt}</div>', unsafe_allow_html=True)
                st.caption(f"💡 {q['explanation']}")

            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        if not st.session_state.quiz_submitted:
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("📊 Submit Quiz", type="primary", use_container_width=True):
                    st.session_state.quiz_submitted = True
                    st.rerun()
        else:
            # Score
            score = sum(
                1 for i, q in enumerate(questions)
                if st.session_state.quiz_answers.get(i) == q["answer"]
            )
            total = len(questions)
            pct = int(score / total * 100)
            emoji = "🏆" if pct >= 80 else "👍" if pct >= 60 else "📚"

            st.markdown(f"""
<div class="score-display">
  <h2>{emoji} {score}/{total} ({pct}%)</h2>
  <p>{"Excellent work!" if pct >= 80 else "Good effort! Review the explanations." if pct >= 60 else "Keep studying! Check the answers above."}</p>
</div>
""", unsafe_allow_html=True)

            if st.button("🔄 New Quiz", use_container_width=True):
                st.session_state.quiz_questions = []
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: FLASHCARDS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Flashcards":
    st.header("🃏 Flashcard Generator")

    with st.expander("⚙️ Flashcard Settings", expanded=not bool(st.session_state.flashcards)):
        source_type = st.radio(
            "Generate from",
            ["Loaded Document", "Type a Topic"],
            horizontal=True,
            disabled=not st.session_state.extracted_text,
        )
        if source_type == "Type a Topic" or not st.session_state.extracted_text:
            topic_input = st.text_input("Topic", placeholder="e.g., Machine Learning, Newton's Laws...")
        else:
            topic_input = ""

        num_cards = st.slider("Number of Flashcards", 5, 20, 10)

        if st.button("🚀 Generate Flashcards", use_container_width=True, type="primary"):
            use_text = st.session_state.extracted_text if source_type == "Loaded Document" and st.session_state.extracted_text else ""
            use_topic = topic_input if not use_text else ""

            if not use_text and not use_topic:
                st.warning("Please load a document or type a topic.")
            else:
                with st.spinner("Creating flashcards..."):
                    cards = flashcard_gen.generate(
                        source_text=truncate_text(use_text, 6000),
                        topic=use_topic,
                        num_cards=num_cards,
                    )
                if cards:
                    st.session_state.flashcards = cards
                    st.session_state.flashcard_index = 0
                    st.session_state.flashcard_revealed = False
                    st.success(f"✅ {len(cards)} flashcards created!")
                    st.rerun()
                else:
                    st.error("Could not generate flashcards. Try again.")

    # Display Flashcards — two modes
    if st.session_state.flashcards:
        cards = st.session_state.flashcards
        st.divider()

        view_mode = st.radio("View mode", ["📖 One by One", "📋 All Cards"], horizontal=True)

        if view_mode == "📖 One by One":
            idx = st.session_state.flashcard_index
            card = cards[idx]

            st.markdown(f"**Card {idx + 1} of {len(cards)}**")
            st.progress((idx + 1) / len(cards))

            st.markdown(f'<div class="flashcard-front"><strong>📌 Front</strong><br><br>{card["front"]}</div>', unsafe_allow_html=True)

            if st.session_state.flashcard_revealed:
                st.markdown(f'<div class="flashcard-back"><strong>💡 Back</strong><br><br>{card["back"]}</div>', unsafe_allow_html=True)
            else:
                if st.button("👁️ Reveal Answer", use_container_width=True):
                    st.session_state.flashcard_revealed = True
                    st.rerun()

            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("⬅️ Previous", disabled=idx == 0, use_container_width=True):
                    st.session_state.flashcard_index -= 1
                    st.session_state.flashcard_revealed = False
                    st.rerun()
            with col3:
                if st.button("Next ➡️", disabled=idx == len(cards) - 1, use_container_width=True):
                    st.session_state.flashcard_index += 1
                    st.session_state.flashcard_revealed = False
                    st.rerun()

        else:
            for i, card in enumerate(cards):
                st.markdown(f'<div class="flashcard-front"><strong>Q{i+1}. {card["front"]}</strong></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="flashcard-back">💡 {card["back"]}</div>', unsafe_allow_html=True)

        if st.button("🔄 New Flashcards"):
            st.session_state.flashcards = []
            st.session_state.flashcard_index = 0
            st.session_state.flashcard_revealed = False
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: NOTES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Notes":
    st.header("📝 Smart Notes Generator")

    with st.expander("⚙️ Notes Settings", expanded=not bool(st.session_state.notes)):
        col1, col2 = st.columns(2)
        with col1:
            source_type = st.radio(
                "Generate from",
                ["Loaded Document", "Type a Topic"],
                horizontal=True,
                disabled=not st.session_state.extracted_text,
            )
            if source_type == "Type a Topic" or not st.session_state.extracted_text:
                topic_input = st.text_input("Topic", placeholder="e.g., Quantum Computing, French Revolution...")
            else:
                topic_input = ""
        with col2:
            style = st.selectbox(
                "Notes Style",
                ["Detailed", "Summary", "Bullet Points", "Cornell Notes"],
            )

        if st.button("🚀 Generate Notes", use_container_width=True, type="primary"):
            use_text = st.session_state.extracted_text if source_type == "Loaded Document" and st.session_state.extracted_text else ""
            use_topic = topic_input if not use_text else ""

            if not use_text and not use_topic:
                st.warning("Please load a document or type a topic.")
            else:
                with st.spinner("Writing your notes..."):
                    notes = note_gen.generate(
                        source_text=truncate_text(use_text, 7000),
                        topic=use_topic,
                        style=style,
                    )
                st.session_state.notes = notes
                st.rerun()

    if st.session_state.notes:
        st.divider()
        st.markdown(st.session_state.notes)
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇️ Download Notes (.md)",
                data=st.session_state.notes,
                file_name="edugen_notes.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col2:
            if st.button("🔄 Regenerate Notes", use_container_width=True):
                st.session_state.notes = ""
                st.rerun()