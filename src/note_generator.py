import google.generativeai as genai
import re
from typing import Dict, Any, List
from config import GOOGLE_API_KEY, GEMINI_MODEL

class NoteGenerator:
    """Generate structured notes from educational content"""
    
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    def generate_notes(self, text: str, settings: Dict[str, Any]) -> str:
        """Generate comprehensive notes based on the provided text and settings"""
        
        style = settings.get('style', 'Detailed')
        include_examples = settings.get('include_examples', True)
        
        if style == 'Summary':
            return self.generate_summary_notes(text, include_examples)
        elif style == 'Bullet Points':
            return self.generate_bullet_notes(text, include_examples)
        else:  # Detailed
            return self.generate_detailed_notes(text, include_examples)
    
    def generate_detailed_notes(self, text: str, include_examples: bool = True) -> str:
        """Generate detailed, comprehensive study notes"""
        
        examples_instruction = "Include relevant examples and case studies where applicable." if include_examples else "Focus on concepts without detailed examples."
        
        prompt = f"""
        Based on the following educational content, create comprehensive, well-structured study notes.

        Content: {text[:4000]}...

        Requirements:
        - Create detailed, organized study notes
        - Use clear headings and subheadings
        - Include key concepts, definitions, and important points
        - {examples_instruction}
        - Use markdown formatting for better readability
        - Structure the notes logically with proper flow
        - Highlight important terms and concepts
        - Include summary sections for complex topics

        Format the notes using markdown with:
        - # for main topics
        - ## for subtopics  
        - ### for detailed sections
        - **bold** for important terms
        - *italic* for emphasis
        - Bullet points for lists
        - Numbered lists for processes/steps

        Generate comprehensive study notes now:
        """
        
        try:
            response = self.model.generate_content(prompt)
            notes = self.format_notes(response.text)
            return notes
        except Exception as e:
            return self.create_fallback_detailed_notes(text)
    
    def generate_summary_notes(self, text: str, include_examples: bool = True) -> str:
        """Generate concise summary notes"""
        
        examples_instruction = "Include brief examples where helpful." if include_examples else "Focus only on key concepts."
        
        prompt = f"""
        Create concise summary notes from the following educational content.

        Content: {text[:4000]}...

        Requirements:
        - Summarize main concepts and key points
        - Keep it concise but comprehensive
        - {examples_instruction}
        - Use clear, simple language
        - Focus on the most important information
        - Use markdown formatting

        Generate summary notes now:
        """
        
        try:
            response = self.model.generate_content(prompt)
            notes = self.format_notes(response.text)
            return notes
        except Exception as e:
            return self.create_fallback_summary_notes(text)
    
    def generate_bullet_notes(self, text: str, include_examples: bool = True) -> str:
        """Generate bullet-point style notes"""
        
        examples_instruction = "Include example bullets where relevant." if include_examples else "Focus on main concept bullets only."
        
        prompt = f"""
        Create bullet-point style study notes from the following educational content.

        Content: {text[:4000]}...

        Requirements:
        - Use bullet points and sub-bullets extensively
        - Organize information hierarchically
        - {examples_instruction}
        - Keep each bullet point concise but informative
        - Use markdown formatting with proper bullet structure
        - Group related concepts together

        Generate bullet-point notes now:
        """
        
        try:
            response = self.model.generate_content(prompt)
            notes = self.format_notes(response.text)
            return notes
        except Exception as e:
            return self.create_fallback_bullet_notes(text)
    
    def format_notes(self, raw_notes: str) -> str:
        """Clean and format the generated notes"""
        
        # Remove any code block markers
        notes = re.sub(r'```markdown\n?', '', raw_notes)
        notes = re.sub(r'```\n?', '', notes)
        
        # Ensure proper spacing around headers
        notes = re.sub(r'\n(#{1,6})', r'\n\n\1', notes)
        notes = re.sub(r'(#{1,6}.*)\n([^\n#])', r'\1\n\n\2', notes)
        
        # Clean up excessive whitespace
        notes = re.sub(r'\n{3,}', '\n\n', notes)
        
        # Add table of contents if the notes are long enough
        if len(notes) > 1000:
            toc = self.generate_table_of_contents(notes)
            if toc:
                notes = f"{toc}\n\n---\n\n{notes}"
        
        return notes.strip()
    
    def generate_table_of_contents(self, notes: str) -> str:
        """Generate a table of contents from the notes"""
        
        # Find all headers
        headers = re.findall(r'^(#{1,6})\s*(.+)$', notes, re.MULTILINE)
        
        if len(headers) < 3:  # Only generate TOC if there are enough headers
            return ""
        
        toc = "## 📚 Table of Contents\n\n"
        
        for level, title in headers:
            # Calculate indentation based on header level
            indent = "  " * (len(level) - 1)
            # Create anchor link
            anchor = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-').lower()
            toc += f"{indent}- [{title}](#{anchor})\n"
        
        return toc
    
    def extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from the text"""
        
        prompt = f"""
        Extract the key concepts, terms, and important ideas from the following text.
        Return them as a simple list, one concept per line.

        Text: {text[:2000]}...

        Key concepts:
        """
        
        try:
            response = self.model.generate_content(prompt)
            concepts = [line.strip().lstrip('- ').lstrip('* ') 
                       for line in response.text.split('\n') 
                       if line.strip() and not line.strip().startswith('#')]
            return concepts[:10]  # Limit to top 10 concepts
        except Exception as e:
            # Fallback: extract some concepts using basic text analysis
            words = text.split()
            # Simple heuristic: find capitalized words and phrases
            concepts = []
            for i, word in enumerate(words):
                if word[0].isupper() and len(word) > 3:
                    concepts.append(word)
            return list(set(concepts))[:10]
    
    def create_fallback_detailed_notes(self, text: str) -> str:
        """Create fallback detailed notes if AI generation fails"""
        
        # Basic structure with available content
        concepts = self.extract_key_concepts(text)
        
        notes = f"""# 📚 Study Notes

## 📖 Overview
This document contains study notes generated from the provided educational content.

## 🔑 Key Concepts
"""
        
        for concept in concepts:
            notes += f"- **{concept}**\n"
        
        notes += f"""

## 📝 Content Summary
The material covers various educational topics. Please try regenerating the notes for more detailed content.

## 💡 Important Points
- Review the source material for comprehensive understanding
- Consider generating notes again for better results
- Use the quiz and flashcard features for active learning

---
*Note: These are fallback notes. For better results, please try generating notes again.*
"""
        
        return notes
    
    def create_fallback_summary_notes(self, text: str) -> str:
        """Create fallback summary notes"""
        
        return f"""# 📝 Summary Notes

## Key Points
- Educational content processed
- Multiple topics covered
- Review recommended

## Next Steps
- Try regenerating notes for detailed content
- Use other learning features (quiz, flashcards)
- Consult original source material

---
*These are simplified notes. Please regenerate for detailed content.*
"""
    
    def create_fallback_bullet_notes(self, text: str) -> str:
        """Create fallback bullet notes"""
        
        return f"""# 🎯 Key Points

## Main Topics
- Content analysis completed
- Educational material processed
- Key information extracted

## Study Recommendations
- Review source material
- Use interactive quiz feature
- Create flashcards for memorization
- Try regenerating for detailed bullets

## Next Actions
- Regenerate notes for better results
- Explore other learning tools
- Practice with generated quizzes

---
*Note: Please regenerate for detailed bullet points.*
"""
    
    def add_study_tips(self, notes: str) -> str:
        """Add study tips and learning strategies to the notes"""
        
        study_tips = """

---

## 🎯 Study Tips

### Effective Learning Strategies
- **Active Reading**: Take notes while reading these materials
- **Spaced Repetition**: Review these notes regularly over time
- **Self-Testing**: Use the quiz feature to test your knowledge
- **Teach Others**: Explain concepts from these notes to someone else

### Note-Taking Tips
- **Highlight Key Terms**: Mark important concepts for quick review
- **Create Mind Maps**: Visualize connections between topics
- **Summarize Sections**: Write brief summaries in your own words
- **Ask Questions**: Note any unclear concepts for further research

### Memory Techniques
- **Use Acronyms**: Create memorable abbreviations for lists
- **Make Associations**: Connect new information to what you already know
- **Practice Recall**: Test yourself without looking at the notes
- **Use Flashcards**: Create flashcards for key terms and definitions
"""
        
        return notes + study_tips
    
    def generate_notes_with_learning_objectives(self, text: str, settings: Dict[str, Any]) -> str:
        """Generate notes with clear learning objectives"""
        
        # First generate the main notes
        main_notes = self.generate_notes(text, settings)
        
        # Add learning objectives at the beginning
        objectives_prompt = f"""
        Based on this educational content, create 3-5 clear learning objectives that students should achieve after studying this material.

        Content: {text[:2000]}...

        Format as:
        ## 🎯 Learning Objectives
        After studying these notes, you should be able to:
        1. [Objective 1]
        2. [Objective 2]
        ...
        """
        
        try:
            response = self.model.generate_content(objectives_prompt)
            objectives = response.text.strip()
            
            # Insert objectives at the beginning of the notes
            if main_notes.startswith('# '):
                # Find the end of the first header line
                first_newline = main_notes.find('\n')
                if first_newline != -1:
                    title = main_notes[:first_newline]
                    rest = main_notes[first_newline:]
                    main_notes = f"{title}\n\n{objectives}\n{rest}"
            else:
                main_notes = f"{objectives}\n\n{main_notes}"
                
        except Exception as e:
            # If objectives generation fails, just return the main notes
            pass
        
        return main_notes