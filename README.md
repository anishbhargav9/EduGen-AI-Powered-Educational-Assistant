# 📘 EduGen - AI-Powered Learning Assistant  

EduGen is an AI-powered education platform that helps students and educators generate **quizzes, notes, and flashcards** from uploaded documents.  
It also provides an **interactive RAG-based chatbot** for personalized learning.  

---

## 🚀 Features
- 📄 **Document Processing** – Upload PDFs, DOCX, or text files for analysis  
- ❓ **Quiz Generator** – Automatically create quizzes from learning material  
- 📝 **Notes Generator** – Summarize content into structured notes  
- 🎴 **Flashcards Generator** – Generate flashcards for quick revision  
- 🤖 **RAG Chatbot** – Chat with your documents using Retrieval-Augmented Generation (RAG)  
- 🌐 **Streamlit Web App** – Simple and interactive user interface  

---

## 🛠️ Tech Stack
- **Frontend/UI**: [Streamlit](https://streamlit.io/)  
- **Backend**: Python  
- **AI/ML**: [LangChain](https://www.langchain.com/), [FAISS](https://github.com/facebookresearch/faiss)  
- **APIs**: Google Generative AI / Gemini  
- **Others**: dotenv, tempfile, pathlib  

---

## 📂 Project Structure
EduGen/
│── main.py # Streamlit app entry point
│── requirements.txt # Dependencies
│── README.md # Project documentation
│── .gitignore # Git ignore rules
│
└── src/
│── document_processor.py
│── quiz_generator.py
│── note_generator.py
│── flashcard_generator.py
│── rag_chat.py
│── utils.py


---

## ⚡ Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/EduGen.git
   cd EduGen

2.Create & activate a virtual environment:
python -m venv venv
venv\Scripts\activate   # On Windows
source venv/bin/activate # On Mac/Linux

3.Install dependencies:
pip install -r requirements.txt

4.Run the Streamlit app:
streamlit run main.py

