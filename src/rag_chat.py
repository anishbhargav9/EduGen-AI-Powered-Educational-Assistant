import os
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.schema import Document
from typing import List, Optional
from config import (
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    EMBEDDING_MODEL,
    MAX_CHUNK_SIZE,
    CHUNK_OVERLAP,
    SIMILARITY_TOP_K,
)

class RAGChat:
    """RAG-powered chat system for answering questions about uploaded content"""
    
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)

        # Initialize embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            google_api_key=GOOGLE_API_KEY,
            transport="grpc"
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=MAX_CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        self.vector_store: Optional[FAISS] = None
    
    def create_vector_store(self, text: str) -> FAISS:
        """Create FAISS vector store from text content"""
        try:
            # Split text into chunks
            documents = self.text_splitter.split_text(text)
            
            # Create Document objects
            docs = [Document(page_content=doc, metadata={"source": "uploaded_content"}) for doc in documents]
            
            # Create vector store
            self.vector_store = FAISS.from_documents(docs, self.embeddings)
            return self.vector_store
            
        except Exception as e:
            raise Exception(f"Error creating vector store: {str(e)}")
    
    def get_response(self, query: str, vector_store: Optional[FAISS] = None) -> str:
        """Get AI response using RAG approach"""
        if vector_store is None:
            vector_store = self.vector_store
        
        if vector_store is None:
            return "No content has been uploaded yet. Please upload some documents first."
        
        try:
            # Retrieve relevant documents
            relevant_docs = vector_store.similarity_search(query, k=SIMILARITY_TOP_K)
            
            if not relevant_docs:
                return "I couldn't find relevant information in your uploaded content to answer that question."
            
            # Prepare context
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Create prompt
            prompt = self.create_rag_prompt(query, context)
            
            # Get response from Gemini
            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.3}
            )
            
            return self.format_response(response.text, relevant_docs)
            
        except Exception as e:
            return f"Sorry, I encountered an error while processing your question: {str(e)}"
    
    def create_rag_prompt(self, query: str, context: str) -> str:
        """Create a prompt for RAG-based question answering"""
        return f"""
You are an intelligent educational assistant. Answer the user's question based on the provided context from their uploaded educational materials.

CONTEXT:
{context[:3000]}...

QUESTION: {query}

INSTRUCTIONS:
- Answer based primarily on the provided context
- Be comprehensive but concise
- If the context doesn't contain enough information, say so clearly
- Use a helpful, educational tone
- Structure your answer clearly with examples when possible
- If relevant, suggest related topics the user might want to explore

ANSWER:
"""
    
    def format_response(self, response_text: str, relevant_docs: List[Document]) -> str:
        """Format the AI response with source information"""
        formatted_response = response_text.strip()
        
        if relevant_docs:
            formatted_response += "\n\n---\n"
            formatted_response += "*This answer is based on your uploaded educational content.*"
        
        return formatted_response
    
    def save_vector_store(self, path: str) -> bool:
        """Save vector store to disk"""
        try:
            if self.vector_store:
                self.vector_store.save_local(path)
                return True
            return False
        except Exception:
            return False
    
    def load_vector_store(self, path: str) -> bool:
        """Load vector store from disk"""
        try:
            if os.path.exists(path):
                self.vector_store = FAISS.load_local(path, self.embeddings, allow_dangerous_deserialization=True)
                return True
            return False
        except Exception:
            return False
