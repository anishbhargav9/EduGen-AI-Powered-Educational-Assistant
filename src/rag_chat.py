import chromadb
from chromadb.config import Settings
import uuid
import config
from src.gemini_client import GeminiClient


class RAGChat:
    """
    Retrieval-Augmented Generation chat using ChromaDB for vector storage
    and Gemini for answer generation.
    """

    def __init__(self):
        self.llm = GeminiClient()
        self.chroma_client = chromadb.PersistentClient(
            path=config.CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="edugen_documents",
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[str], source_name: str = "document") -> int:
        """Embed and store text chunks in ChromaDB."""
        if not chunks:
            return 0

        embeddings = []
        valid_chunks = []
        valid_ids = []

        for chunk in chunks:
            try:
                embedding = self.llm.get_embedding(chunk)
                embeddings.append(embedding)
                valid_chunks.append(chunk)
                valid_ids.append(str(uuid.uuid4()))
            except Exception:
                continue

        if valid_chunks:
            self.collection.add(
                ids=valid_ids,
                embeddings=embeddings,
                documents=valid_chunks,
                metadatas=[{"source": source_name} for _ in valid_chunks],
            )

        return len(valid_chunks)

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """Retrieve most relevant chunks for a query."""
        try:
            query_embedding = self.llm.get_embedding(query)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self.collection.count()),
            )
            return results["documents"][0] if results["documents"] else []
        except Exception:
            return []

    def chat(self, question: str, chat_history: list[dict] = None) -> str:
        """Answer a question using retrieved context + Gemini."""
        context_chunks = self.retrieve(question)

        if not context_chunks:
            # No documents loaded, answer from general knowledge
            prompt = f"""You are EduGen, a helpful AI learning assistant.
Answer the following question clearly and educationally:

Question: {question}

Note: No document context is available. Answer from your general knowledge."""
        else:
            context = "\n\n".join(context_chunks)
            history_text = ""
            if chat_history:
                history_text = "\n".join(
                    [f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history[-6:]]
                )

            prompt = f"""You are EduGen, a helpful AI learning assistant.
Use the context below to answer the student's question accurately and clearly.
If the answer is not in the context, say so and answer from general knowledge.

=== DOCUMENT CONTEXT ===
{context}

=== CONVERSATION HISTORY ===
{history_text}

=== STUDENT QUESTION ===
{question}

=== YOUR ANSWER ===
Provide a clear, well-structured, educational answer:"""

        return self.llm.generate(prompt, temperature=0.3)

    def clear_collection(self):
        """Delete all stored documents (reset)."""
        self.chroma_client.delete_collection("edugen_documents")
        self.collection = self.chroma_client.get_or_create_collection(
            name="edugen_documents",
            metadata={"hnsw:space": "cosine"},
        )

    def document_count(self) -> int:
        """Return number of stored chunks."""
        return self.collection.count()