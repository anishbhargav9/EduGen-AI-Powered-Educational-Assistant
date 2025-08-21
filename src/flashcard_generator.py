import google.generativeai as genai
import json
import re
import random
from typing import List, Dict, Any
from config import GOOGLE_API_KEY, GEMINI_MODEL

class FlashcardGenerator:
    """Generate flashcards for key concepts and terms"""
    
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    def generate_flashcards(self, text: str, num_cards: int = 20) -> List[Dict[str, str]]:
        """Generate flashcards from the provided text"""
        
        prompt = f"""
        Based on the following educational content, create {num_cards} flashcards for key concepts, definitions, and important information.

        Content: {text[:4000]}...

        Requirements:
        - Focus on key terms, concepts, definitions, and important facts
        - Questions should be clear and concise
        - Answers should be informative but not too long (1-3 sentences)
        - Include a mix of:
          * Definition questions (What is...?)
          * Conceptual questions (How does...?)
          * Application questions (Why is...?)
          * Factual questions (When/Where...?)
        - Avoid overly complex or trick questions
        - Make sure answers are accurate and complete

        Format your response as a JSON array with this structure:
        [
            {{
                "question": "What is the definition of [key term]?",
                "answer": "Clear, concise answer explaining the concept."
            }},
            {{
                "question": "How does [process/concept] work?",
                "answer": "Explanation of the process or concept."
            }}
        ]

        Return only the JSON array, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            flashcards = self.parse_flashcard_response(response.text)
            
            # If we got fewer cards than requested, try to generate more
            if len(flashcards) < num_cards:
                additional_cards = self.generate_additional_flashcards(text, num_cards - len(flashcards))
                flashcards.extend(additional_cards)
            
            # Shuffle and return requested number
            random.shuffle(flashcards)
            return flashcards[:num_cards]
            
        except Exception as e:
            return self.create_fallback_flashcards(text, num_cards)
    
    def generate_additional_flashcards(self, text: str, num_cards: int) -> List[Dict[str, str]]:
        """Generate additional flashcards focusing on different aspects"""
        
        prompt = f"""
        Create {num_cards} more flashcards from this educational content, focusing on different aspects than basic definitions.

        Content: {text[:3000]}...

        Focus on:
        - Cause and effect relationships
        - Comparisons and contrasts
        - Processes and procedures
        - Applications and examples
        - Connections between concepts

        Format as JSON array:
        [
            {{
                "question": "Question here?",
                "answer": "Answer here."
            }}
        ]
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self.parse_flashcard_response(response.text)
        except Exception as e:
            return []
    
    def parse_flashcard_response(self, response_text: str) -> List[Dict[str, str]]:
        """Parse the AI response to extract flashcards"""
        
        try:
            # Clean the response
            cleaned_text = self.clean_json_response(response_text)
            
            # Parse JSON
            flashcards = json.loads(cleaned_text)
            
            # Validate flashcards
            valid_flashcards = []
            for card in flashcards:
                if self.validate_flashcard(card):
                    # Clean question and answer
                    card['question'] = self.clean_text(card['question'])
                    card['answer'] = self.clean_text(card['answer'])
                    valid_flashcards.append(card)
            
            return valid_flashcards
            
        except json.JSONDecodeError:
            # Try to extract individual flashcards using regex
            return self.extract_flashcards_with_regex(response_text)
    
    def clean_json_response(self, text: str) -> str:
        """Clean AI response to extract valid JSON"""
        
        # Remove markdown code blocks
        text = re.sub(r'```json\n?', '', text)
        text = re.sub(r'```\n?', '', text)
        
        # Find JSON array
        start = text.find('[')
        end = text.rfind(']') + 1
        
        if start != -1 and end > start:
            return text[start:end]
        
        return text
    
    def extract_flashcards_with_regex(self, text: str) -> List[Dict[str, str]]:
        """Extract flashcards using regex if JSON parsing fails"""
        
        flashcards = []
        
        # Try to find question-answer pairs
        patterns = [
            r'"question":\s*"([^"]+)",\s*"answer":\s*"([^"]+)"',
            r'Question:\s*([^\n]+)\s*Answer:\s*([^\n]+)',
            r'Q:\s*([^\n]+)\s*A:\s*([^\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for question, answer in matches:
                if len(question.strip()) > 5 and len(answer.strip()) > 5:
                    flashcards.append({
                        'question': self.clean_text(question),
                        'answer': self.clean_text(answer)
                    })
        
        return flashcards
    
    def validate_flashcard(self, card: Dict[str, str]) -> bool:
        """Validate flashcard structure and content"""
        
        if not isinstance(card, dict):
            return False
        
        if 'question' not in card or 'answer' not in card:
            return False
        
        question = card['question'].strip()
        answer = card['answer'].strip()
        
        # Check minimum length
        if len(question) < 5 or len(answer) < 5:
            return False
        
        # Check maximum length (to avoid overly long cards)
        if len(question) > 200 or len(answer) > 500:
            return False
        
        return True
    
    def clean_text(self, text: str) -> str:
        """Clean and format text content"""
        
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove quotes at the beginning and end
        text = text.strip('"\'')
        
        # Capitalize first letter if it's not already
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        # Ensure question ends with question mark
        if '?' in text and not text.endswith('?'):
            # Move question mark to the end if it's misplaced
            text = text.replace('?', '') + '?'
        
        return text
    
    def create_fallback_flashcards(self, text: str, num_cards: int) -> List[Dict[str, str]]:
        """Create fallback flashcards if AI generation fails"""
        
        # Extract key terms and concepts using basic text analysis
        key_terms = self.extract_key_terms(text)
        
        flashcards = []
        
        # Create basic definition flashcards
        for i, term in enumerate(key_terms[:num_cards]):
            flashcards.append({
                'question': f"What is {term}?",
                'answer': f"Please refer to the source material for the definition of {term}. Consider regenerating flashcards for detailed answers."
            })
        
        # Fill remaining slots with generic cards
        while len(flashcards) < num_cards:
            flashcards.append({
                'question': "What are the main topics covered in this material?",
                'answer': "Please regenerate flashcards for specific content-based questions and answers."
            })
        
        return flashcards
    
    def extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text using basic analysis"""
        
        # Split text into words
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter for likely key terms (capitalized, reasonable length)
        key_terms = []
        for word in words:
            if 3 <= len(word) <= 30 and word.lower() not in ['the', 'and', 'for', 'with']:
                key_terms.append(word)
        
        # Remove duplicates and return
        return list(set(key_terms))
    
    def generate_definition_flashcards(self, text: str, num_cards: int = 10) -> List[Dict[str, str]]:
        """Generate flashcards focused specifically on definitions"""
        
        prompt = f"""
        Extract key terms and their definitions from the following text to create {num_cards} definition flashcards.

        Content: {text[:3000]}...

        Requirements:
        - Focus only on terms that have clear definitions in the text
        - Questions should be "What is [term]?" or "Define [term]"
        - Answers should be clear, concise definitions
        - Only include terms that are actually defined in the content

        Format as JSON array:
        [
            {{
                "question": "What is [term]?",
                "answer": "Definition of the term."
            }}
        ]
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self.parse_flashcard_response(response.text)
        except Exception as e:
            return []
    
    def generate_concept_flashcards(self, text: str, num_cards: int = 10) -> List[Dict[str, str]]:
        """Generate flashcards focused on conceptual understanding"""
        
        prompt = f"""
        Create {num_cards} flashcards that test conceptual understanding from this content.

        Content: {text[:3000]}...

        Focus on:
        - "How does..." questions
        - "Why is..." questions  
        - "What happens when..." questions
        - Process and relationship questions

        Format as JSON array with question and answer pairs.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self.parse_flashcard_response(response.text)
        except Exception as e:
            return []
    
    def organize_flashcards_by_topic(self, flashcards: List[Dict[str, str]], text: str) -> Dict[str, List[Dict[str, str]]]:
        """Organize flashcards by topic/category"""
        
        if not flashcards:
            return {}
        
        # Simple organization - this could be enhanced with more sophisticated categorization
        organized = {
            "Definitions": [],
            "Concepts": [],
            "Processes": [],
            "General": []
        }
        
        for card in flashcards:
            question = card['question'].lower()
            
            if any(word in question for word in ['what is', 'define', 'definition']):
                organized["Definitions"].append(card)
            elif any(word in question for word in ['how does', 'how do', 'process']):
                organized["Processes"].append(card)
            elif any(word in question for word in ['why', 'explain', 'concept']):
                organized["Concepts"].append(card)
            else:
                organized["General"].append(card)
        
        # Remove empty categories
        return {k: v for k, v in organized.items() if v}
    
    def export_flashcards(self, flashcards: List[Dict[str, str]], format_type: str = "text") -> str:
        """Export flashcards in different formats"""
        
        if format_type == "text":
            return self.export_as_text(flashcards)
        elif format_type == "csv":
            return self.export_as_csv(flashcards)
        elif format_type == "json":
            return json.dumps(flashcards, indent=2)
        else:
            return self.export_as_text(flashcards)
    
    def export_as_text(self, flashcards: List[Dict[str, str]]) -> str:
        """Export flashcards as plain text"""
        
        text = "# Flashcards\n\n"
        
        for i, card in enumerate(flashcards, 1):
            text += f"## Card {i}\n\n"
            text += f"**Question:** {card['question']}\n\n"
            text += f"**Answer:** {card['answer']}\n\n"
            text += "---\n\n"
        
        return text
    
    def export_as_csv(self, flashcards: List[Dict[str, str]]) -> str:
        """Export flashcards as CSV"""
        
        csv_content = "Question,Answer\n"
        
        for card in flashcards:
            # Escape quotes and commas
            question = card['question'].replace('"', '""')
            answer = card['answer'].replace('"', '""')
            csv_content += f'"{question}","{answer}"\n'
        
        return csv_content