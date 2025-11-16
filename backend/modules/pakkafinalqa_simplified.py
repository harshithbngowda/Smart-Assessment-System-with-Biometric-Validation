"""
Simplified PakkaFinalQA Generator - Works without transformers/tensorflow
Uses NLTK and simple heuristics for question generation
"""

import os
import re
import random
from typing import List, Dict, Any
from collections import Counter

import pdfplumber
from docx import Document as DocxDocument
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt")
    nltk.data.find("taggers/averaged_perceptron_tagger")
except:
    nltk.download("punkt", quiet=True)
    nltk.download("averaged_perceptron_tagger", quiet=True)

print("✅ Simplified Q&A Generator loaded (NLTK-based)")

class PakkaFinalQAGenerator:
    def __init__(self):
        self.min_sentence_length = 10
        self.min_word_length = 3
        
    def process_document(self, file_path: str, mode: str = "auto", num_questions: int = 10) -> List[Dict[str, Any]]:
        """Process document and generate questions"""
        # Extract text
        text = self._extract_text(file_path)
        
        if not text or len(text) < 50:
            return self._generate_default_questions()
        
        # Generate questions
        questions = []
        
        # Determine mode if auto
        if mode == "auto":
            mode = self._detect_mode(text)
        
        # Generate different types of questions
        if num_questions >= 3:
            mcq_count = max(1, num_questions // 3)
            desc_count = max(1, num_questions // 3)
            prog_count = num_questions - mcq_count - desc_count
        else:
            mcq_count = 1
            desc_count = 1
            prog_count = max(0, num_questions - 2)
        
        # Generate MCQs
        mcqs = self._generate_mcq_questions(text, mcq_count)
        questions.extend(mcqs)
        
        # Generate descriptive questions
        desc_questions = self._generate_descriptive_questions(text, desc_count)
        questions.extend(desc_questions)
        
        # Generate programming questions if applicable
        if prog_count > 0 and ('python' in text.lower() or 'function' in text.lower() or 'code' in text.lower()):
            prog_questions = self._generate_programming_questions(text, prog_count)
            questions.extend(prog_questions)
        else:
            # Generate more descriptive instead
            extra_desc = self._generate_descriptive_questions(text, prog_count)
            questions.extend(extra_desc)
        
        return questions[:num_questions]
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF, DOCX, or TXT file"""
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.pdf':
                text = ""
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text.strip()
                
            elif ext == '.docx':
                doc = DocxDocument(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
                
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
                    
        except Exception as e:
            print(f"Error extracting text: {e}")
        
        return ""
    
    def _detect_mode(self, text: str) -> str:
        """Detect content type"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['python', 'javascript', 'function', 'code', 'algorithm']):
            return 'programming'
        elif any(keyword in text_lower for keyword in ['theorem', 'equation', 'calculate', 'formula']):
            return 'math'
        else:
            return 'descriptive'
    
    def _generate_mcq_questions(self, text: str, count: int) -> List[Dict[str, Any]]:
        """Generate multiple choice questions"""
        questions = []
        sentences = sent_tokenize(text)
        
        # Find important sentences (containing keywords or definitions)
        important_sentences = []
        for sent in sentences:
            if len(sent.split()) >= 5 and any(keyword in sent.lower() for keyword in ['is', 'are', 'means', 'refers', 'called', 'known', 'defined']):
                important_sentences.append(sent)
        
        if not important_sentences:
            important_sentences = [s for s in sentences if len(s.split()) >= 5]
        
        for i, sent in enumerate(important_sentences[:count]):
            words = word_tokenize(sent)
            tagged = pos_tag(words)
            
            # Find nouns or proper nouns
            key_words = [word for word, tag in tagged if tag in ['NN', 'NNP', 'NNS'] and len(word) > 3]
            
            if key_words:
                answer = key_words[0]
                question_text = sent.replace(answer, "________")
                
                # Generate distractors
                all_nouns = [word for word, tag in pos_tag(word_tokenize(text)) if tag in ['NN', 'NNP'] and len(word) > 3]
                distractors = [w for w in set(all_nouns) if w != answer][:3]
                
                if len(distractors) < 3:
                    distractors.extend(["Option A", "Option B", "Option C"])
                distractors = distractors[:3]
                
                options = [answer] + distractors
                random.shuffle(options)
                
                questions.append({
                    'question': f"Fill in the blank: {question_text}",
                    'type': 'mcq',
                    'answer': answer,
                    'options': options
                })
        
        return questions
    
    def _generate_descriptive_questions(self, text: str, count: int) -> List[Dict[str, Any]]:
        """Generate descriptive questions"""
        questions = []
        sentences = sent_tokenize(text)
        
        # Find topic sentences
        topic_sentences = []
        for sent in sentences:
            if len(sent.split()) >= 6:
                words_lower = sent.lower()
                if any(keyword in words_lower for keyword in ['explain', 'describe', 'discuss', 'important', 'main', 'key', 'essential']):
                    topic_sentences.append(sent)
        
        if not topic_sentences:
            topic_sentences = [s for s in sentences if len(s.split()) >= 8]
        
        question_starters = [
            "Explain",
            "Describe",
            "What are the main points about",
            "Discuss",
            "How does",
            "What is the significance of"
        ]
        
        for i, sent in enumerate(topic_sentences[:count]):
            # Extract main topic
            words = word_tokenize(sent)
            tagged = pos_tag(words)
            topics = [word for word, tag in tagged if tag in ['NN', 'NNP', 'VBG'] and len(word) > 3]
            
            if topics:
                topic = topics[0]
                starter = random.choice(question_starters)
                
                if starter in ['Explain', 'Describe', 'Discuss']:
                    question_text = f"{starter} {topic} in detail."
                else:
                    question_text = f"{starter} {topic}?"
                
                questions.append({
                    'question': question_text,
                    'type': 'descriptive',
                    'answer': sent,
                    'options': []
                })
        
        return questions
    
    def _generate_programming_questions(self, text: str, count: int) -> List[Dict[str, Any]]:
        """Generate programming questions"""
        questions = []
        
        # Find sentences with programming keywords
        sentences = sent_tokenize(text)
        prog_sentences = [s for s in sentences if any(kw in s.lower() for kw in ['function', 'method', 'class', 'loop', 'variable', 'array', 'list'])]
        
        if not prog_sentences:
            return []
        
        for i, sent in enumerate(prog_sentences[:count]):
            words = word_tokenize(sent)
            tagged = pos_tag(words)
            
            # Find programming concepts
            concepts = [word for word, tag in tagged if tag in ['NN', 'NNP', 'VB'] and len(word) > 3]
            
            if concepts:
                concept = concepts[0]
                questions.append({
                    'question': f"Write a Python program to demonstrate {concept}.",
                    'type': 'programming',
                    'answer': f"# Sample program for {concept}\n# Students should write complete code here",
                    'options': []
                })
        
        return questions
    
    def _generate_default_questions(self) -> List[Dict[str, Any]]:
        """Generate default questions when text extraction fails"""
        return [
            {
                'question': "What are the main topics covered in this document?",
                'type': 'descriptive',
                'answer': "Please summarize the main points from the document.",
                'options': []
            },
            {
                'question': "Explain the key concepts discussed.",
                'type': 'descriptive',
                'answer': "Provide a detailed explanation of the key concepts.",
                'options': []
            }
        ]
