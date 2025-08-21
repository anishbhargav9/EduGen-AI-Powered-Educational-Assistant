import os
import re
from pathlib import Path
from typing import List, Optional

import PyPDF2
from pptx import Presentation
from youtube_transcript_api import YouTubeTranscriptApi
import streamlit as st


class DocumentProcessor:
    """Handle processing of different document types"""
    
    def __init__(self):
        self.supported_formats = ['pdf', 'pptx', 'ppt', 'txt', 'youtube']
        
    def process_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    except Exception as e:
                        st.warning(f"Could not extract text from page {page_num + 1}: {str(e)}")
                        continue
                
                if not text.strip():
                    raise Exception("No text could be extracted from the PDF")
                    
                return self.clean_text(text)
                
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def process_ppt(self, file_path: str) -> str:
        """Extract text from PowerPoint file"""
        try:
            presentation = Presentation(file_path)
            text = ""
            
            for slide_num, slide in enumerate(presentation.slides):
                slide_text = f"\n--- Slide {slide_num + 1} ---\n"
                
                # Extract text from shapes
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        slide_text += shape.text + "\n"
                
                # Extract text from notes
                if slide.notes_slide.notes_text_frame:
                    notes_text = slide.notes_slide.notes_text_frame.text
                    if notes_text.strip():
                        slide_text += f"\nNotes: {notes_text}\n"
                
                text += slide_text
            
            if not text.strip():
                raise Exception("No text could be extracted from the PowerPoint")
                
            return self.clean_text(text)
            
        except Exception as e:
            raise Exception(f"Error processing PowerPoint: {str(e)}")
    
    def process_youtube(self, url: str) -> str:
        """Extract transcript from YouTube video"""
        try:
            # Extract video ID from URL
            video_id = self.extract_video_id(url)
            if not video_id:
                raise Exception("Invalid YouTube URL")
            
            # Try to get transcript
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                
                # Combine transcript text
                transcript_text = ""
                for entry in transcript_list:
                    transcript_text += entry['text'] + " "
                
                if not transcript_text.strip():
                    raise Exception("Empty transcript received")
                
                return self.clean_text(transcript_text)
                
            except Exception as transcript_error:
                # Try different languages if English fails
                try:
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    
                    # Get available transcripts
                    for transcript in transcript_list:
                        try:
                            transcript_data = transcript.fetch()
                            transcript_text = ""
                            for entry in transcript_data:
                                transcript_text += entry['text'] + " "
                            
                            if transcript_text.strip():
                                return self.clean_text(transcript_text)
                        except:
                            continue
                    
                    raise Exception("No readable transcript found")
                    
                except Exception as e:
                    raise Exception(f"Could not retrieve transcript: {str(e)}")
                    
        except Exception as e:
            raise Exception(f"Error processing YouTube video: {str(e)}")
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com.*[?&]v=([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def clean_text(self, text: str) -> str:
        """Clean and format extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)\[\]\"\'\/\@\#\$\%\&\*\+\=\|\\\{\}\~\`\^\<\>]', '', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks for better processing"""
        if not text:
            return []
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            
            # Break if we've covered all words
            if i + chunk_size >= len(words):
                break
        
        return chunks
    
    def get_document_info(self, file_path: str) -> dict:
        """Get basic information about the document"""
        file_path = Path(file_path)
        
        info = {
            'name': file_path.name,
            'size': file_path.stat().st_size,
            'extension': file_path.suffix.lower(),
            'type': self.get_file_type(file_path.suffix.lower())
        }
        
        return info
    
    def get_file_type(self, extension: str) -> str:
        """Determine file type from extension"""
        ext_map = {
            '.pdf': 'PDF Document',
            '.pptx': 'PowerPoint Presentation', 
            '.ppt': 'PowerPoint Presentation',
            '.txt': 'Text Document',
            '.md': 'Markdown Document'
        }
        
        return ext_map.get(extension, 'Unknown')
    
    def validate_file(self, file_path: str, max_size_mb: int = 50) -> bool:
        """Validate if file can be processed"""
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                return False
            
            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                return False
            
            # Check file extension
            if file_path.suffix.lower() not in ['.pdf', '.pptx', '.ppt', '.txt', '.md']:
                return False
                
            return True
            
        except Exception:
            return False