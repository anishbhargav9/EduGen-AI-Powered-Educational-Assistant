import json
import re
from src.gemini_client import GeminiClient


class FlashcardGenerator:
    """Generates flashcards (front/back) from document text or a typed topic."""

    def __init__(self):
        self.llm = GeminiClient()

    def generate(
        self,
        source_text: str = "",
        topic: str = "",
        num_cards: int = 10,
    ) -> list[dict]:
        """
        Generate flashcards.
        Returns a list of dicts: [{"front": ..., "back": ...}]
        """
        if source_text:
            content_section = f"""Use the following document content as your source:
=== DOCUMENT CONTENT ===
{source_text[:6000]}
=== END OF CONTENT ==="""
        else:
            content_section = f"Generate flashcards about the topic: {topic}"

        prompt = f"""You are an expert educator creating study flashcards for students.

{content_section}

Create exactly {num_cards} flashcards.

Return ONLY a valid JSON array. No extra text, no markdown, no code blocks.
Format:
[
  {{
    "front": "Term or question on the front of the card",
    "back": "Clear, concise definition or answer on the back"
  }}
]

Rules:
- Front: a key term, concept, or question
- Back: a clear, memorable explanation (2-4 sentences max)
- Cover the most important concepts
- Make them useful for exam preparation"""

        response = self.llm.generate(prompt, temperature=0.5)
        return self._parse_response(response)

    def _parse_response(self, response: str) -> list[dict]:
        """Parse JSON from LLM response safely."""
        try:
            clean = re.sub(r"```(?:json)?", "", response).replace("```", "").strip()
            cards = json.loads(clean)
            validated = []
            for card in cards:
                if "front" in card and "back" in card:
                    validated.append(card)
            return validated
        except Exception:
            return []