import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import chromadb
from chromadb.config import Settings
import uuid
import config
from src.groq_client import GroqClient


class RAGChat:
    """
    Retrieval-Augmented Generation chat using ChromaDB for vector storage
    and Groq for answer generation.
    """

    def __init__(self):
        self.llm = GroqClient()

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
            count = self.collection.count()

            if count == 0:
                return []

            query_embedding = self.llm.get_embedding(query)

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, count),
            )

            if results and results.get("documents"):
                return results["documents"][0]

            return []

        except Exception:
            return []

    def chat(self, question: str, chat_history: list[dict] = None) -> str:
        """Answer a question using retrieved context + Groq."""
        context_chunks = self.retrieve(question)

        if not context_chunks:
            prompt = f"""You are EduGen, a helpful AI learning assistant.
Answer the following question clearly and educationally:

Question: {question}

Note: No document context is available. Answer from your general knowledge."""
        else:
            context = "\n\n".join(context_chunks)

            history_text = ""
            if chat_history:
                history_text = "\n".join(
                    [
                        f"{msg['role'].capitalize()}: {msg['content']}"
                        for msg in chat_history[-6:]
                    ]
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
        try:
            self.chroma_client.delete_collection("edugen_documents")
        except Exception:
            pass

        self.collection = self.chroma_client.get_or_create_collection(
            name="edugen_documents",
            metadata={"hnsw:space": "cosine"},
        )

    def document_count(self) -> int:
        """Return number of stored chunks."""
        try:
            return self.collection.count()
        except Exception:
            return 0
