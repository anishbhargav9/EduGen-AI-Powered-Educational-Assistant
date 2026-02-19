from google import genai
from google.genai import types
import config


class GeminiClient:
    """Centralized Gemini LLM service. Single point of contact for all LLM calls."""

    def __init__(self):
        self.client = genai.Client(api_key=config.GOOGLE_API_KEY)
        self.model = config.GEMINI_MODEL

    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate text from a prompt."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=8192,
                ),
            )
            answer = ""
            if response.candidates:
                parts = response.candidates[0].content.parts
                answer = "".join([p.text for p in parts if hasattr(p, "text")])
            return answer.strip() if answer.strip() else "No response generated."
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def get_embedding(self, text: str) -> list:
        """Get embedding vector for a text string."""
        try:
            result = self.client.models.embed_content(
                model=config.EMBEDDING_MODEL,
                contents=text,
            )
            return result.embeddings[0].values
        except Exception as e:
            raise RuntimeError(f"Embedding error: {str(e)}")