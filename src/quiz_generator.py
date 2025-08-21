import google.generativeai as genai
import json
import re
import random
from typing import List, Dict, Any
import os
from config import GOOGLE_API_KEY, GEMINI_MODEL

class QuizGenerator:
    """Generate various types of quizzes from text content"""
    
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        
    def generate_quiz(self, text: str, settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate a quiz based on the provided text and settings"""
        
        difficulty = settings.get('difficulty', 'Medium')
        num_questions = settings.get('num_questions', 15)
        question_types = settings.get('question_types', ['Multiple Choice', 'True/False'])
        
        quiz_questions = []
        questions_per_type = max(1, num_questions // len(question_types))
        
        for question_type in question_types:
            if question_type == 'Multiple Choice':
                questions = self.generate_mcq(text, questions_per_type, difficulty)
                quiz_questions.extend(questions)
            elif question_type == 'True/False':
                questions = self.generate_true_false(text, questions_per_type, difficulty)
                quiz_questions.extend(questions)
            elif question_type == 'Short Answer':
                questions = self.generate_short_answer(text, questions_per_type, difficulty)
                quiz_questions.extend(questions)
        
        # Shuffle questions and trim to exact number requested
        random.shuffle(quiz_questions)
        return quiz_questions[:num_questions]
    
    def generate_mcq(self, text: str, num_questions: int, difficulty: str) -> List[Dict[str, Any]]:
        """Generate multiple choice questions"""
        
        prompt = f"""
        Based on the following text, generate {num_questions} multiple choice questions at {difficulty} difficulty level.

        Text: {text[:3000]}...

        Requirements:
        - Each question should have exactly 4 options (A, B, C, D)
        - Only one correct answer per question
        - Include explanations for the correct answers
        - Questions should test understanding, not just memorization
        - For {difficulty} difficulty: {"Focus on basic concepts and definitions" if difficulty == "Easy" else "Include analysis and application" if difficulty == "Medium" else "Require synthesis and critical thinking"}

        Format your response as a JSON array with this structure:
        [
            {{
                "question": "Question text here?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Option A",
                "explanation": "Explanation of why this is correct",
                "type": "multiple_choice"
            }}
        ]

        Return only the JSON array, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            questions = self.parse_json_response(response.text, 'mcq')
            return questions[:num_questions]
        except Exception as e:
            # Fallback questions if API fails
            return self.create_fallback_mcq(text, num_questions)
    
    def generate_true_false(self, text: str, num_questions: int, difficulty: str) -> List[Dict[str, Any]]:
        """Generate true/false questions"""
        
        prompt = f"""
        Based on the following text, generate {num_questions} true/false questions at {difficulty} difficulty level.

        Text: {text[:3000]}...

        Requirements:
        - Mix of true and false statements (roughly 50/50)
        - Include explanations for each answer
        - For {difficulty} difficulty: {"Focus on straightforward facts" if difficulty == "Easy" else "Include some interpretation" if difficulty == "Medium" else "Require careful analysis"}
        - Avoid trick questions or overly obvious answers

        Format your response as a JSON array with this structure:
        [
            {{
                "question": "Statement to evaluate",
                "correct_answer": "True",
                "explanation": "Explanation of why this is true/false",
                "type": "true_false"
            }}
        ]

        Return only the JSON array, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            questions = self.parse_json_response(response.text, 'true_false')
            return questions[:num_questions]
        except Exception as e:
            return self.create_fallback_true_false(text, num_questions)
    
    def generate_short_answer(self, text: str, num_questions: int, difficulty: str) -> List[Dict[str, Any]]:
        """Generate short answer questions"""
        
        prompt = f"""
        Based on the following text, generate {num_questions} short answer questions at {difficulty} difficulty level.

        Text: {text[:3000]}...

        Requirements:
        - Questions should require 1-3 sentence answers
        - Include sample correct answers
        - For {difficulty} difficulty: {"Ask for definitions and basic explanations" if difficulty == "Easy" else "Ask for explanations and examples" if difficulty == "Medium" else "Ask for analysis and synthesis"}

        Format your response as a JSON array with this structure:
        [
            {{
                "question": "Question requiring short answer?",
                "correct_answer": "Sample correct answer",
                "explanation": "Additional context or alternative answers",
                "type": "short_answer"
            }}
        ]

        Return only the JSON array, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            questions = self.parse_json_response(response.text, 'short_answer')
            return questions[:num_questions]
        except Exception as e:
            return self.create_fallback_short_answer(text, num_questions)
    
    def parse_json_response(self, response_text: str, question_type: str) -> List[Dict[str, Any]]:
        """Parse JSON response from the AI model"""
        try:
            # Clean the response text
            cleaned_text = self.clean_json_response(response_text)
            
            # Parse JSON
            questions = json.loads(cleaned_text)
            
            # Validate and format questions
            formatted_questions = []
            for q in questions:
                if self.validate_question(q, question_type):
                    formatted_questions.append(q)
            
            return formatted_questions
            
        except json.JSONDecodeError as e:
            # Try to extract JSON from the response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                try:
                    questions = json.loads(json_match.group())
                    return [q for q in questions if self.validate_question(q, question_type)]
                except:
                    pass
            
            # If all else fails, return empty list
            return []
    
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
    
    def validate_question(self, question: Dict[str, Any], question_type: str) -> bool:
        """Validate question structure"""
        required_fields = ['question', 'correct_answer', 'type']
        
        # Check basic fields
        for field in required_fields:
            if field not in question:
                return False
        
        # Type-specific validation
        if question_type == 'multiple_choice':
            if 'options' not in question or len(question['options']) != 4:
                return False
        
        return True
    
    def create_fallback_mcq(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """Create fallback MCQ questions if AI generation fails"""
        # Extract key sentences from text for questions
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20][:num_questions]
        
        questions = []
        for i, sentence in enumerate(sentences):
            question = {
                "question": f"Based on the content, which statement is most accurate regarding the topic discussed?",
                "options": [
                    "Option A: Analysis pending",
                    "Option B: Content review needed", 
                    "Option C: Information being processed",
                    "Option D: Please regenerate quiz"
                ],
                "correct_answer": "Option D: Please regenerate quiz",
                "explanation": "This is a fallback question. Please try generating the quiz again.",
                "type": "multiple_choice"
            }
            questions.append(question)
        
        return questions
    
    def create_fallback_true_false(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """Create fallback True/False questions"""
        questions = []
        for i in range(num_questions):
            question = {
                "question": "The content contains important educational information.",
                "correct_answer": "True",
                "explanation": "This is a fallback question. Please try generating the quiz again.",
                "type": "true_false"
            }
            questions.append(question)
        
        return questions
    
    def create_fallback_short_answer(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """Create fallback short answer questions"""
        questions = []
        for i in range(num_questions):
            question = {
                "question": "What are the main topics covered in this material?",
                "correct_answer": "Please regenerate the quiz for specific answers.",
                "explanation": "This is a fallback question generated due to processing issues.",
                "type": "short_answer"
            }
            questions.append(question)
        
        return questions
    
    def get_quiz_statistics(self, quiz_data: List[Dict[str, Any]], user_answers: Dict[int, str]) -> Dict[str, Any]:
        """Calculate quiz statistics"""
        total_questions = len(quiz_data)
        answered_questions = len(user_answers)
        correct_answers = 0
        
        for i, question in enumerate(quiz_data):
            if i in user_answers:
                user_answer = user_answers[i]
                correct_answer = question['correct_answer']
                
                if question['type'] in ['multiple_choice', 'true_false']:
                    if user_answer == correct_answer:
                        correct_answers += 1
                elif question['type'] == 'short_answer':
                    # Simple keyword matching for short answers
                    if correct_answer.lower() in user_answer.lower():
                        correct_answers += 1
        
        score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        return {
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'correct_answers': correct_answers,
            'score_percentage': score_percentage,
            'completion_rate': (answered_questions / total_questions * 100) if total_questions > 0 else 0
        }