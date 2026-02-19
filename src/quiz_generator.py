import json
import re
from src.groq_client import GroqClient


class QuizGenerator:
    """Generates MCQ quizzes from document text or a typed topic."""

    def __init__(self):
        self.llm = GroqClient()

    def generate(
        self,
        source_text: str = "",
        topic: str = "",
        num_questions: int = 5,
        difficulty: str = "Medium",
    ) -> list[dict]:
        """
        Generate quiz questions.
        Returns a list of dicts:
        [{"question": ..., "options": [...], "answer": ..., "explanation": ...}]
        """
        if source_text:
            content_section = f"""Use the following document content as your source:
=== DOCUMENT CONTENT ===
{source_text[:6000]}
=== END OF CONTENT ==="""
        else:
            content_section = f"Generate questions about the topic: {topic}"

        prompt = f"""You are an expert quiz creator for students.

{content_section}

Create exactly {num_questions} multiple choice questions at {difficulty} difficulty level.

Return ONLY a valid JSON array. No extra text, no markdown, no code blocks.
Format:
[
  {{
    "question": "Question text here?",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "answer": "A) option1",
    "explanation": "Brief explanation of why this is correct."
  }}
]

Rules:
- Each question must have exactly 4 options labeled A), B), C), D)
- The answer must exactly match one of the options
- Make questions clear and educational
- Vary the correct answer position (not always A)"""

        response = self.llm.generate(prompt, temperature=0.5)
        return self._parse_response(response)

    def _parse_response(self, response: str) -> list[dict]:
        """Parse JSON from LLM response safely."""
        try:
            # Strip markdown code blocks if present
            clean = re.sub(r"```(?:json)?", "", response).replace("```", "").strip()
            questions = json.loads(clean)
            # Validate structure
            validated = []
            for q in questions:
                if all(k in q for k in ["question", "options", "answer", "explanation"]):
                    validated.append(q)
            return validated
        except Exception:
            return []