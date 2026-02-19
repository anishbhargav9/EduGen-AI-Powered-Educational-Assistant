from groq import Groq
import config


class GroqClient:
    """Centralized Groq LLM service."""

    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL

    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate text from a prompt."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=8192,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def get_embedding(self, text: str) -> list:
        """Get embedding using local sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer
            if not hasattr(self, '_embed_model'):
                self._embed_model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = self._embed_model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            raise RuntimeError(f"Embedding error: {str(e)}")