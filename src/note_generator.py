from src.groq_client import GroqClient


class NoteGenerator:
    """Generates structured study notes from document text or a typed topic."""

    def __init__(self):
        self.llm = GroqClient()

    def generate(
        self,
        source_text: str = "",
        topic: str = "",
        style: str = "Detailed",
    ) -> str:
        """
        Generate study notes in markdown format.
        style options: "Detailed", "Summary", "Bullet Points", "Cornell Notes"
        """
        if source_text:
            content_section = f"""Use the following document content as your source:
=== DOCUMENT CONTENT ===
{source_text[:7000]}
=== END OF CONTENT ==="""
        else:
            content_section = f"Generate notes about the topic: {topic}"

        style_instructions = {
            "Detailed": "Create comprehensive, detailed notes covering all key concepts with explanations and examples.",
            "Summary": "Create a concise summary hitting only the most important points. Keep it brief and scannable.",
            "Bullet Points": "Create notes entirely in bullet point format. Use nested bullets for sub-points.",
            "Cornell Notes": """Create notes in Cornell format:
- Main Notes section (right column): Key concepts and details
- Cues section (left column): Questions and keywords
- Summary section (bottom): 3-5 sentence summary of everything""",
        }

        instruction = style_instructions.get(style, style_instructions["Detailed"])

        prompt = f"""You are an expert study notes creator for students.

{content_section}

Note Style: {style}
Instructions: {instruction}

Create well-structured study notes in Markdown format.
Use proper markdown:
- # for main title
- ## for major sections
- ### for subsections
- **bold** for key terms
- Bullet points where appropriate
- > for important quotes or definitions

Make the notes clear, educational, and exam-ready.
Start directly with the notes content:"""

        return self.llm.generate(prompt, temperature=0.4)