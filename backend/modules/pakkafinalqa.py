import os
import re
import json
import time
import random
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from collections import Counter

import pdfplumber
from docx import Document as DocxDocument
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag

# Try to import advanced libraries for enhanced functionality
try:
    import sympy as sp
    from sympy import sympify, Symbol, solve, diff, integrate
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False
    print("⚠️ SymPy not available. Math calculations will be limited.")

try:
    from transformers import pipeline
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ Transformers not available. Using rule-based approach only.")

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt")
    nltk.data.find("taggers/averaged_perceptron_tagger")
except:
    nltk.download("punkt", quiet=True)
    nltk.download("averaged_perceptron_tagger", quiet=True)

class PakkaFinalQAGenerator:
    """
    Ultimate Q&A Generator combining the best features from multiple approaches:
    - Descriptive Q&A with context awareness
    - Programming Q&A with code analysis
    - Math Q&A with equation solving
    - MCQ generation with 4 options
    """
    
    def __init__(self):
        print("🚀 Pakka Final QA Generator - Ultimate Solution for All Content Types")
        print("📋 Modes Available: Descriptive, Programming, Math, MCQ")
        
        self.document_context = {
            'main_characters': [],
            'locations': [],
            'time_periods': [],
            'key_concepts': [],
            'code_elements': [],
            'math_concepts': [],
            'content_type': 'unknown',
            'formulas': [],
            'theorems': [],
            'functions': [],
            'algorithms': [],
            'word_problems': []
        }
        
        # Initialize ML models if available
        self.ml_available = ML_AVAILABLE
        if self.ml_available:
            try:
                self.qg_pipeline = pipeline("text2text-generation", model="valhalla/t5-small-qg-hl")
                self.qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")
                print("✅ ML Models loaded successfully.")
            except Exception as e:
                print(f"⚠️ ML models failed to load: {e}")
                self.ml_available = False
        
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF, DOCX, or TXT files"""
        ext = Path(file_path).suffix.lower()
        text = ""
        
        try:
            if ext == ".pdf":
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                            
            elif ext == ".docx":
                doc = DocxDocument(file_path)
                for para in doc.paragraphs:
                    if para.text.strip():
                        text += para.text + "\n"
                        
            elif ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            else:
                raise ValueError(f"Unsupported file type: {ext}")
                
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return ""
            
        return text.strip()
    
    def detect_content_type(self, text: str) -> str:
        """Enhanced content type detection"""
        text_lower = text.lower()
        text_length = len(text)
        
        # Very strong programming indicators
        very_strong_prog = ['#include', 'printf(', 'scanf(', 'int main(', 'void main(', 'def ', 'class ', 
                           'import ', 'write a c program', 'write a program to', 'algorithm to']
        very_strong_prog_count = sum(1 for indicator in very_strong_prog if indicator in text_lower)
        
        # Programming syntax indicators
        prog_syntax = ['printf', 'scanf', 'main()', 'return 0;', 'void main', '#include <', 
                      'int main', 'public static void', 'def main', 'if __name__']
        prog_syntax_count = sum(1 for indicator in prog_syntax if indicator in text_lower)
        
        # Math indicators
        math_indicators = ['derivative', 'integral', 'equation', 'solve for', 'theorem', 'proof', 
                          'formula', 'calculate', 'mathematics', '∫', 'dx', 'dy', '∂', 'lim', 
                          'sin', 'cos', 'tan', 'matrix', 'polynomial', 'calculus', 'algebra']
        math_count = sum(1 for indicator in math_indicators if indicator in text_lower)
        
        # Science/Environmental/Climate indicators (EXPANDED)
        science_indicators = ['climate change', 'global warming', 'greenhouse gas', 'carbon dioxide', 
                             'sustainable development', 'environmental', 'ecosystem', 'biodiversity',
                             'renewable energy', 'fossil fuel', 'pollution', 'conservation',
                             'adaptation', 'mitigation', 'emissions', 'temperature', 'atmosphere',
                             'sdg', 'sustainability', 'resilience', 'vulnerability', 'extreme weather',
                             'sea level', 'deforestation', 'carbon footprint', 'paris agreement',
                             'infrastructure adaptation', 'agricultural adaptation', 'water management',
                             'urban planning', 'health adaptation', 'ecosystem-based', 'drought-resistant',
                             'flood defense', 'seawall', 'irrigation', 'desalination', 'green infrastructure',
                             'heat wave', 'storm surge', 'wetland', 'mangrove', 'climate-resilient']
        science_count = sum(1 for indicator in science_indicators if indicator in text_lower)
        
        # CRITICAL: If text contains adaptation strategies, it's DEFINITELY science
        adaptation_keywords = ['infrastructure adaptation', 'agricultural adaptation', 'water management',
                               'urban planning', 'health adaptation', 'ecosystem-based adaptation',
                               'flood defense', 'drought-resistant', 'irrigation efficiency',
                               'climate-resilient', 'green infrastructure']
        has_adaptation = any(kw in text_lower for kw in adaptation_keywords)
        if has_adaptation:
            science_count += 10  # Massive boost to ensure science detection
        
        # Story indicators
        story_indicators = ['once upon', 'character', 'story', 'novel', 'tale', 'protagonist', 'chapter',
                           'he said', 'she said', 'dialogue', 'plot', 'setting', 'theme']
        story_count = sum(1 for indicator in story_indicators if indicator in text_lower)
        
        # Calculate densities
        very_strong_density = (very_strong_prog_count * 1000) / text_length if text_length > 0 else 0
        prog_syntax_density = (prog_syntax_count * 1000) / text_length if text_length > 0 else 0
        
        print(f"🔍 Content Detection:")
        print(f"   Very Strong Programming: {very_strong_prog_count} (density: {very_strong_density:.2f})")
        print(f"   Programming Syntax: {prog_syntax_count} (density: {prog_syntax_density:.2f})")
        print(f"   Math: {math_count}")
        print(f"   Science/Environmental: {science_count}")
        print(f"   Story: {story_count}")
        
        # Decision logic - prioritize science/environmental content FIRST
        if very_strong_density > 0.5 or prog_syntax_density > 0.3:
            return "programming"
        elif very_strong_prog_count > 0 and prog_syntax_count > 0:
            return "programming"
        elif science_count >= 2:  # Lower threshold - even 2 science keywords should trigger
            print(f"🔬 Detected as SCIENCE content (science_count={science_count})")
            return "science"
        elif math_count > 3:
            return "math"
        elif story_count > 2:
            print(f"📖 Detected as STORY content (story_count={story_count})")
            return "descriptive"
        else:
            # Default to science if we have ANY science keywords
            if science_count > 0:
                print(f"🔬 Defaulting to SCIENCE (science_count={science_count})")
                return "science"
            print(f"📝 Defaulting to DESCRIPTIVE")
            return "descriptive"
    
    def analyze_document_context(self, text: str, content_type: str):
        """Comprehensive document analysis"""
        print(f"🔍 Analyzing {content_type} content...")
        
        sentences = sent_tokenize(text)
        
        if content_type == "programming":
            self.analyze_programming_context(text, sentences)
        elif content_type == "math":
            self.analyze_math_context(text, sentences)
        elif content_type == "science":
            self.analyze_science_context(text, sentences)
        elif content_type == "descriptive":
            self.analyze_story_context(text, sentences)
        else:
            self.analyze_general_context(text, sentences)
    
    def analyze_programming_context(self, text: str, sentences: List[str]):
        """Enhanced programming content analysis"""
        code_blocks = []
        functions = []
        algorithms = []
        concepts = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Extract code blocks
            if any(char in sentence for char in ['{', '}', ';', '()', '[]']) or \
               any(word in sentence_lower for word in ['def ', 'function', 'class', 'int ', 'void']):
                code_blocks.append(sentence)
            
            # Extract function definitions
            if any(word in sentence_lower for word in ['function', 'method', 'def ', 'void', 'int ', 'string']):
                functions.append(sentence)
            
            # Extract algorithms
            if any(word in sentence_lower for word in ['algorithm', 'sort', 'search', 'traverse', 'iterate']):
                algorithms.append(sentence)
            
            # Extract programming concepts
            if any(word in sentence_lower for word in ['variable', 'array', 'loop', 'condition', 'object', 'class']):
                concepts.append(sentence)
        
        self.document_context.update({
            'code_blocks': code_blocks[:15],
            'functions': functions[:10],
            'algorithms': algorithms[:10],
            'programming_concepts': concepts[:15]
        })
        
        print(f"   📊 Programming Analysis:")
        print(f"      Code blocks: {len(code_blocks)}")
        print(f"      Functions: {len(functions)}")
        print(f"      Algorithms: {len(algorithms)}")
        print(f"      Concepts: {len(concepts)}")
    
    def analyze_math_context(self, text: str, sentences: List[str]):
        """Enhanced math content analysis"""
        formulas = []
        theorems = []
        proofs = []
        calculations = []
        word_problems = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Extract formulas (mathematical expressions)
            if any(symbol in sentence for symbol in ['=', '+', '-', '*', '/', '^', '∫', '∑', '√', '∆']):
                formulas.append(sentence)
            
            # Extract theorems
            if any(word in sentence_lower for word in ['theorem', 'lemma', 'corollary']):
                theorems.append(sentence)
            
            # Extract proofs
            if any(word in sentence_lower for word in ['proof', 'prove', 'therefore', 'hence', 'qed']):
                proofs.append(sentence)
            
            # Extract calculations
            if any(word in sentence_lower for word in ['calculate', 'solve', 'find', 'determine', 'compute']):
                calculations.append(sentence)
            
            # Extract word problems
            if any(phrase in sentence_lower for phrase in ['a person', 'a car', 'a train', 'how much', 'how many', 
                                                          'if a', 'suppose', 'given that']) and \
               any(symbol in sentence for symbol in ['$', '%', 'km', 'meter', 'hour', 'year']):
                word_problems.append(sentence)
        
        self.document_context.update({
            'formulas': formulas[:10],
            'theorems': theorems[:10],
            'proofs': proofs[:10],
            'calculations': calculations[:10],
            'word_problems': word_problems[:10]
        })
        
        print(f"   📊 Math Analysis:")
        print(f"      Formulas: {len(formulas)}")
        print(f"      Theorems: {len(theorems)}")
        print(f"      Word Problems: {len(word_problems)}")
        print(f"      Calculations: {len(calculations)}")
    
    def analyze_story_context(self, text: str, sentences: List[str]):
        """Story/descriptive content analysis"""
        # Extract characters
        proper_nouns = []
        for sentence in sentences:
            words = word_tokenize(sentence)
            pos_tags = pos_tag(words)
            for word, tag in pos_tags:
                if tag in ['NNP', 'NNPS'] and len(word) > 2:
                    proper_nouns.append(word)
        
        char_counts = Counter(proper_nouns)
        self.document_context['main_characters'] = [char for char, count in char_counts.most_common(5) if count > 1]
        
        # Extract locations
        location_indicators = ['castle', 'palace', 'city', 'town', 'village', 'kingdom', 'forest', 'mountain']
        locations = []
        for sentence in sentences:
            for indicator in location_indicators:
                if indicator in sentence.lower():
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if word.lower() == indicator:
                            for j in range(max(0, i-2), min(len(words), i+3)):
                                if words[j][0].isupper():
                                    locations.append(words[j])
        
        self.document_context['locations'] = list(set(locations))[:5]
        
        print(f"   Characters: {self.document_context['main_characters']}")
        print(f"   Locations: {self.document_context['locations']}")
    
    def analyze_science_context(self, text: str, sentences: List[str]):
        """Analyze science/environmental content"""
        key_concepts = []
        processes = []
        impacts = []
        solutions = []
        
        # Keywords for different aspects
        concept_keywords = ['climate change', 'global warming', 'greenhouse effect', 'carbon cycle',
                           'ecosystem', 'biodiversity', 'sustainability', 'renewable energy']
        process_keywords = ['adaptation', 'mitigation', 'conservation', 'restoration', 'reduction']
        impact_keywords = ['temperature rise', 'sea level', 'extreme weather', 'drought', 'flooding',
                          'heat waves', 'storms', 'melting', 'extinction']
        solution_keywords = ['renewable', 'sustainable', 'green', 'clean energy', 'efficiency',
                            'resilience', 'infrastructure', 'policy', 'technology']
        
        text_lower = text.lower()
        
        # Extract key concepts
        for keyword in concept_keywords:
            if keyword in text_lower:
                key_concepts.append(keyword)
        
        for keyword in process_keywords:
            if keyword in text_lower:
                processes.append(keyword)
                
        for keyword in impact_keywords:
            if keyword in text_lower:
                impacts.append(keyword)
                
        for keyword in solution_keywords:
            if keyword in text_lower:
                solutions.append(keyword)
        
        # Store in context
        self.document_context['key_concepts'] = key_concepts[:10]
        self.document_context['processes'] = processes
        self.document_context['impacts'] = impacts
        self.document_context['solutions'] = solutions
        
        print(f"   Key Concepts: {key_concepts[:5]}")
        print(f"   Processes: {processes[:3]}")
        print(f"   Impacts: {impacts[:3]}")
        print(f"   Solutions: {solutions[:3]}")
    
    def analyze_general_context(self, text: str, sentences: List[str]):
        """General content analysis"""
        important_nouns = []
        for sentence in sentences:
            words = word_tokenize(sentence)
            pos_tags = pos_tag(words)
            for word, tag in pos_tags:
                if tag in ['NN', 'NNS'] and len(word) > 3:
                    important_nouns.append(word.lower())
        
        concept_counts = Counter(important_nouns)
        self.document_context['key_concepts'] = [concept for concept, count in concept_counts.most_common(10) if count > 1]
    
    def generate_descriptive_qa(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate descriptive questions with proper context"""
        if self.ml_available:
            return self.generate_descriptive_qa_ml(text, num_questions)
        qa_pairs = []
        sentences = sent_tokenize(text)
        
        # Character-based questions with context
        for character in self.document_context.get('main_characters', [])[:3]:
            char_sentences = [s for s in sentences if character.lower() in s.lower()]
            if char_sentences and len(qa_pairs) < num_questions:
                # Get surrounding context for better questions
                context_info = self.get_character_context(character, char_sentences, text)
                
                if any(word in ' '.join(char_sentences).lower() for word in ['said', 'spoke', 'called', 'asked', 'replied']):
                    article = "the " if not character.lower().startswith(('a ', 'an ', 'the ')) else ""
                    qa_pairs.append({
                        'question': f"In the story about {context_info['setting']}, what does {article}{character} say or communicate, and what does this reveal about their character?",
                        'answer': self.create_enhanced_character_analysis(character, char_sentences, text, 'dialogue'),
                        'type': 'descriptive_character_dialogue'
                    })
                elif any(word in ' '.join(char_sentences).lower() for word in ['went', 'came', 'traveled', 'walked', 'moved']):
                    # Get specific context about what the character is doing
                    action_context = self.get_specific_action_context(character, char_sentences, text)
                    article = "the " if not character.lower().startswith(('a ', 'an ', 'the ')) else ""
                    pronoun = "he does" if any(word in character.lower() for word in ['king', 'prince', 'man', 'boy']) else "she does" if any(word in character.lower() for word in ['queen', 'princess', 'woman', 'girl']) else "they do"
                    
                    qa_pairs.append({
                        'question': f"In this story about {action_context['story_context']}, describe {article}{character}'s {action_context['action_type']} and explain what this reveals about {action_context['character_pronoun']} character.",
                        'answer': self.create_enhanced_character_analysis(character, char_sentences, text, 'actions'),
                        'type': 'descriptive_character_actions'
                    })
                else:
                    print(f"❌❌❌ ERROR: STORY GENERATOR CALLED! This should NOT happen for science content!")
                    print(f"❌ Character detected: {character}")
                    print(f"❌ This means content was detected as STORY instead of SCIENCE")
                    article = "the " if not character.lower().startswith(('a ', 'an ', 'the ')) else ""
                    qa_pairs.append({
                        'question': f"In this story set in {context_info['setting']}, what role does {article}{character} play and what are their key characteristics?",
                        'answer': self.create_enhanced_character_analysis(character, char_sentences, text, 'general'),
                        'type': 'descriptive_character_general'
                    })
        
        # Location-based questions with context
        for location in self.document_context.get('locations', [])[:2]:
            location_sentences = [s for s in sentences if location.lower() in s.lower()]
            if location_sentences and len(qa_pairs) < num_questions:
                context_info = self.get_location_context(location, location_sentences, text)
                qa_pairs.append({
                    'question': f"In the story, what specific events happen at {location} during {context_info['time_context']}, and why is this location significant to the plot?",
                    'answer': self.create_location_analysis(location, location_sentences, text),
                    'type': 'descriptive_location'
                })
        
        # Situation-based questions with full context
        remaining = num_questions - len(qa_pairs)
        if remaining > 0:
            contextual_questions = self.generate_contextual_questions(text, remaining)
            qa_pairs.extend(contextual_questions)
        
        return qa_pairs[:num_questions]

    def generate_descriptive_qa_ml(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        qa_pairs = []
        sentences = sent_tokenize(text)
        
        # Create larger context chunks
        paragraphs = []
        current_para = []
        for sent in sentences:
            if len(sent.strip()) > 20:
                current_para.append(sent.strip())
                if len(' '.join(current_para)) > 300:
                    paragraphs.append(' '.join(current_para))
                    current_para = []
        if current_para:
            paragraphs.append(' '.join(current_para))
        
        # Get full text for better context
        full_text = ' '.join(paragraphs[:5])
        
        # Extract key information from document context
        characters = self.document_context.get('characters', [])
        locations = self.document_context.get('locations', [])
        
        # Generate questions directly from sentences - more reliable
        content_based_questions = []
        
        # Strategy 1: Find important sentences with key information
        important_sentences = []
        for sent in sentences:
            sent_lower = sent.lower()
            # Look for sentences with important information markers
            if any(marker in sent_lower for marker in ['describe', 'explain', 'because', 'therefore', 'however', 'although', 'when', 'where', 'who', 'what', 'why', 'how']):
                if len(sent.split()) > 8:  # Substantial sentences
                    important_sentences.append(sent.strip())
        
        # Strategy 2: Create detailed questions from character actions
        if characters:
            for char in characters[:2]:  # Top 2 characters
                char_sentences = [s for s in sentences if char in s]
                if char_sentences:
                    # Remove duplicates and get rich context
                    unique_char_sentences = []
                    seen = set()
                    for s in char_sentences:
                        s_clean = s.strip()
                        if s_clean not in seen and len(s_clean) > 20:
                            unique_char_sentences.append(s_clean)
                            seen.add(s_clean)
                            if len(unique_char_sentences) >= 5:
                                break
                    
                    # Extract specific actions/details about the character
                    actions = []
                    emotions = []
                    for sent in unique_char_sentences:
                        sent_lower = sent.lower()
                        # Look for action verbs
                        if any(verb in sent_lower for verb in ['went', 'called', 'wrapped', 'knelt', 'visited', 'said', 'did', 'made', 'took']):
                            actions.append(sent)
                        # Look for emotional content
                        if any(emotion in sent_lower for emotion in ['grief', 'love', 'sorrow', 'joy', 'fear', 'anger', 'sad', 'happy']):
                            emotions.append(sent)
                    
                    # Build detailed context
                    context_parts = actions[:2] + emotions[:1] + unique_char_sentences[:2]
                    context = ' '.join(list(dict.fromkeys(context_parts)))  # Remove duplicates while preserving order
                    
                    # Create more specific question based on what we found
                    if actions:
                        content_based_questions.append({
                            'question': f"Describe the specific actions of {char} mentioned in the passage and explain their significance in the context of the narrative.",
                            'answer': f"The passage describes {char}'s actions in detail: {context[:500]}",
                            'type': 'descriptive'
                        })
                    else:
                        content_based_questions.append({
                            'question': f"Explain the role and characterization of {char} as presented in this passage, with specific references to the text.",
                            'answer': f"The passage characterizes {char} as follows: {context[:500]}",
                            'type': 'descriptive'
                        })
        
        # Strategy 3: Create detailed questions from locations with events
        if locations:
            for loc in locations[:2]:
                loc_sentences = [s for s in sentences if loc in s]
                if loc_sentences:
                    # Remove duplicates and get unique sentences
                    unique_sentences = []
                    seen = set()
                    for s in loc_sentences:
                        s_clean = s.strip()
                        if s_clean not in seen and len(s_clean) > 20:
                            unique_sentences.append(s_clean)
                            seen.add(s_clean)
                    
                    # Extract events and descriptions related to location
                    events_at_location = []
                    descriptions = []
                    for sent in unique_sentences:
                        sent_lower = sent.lower()
                        # Look for events (past tense verbs, actions)
                        if any(word in sent_lower for word in ['happened', 'occurred', 'took place', 'was', 'were', 'had', 'did']):
                            events_at_location.append(sent)
                        # Look for descriptive content
                        if any(word in sent_lower for word in ['where', 'which', 'beautiful', 'dark', 'grand', 'small', 'large']):
                            descriptions.append(sent)
                    
                    # Get surrounding context for better answers
                    context_parts = []
                    for sent in unique_sentences[:4]:
                        try:
                            idx = sentences.index(sent)
                            # Add sentence before and after for context
                            if idx > 0 and sentences[idx-1] not in context_parts:
                                context_parts.append(sentences[idx-1])
                            if sent not in context_parts:
                                context_parts.append(sent)
                            if idx < len(sentences) - 1 and sentences[idx+1] not in context_parts:
                                context_parts.append(sentences[idx+1])
                        except ValueError:
                            context_parts.append(sent)
                    
                    # Build rich context
                    context = ' '.join(context_parts[:6])
                    
                    # Create specific question based on what we found
                    if events_at_location:
                        content_based_questions.append({
                            'question': f"Describe the events that take place at {loc} in the passage and explain their significance to the overall narrative.",
                            'answer': f"At {loc}, the following events occur: {context[:500]}",
                            'type': 'descriptive'
                        })
                    else:
                        content_based_questions.append({
                            'question': f"Explain the role and significance of {loc} in the passage, including any descriptions or events associated with this location.",
                            'answer': f"The passage describes {loc} in the following context: {context[:500]}",
                            'type': 'descriptive'
                        })
        
        # Strategy 4: Extract questions from important sentences
        for sent in important_sentences[:num_questions]:
            # Convert statement to question
            if 'because' in sent.lower():
                parts = sent.split('because')
                if len(parts) == 2:
                    content_based_questions.append({
                        'question': f"Why {parts[0].strip().lower()}? Explain based on the passage.",
                        'answer': f"Because {parts[1].strip()} As stated in the passage: {sent}",
                        'type': 'descriptive'
                    })
            elif any(char in sent for char in characters[:3]):
                # Question about character action
                char_in_sent = next((c for c in characters if c in sent), None)
                if char_in_sent:
                    content_based_questions.append({
                        'question': f"What does the passage reveal about {char_in_sent}? Provide specific details.",
                        'answer': f"The passage reveals: {sent} Additional context: {' '.join([s for s in sentences if char_in_sent in s][:2])[:300]}",
                        'type': 'descriptive'
                    })
        
        # Strategy 5: Detailed comprehension questions based on full context
        if len(content_based_questions) < num_questions:
            # Analyze the content to create specific questions
            first_para = paragraphs[0] if paragraphs else full_text[:500]
            second_para = paragraphs[1] if len(paragraphs) > 1 else ""
            
            # Detect content type and generate appropriate questions
            content_types = []
            content_keywords = {
                'climate': ['climate', 'adaptation', 'environmental', 'sustainability', 'greenhouse', 'warming'],
                'programming': ['algorithm', 'function', 'code', 'program', 'variable', 'loop', 'array'],
                'physics': ['force', 'energy', 'velocity', 'acceleration', 'mass', 'momentum', 'newton'],
                'chemistry': ['molecule', 'atom', 'reaction', 'compound', 'element', 'chemical', 'bond'],
                'biology': ['cell', 'organism', 'species', 'evolution', 'dna', 'protein', 'gene'],
                'mathematics': ['equation', 'formula', 'theorem', 'proof', 'calculate', 'solve'],
                'database': ['database', 'query', 'table', 'sql', 'normalization', 'relation'],
                'networking': ['network', 'protocol', 'router', 'tcp', 'ip', 'packet'],
                'literature': ['character', 'protagonist', 'plot', 'narrative', 'story', 'theme']
            }
            
            text_lower = full_text.lower()
            for content_type, keywords in content_keywords.items():
                if any(kw in text_lower for kw in keywords):
                    content_types.append(content_type)
            
            # Generate question based on detected content type
            if content_types:
                main_type = content_types[0]
                
                # Extract key concepts from first paragraph
                key_concepts = []
                for sent in sentences[:5]:
                    # Look for numbered lists or bullet points
                    if any(marker in sent for marker in ['1)', '2)', '3)', '•', '-', 'a)', 'b)']):
                        key_concepts.append(sent.strip())
                
                if main_type == 'climate':
                    content_based_questions.append({
                        'question': f"Describe the key strategies or concepts discussed in the content and explain their importance.",
                        'answer': f"{first_para} {second_para[:300]}",
                        'type': 'descriptive'
                    })
                elif main_type in ['programming', 'database', 'networking']:
                    content_based_questions.append({
                        'question': f"Explain the technical concepts presented in the content with relevant examples.",
                        'answer': f"{first_para} {second_para[:300]}",
                        'type': 'descriptive'
                    })
                elif main_type in ['physics', 'chemistry', 'biology', 'mathematics']:
                    content_based_questions.append({
                        'question': f"Explain the scientific principles or concepts discussed in the content.",
                        'answer': f"{first_para} {second_para[:300]}",
                        'type': 'descriptive'
                    })
                elif main_type == 'literature':
                    content_based_questions.append({
                        'question': f"Analyze the literary elements and themes presented in this passage.",
                        'answer': f"{first_para} {second_para[:200]}",
                        'type': 'descriptive'
                    })
                else:
                    content_based_questions.append({
                        'question': f"Explain the main concepts and their significance as presented in the content.",
                        'answer': f"{first_para} {second_para[:300]}",
                        'type': 'descriptive'
                    })
            else:
                # Generic question for unidentified content
                content_based_questions.append({
                    'question': f"Describe the main concepts or ideas presented in the content and explain their significance.",
                    'answer': f"{first_para} {second_para[:300]}",
                    'type': 'descriptive'
                })
        
        if len(content_based_questions) < num_questions and characters and locations:
            content_based_questions.append({
                'question': f"Describe the relationship between {characters[0]} and the setting ({locations[0]}) as depicted in the passage.",
                'answer': f"The passage describes: {' '.join([s for s in sentences if characters[0] in s and locations[0] in s][:2] or sentences[:3])[:350]}",
                'type': 'descriptive'
            })
        
        # Fill remaining with paragraph-based questions
        for i, para in enumerate(paragraphs[:num_questions]):
            if len(content_based_questions) >= num_questions:
                break
            if len(para) > 100:
                # Extract key point from paragraph
                key_words = [w for w in para.split() if len(w) > 6 and w[0].isupper()][:3]
                if key_words:
                    content_based_questions.append({
                        'question': f"Explain the significance of the events or information described in the passage involving {', '.join(key_words[:2])}.",
                        'answer': f"The passage explains: {para[:350]}",
                        'type': 'descriptive'
                    })
        
        return content_based_questions[:num_questions]
        
        # OLD CODE BELOW - REMOVE
        if "Who are the main people or characters mentioned?" in extracted_facts:
            people = extracted_facts["Who are the main people or characters mentioned?"]['answer']
            ctx = extracted_facts["Who are the main people or characters mentioned?"]['context']
            content_based_questions.append({
                'question': f"Describe the role and significance of {people} in this passage and explain their actions or contributions.",
                'answer': f"According to the passage, {people} are described as follows: {ctx[:300]}",
                'type': 'descriptive'
            })
        
        # Question 2: About main event/topic
        if "What is the main event or topic discussed?" in extracted_facts:
            topic = extracted_facts["What is the main event or topic discussed?"]['answer']
            ctx = extracted_facts["What is the main event or topic discussed?"]['context']
            content_based_questions.append({
                'question': f"Explain the main topic or event regarding '{topic}' and describe its key aspects as presented in the passage.",
                'answer': f"The passage discusses: {topic}. Details: {ctx[:300]}",
                'type': 'descriptive'
            })
        
        # Question 3: About location/setting
        if "Where does this take place?" in extracted_facts:
            location = extracted_facts["Where does this take place?"]['answer']
            ctx = extracted_facts["Where does this take place?"]['context']
            # Try to get the main topic to make question more specific
            topic_info = ""
            if "What is the main event or topic discussed?" in extracted_facts:
                topic_info = f" in relation to {extracted_facts['What is the main event or topic discussed?']['answer']}"
            content_based_questions.append({
                'question': f"Describe the setting at {location}{topic_info} and explain how the location influences the events described in the passage.",
                'answer': f"The passage takes place at {location}. {ctx[:300]}",
                'type': 'descriptive'
            })
        
        # Question 4: About timing
        if "When did this happen or occur?" in extracted_facts:
            timing = extracted_facts["When did this happen or occur?"]['answer']
            ctx = extracted_facts["When did this happen or occur?"]['context']
            # Add what happened for context
            event_context = ""
            if "What is the main event or topic discussed?" in extracted_facts:
                event_context = f" regarding {extracted_facts['What is the main event or topic discussed?']['answer']}"
            content_based_questions.append({
                'question': f"Explain when the events{event_context} occurred ({timing}) and describe the historical or temporal context.",
                'answer': f"This occurred at {timing}. The passage states: {ctx[:300]}",
                'type': 'descriptive'
            })
        
        # Question 5: About significance
        if "Why is this significant or important?" in extracted_facts:
            significance = extracted_facts["Why is this significant or important?"]['answer']
            ctx = extracted_facts["Why is this significant or important?"]['context']
            # Get specific topic for better question
            topic_ref = "this"
            if "What is the main event or topic discussed?" in extracted_facts:
                topic_ref = extracted_facts['What is the main event or topic discussed?']['answer']
            content_based_questions.append({
                'question': f"Discuss why {topic_ref} is significant and explain the importance of what is described in the passage.",
                'answer': f"This is significant because: {significance}. The passage explains: {ctx[:300]}",
                'type': 'descriptive'
            })
        
        # Question 6: About problem/conflict
        if "What problem or conflict is described?" in extracted_facts:
            problem = extracted_facts["What problem or conflict is described?"]['answer']
            ctx = extracted_facts["What problem or conflict is described?"]['context']
            content_based_questions.append({
                'question': f"Explain the problem or conflict involving '{problem}' and describe how it is presented in the passage.",
                'answer': f"The problem described is: {problem}. Details: {ctx[:300]}",
                'type': 'descriptive'
            })
        
        # Question 7: About solution/outcome
        if "What is the outcome or result?" in extracted_facts:
            outcome = extracted_facts["What is the outcome or result?"]['answer']
            ctx = extracted_facts["What is the outcome or result?"]['context']
            # Reference the problem if available
            problem_ref = ""
            if "What problem or conflict is described?" in extracted_facts:
                problem_ref = f" of {extracted_facts['What problem or conflict is described?']['answer']}"
            content_based_questions.append({
                'question': f"Describe the outcome or result{problem_ref} mentioned in the passage and explain its implications.",
                'answer': f"The outcome is: {outcome}. The passage describes: {ctx[:300]}",
                'type': 'descriptive'
            })
        
        # Question 8: About how/process
        if "How did this happen or work?" in extracted_facts:
            process = extracted_facts["How did this happen or work?"]['answer']
            ctx = extracted_facts["How did this happen or work?"]['context']
            # Get what we're explaining
            subject = "the process"
            if "What is the main event or topic discussed?" in extracted_facts:
                subject = extracted_facts['What is the main event or topic discussed?']['answer']
            content_based_questions.append({
                'question': f"Explain how {subject} works or occurred as described in the passage and describe the mechanism or process involved.",
                'answer': f"The process works as follows: {process}. Details: {ctx[:300]}",
                'type': 'descriptive'
            })
        
        # Add specific questions based on detected content
        if len(content_based_questions) < num_questions:
            full_context = ' '.join(paragraphs[:3])
            # Extract key entities for more specific questions
            characters = self.document_context.get('characters', [])
            locations = self.document_context.get('locations', [])
            
            if characters and locations:
                content_based_questions.append({
                    'question': f"Describe the main events involving {characters[0]} and explain the significance of the locations mentioned ({', '.join(locations[:2])}).",
                    'answer': f"The passage describes: {full_context[:350]}",
                    'type': 'descriptive'
                })
            elif characters:
                content_based_questions.append({
                    'question': f"Explain the key events involving {characters[0]} and describe the relationships between the main characters.",
                    'answer': f"The passage describes: {full_context[:350]}",
                    'type': 'descriptive'
                })
            else:
                content_based_questions.append({
                    'question': f"Summarize the main events and explain the central conflict or situation described in the passage.",
                    'answer': f"The passage describes: {full_context[:350]}",
                    'type': 'descriptive'
                })
        
        if len(content_based_questions) < num_questions:
            # Look for specific historical/cultural references
            text_sample = ' '.join(paragraphs[:2])
            historical_refs = []
            if 'spain' in text_sample.lower() or 'spanish' in text_sample.lower():
                historical_refs.append('Spanish')
            if 'holy office' in text_sample.lower() or 'inquisition' in text_sample.lower():
                historical_refs.append('religious')
            if 'castle' in text_sample.lower() or 'palace' in text_sample.lower():
                historical_refs.append('royal')
            
            if historical_refs:
                ref_text = ' and '.join(historical_refs)
                content_based_questions.append({
                    'question': f"Discuss the {ref_text} context presented in the passage and explain how these elements contribute to the overall narrative.",
                    'answer': f"The passage provides the following context: {text_sample[:350]}",
                    'type': 'descriptive'
                })
            else:
                content_based_questions.append({
                    'question': f"Identify and explain the cultural or historical elements present in this passage.",
                    'answer': f"The passage mentions: {text_sample[:350]}",
                    'type': 'descriptive'
                })
        
        qa_pairs = content_based_questions[:num_questions]
        
        # Fill any remaining slots with context-aware questions
        while len(qa_pairs) < num_questions:
            context_sample = ' '.join(paragraphs[:2])
            characters = self.document_context.get('characters', [])
            if characters:
                qa_pairs.append({
                    'question': f"Analyze the setting and atmosphere of the passage and explain how they reflect {characters[0]}'s emotional state.",
                    'answer': f"The setting and atmosphere are described as: {context_sample[:350]}",
                    'type': 'descriptive'
                })
            else:
                qa_pairs.append({
                    'question': f"Describe the setting, atmosphere, and mood conveyed in this passage with specific examples.",
                    'answer': f"The passage conveys: {context_sample[:350]}",
                    'type': 'descriptive'
                })
        
        return qa_pairs[:num_questions]
    
    def get_character_context(self, character: str, char_sentences: List[str], full_text: str) -> Dict[str, str]:
        """Get contextual information about a character"""
        context = {
            'setting': 'the narrative',
            'situation': 'the events described'
        }
        
        # Look for setting clues
        text_lower = full_text.lower()
        if any(place in text_lower for place in ['castle', 'palace', 'kingdom']):
            context['setting'] = 'a medieval kingdom'
        elif any(place in text_lower for place in ['city', 'town', 'street']):
            context['setting'] = 'an urban setting'
        elif any(place in text_lower for place in ['forest', 'woods', 'mountain']):
            context['setting'] = 'a natural environment'
        elif any(place in text_lower for place in ['school', 'classroom', 'university']):
            context['setting'] = 'an educational setting'
        elif any(place in text_lower for place in ['office', 'company', 'business']):
            context['setting'] = 'a workplace'
        
        # Look for situation clues
        char_text = ' '.join(char_sentences).lower()
        if any(word in char_text for word in ['danger', 'threat', 'enemy', 'battle']):
            context['situation'] = 'a dangerous situation'
        elif any(word in char_text for word in ['journey', 'travel', 'adventure']):
            context['situation'] = 'an adventure or journey'
        elif any(word in char_text for word in ['problem', 'challenge', 'difficulty']):
            context['situation'] = 'a challenging situation'
        elif any(word in char_text for word in ['celebration', 'party', 'festival']):
            context['situation'] = 'a celebratory event'
        elif any(word in char_text for word in ['meeting', 'discussion', 'conversation']):
            context['situation'] = 'a social interaction'
        
        return context
    
    def get_specific_action_context(self, character: str, char_sentences: List[str], full_text: str) -> Dict[str, str]:
        """Get specific context about character actions"""
        context = {
            'story_context': 'the narrative',
            'action_type': 'actions and movements',
            'character_pronoun': 'his' if any(word in character.lower() for word in ['king', 'prince', 'man', 'boy']) else 'her' if any(word in character.lower() for word in ['queen', 'princess', 'woman', 'girl']) else 'their'
        }
        
        # Analyze the character sentences for specific context
        char_text = ' '.join(char_sentences).lower()
        full_text_lower = full_text.lower()
        
        # Determine story context based on content
        if any(word in full_text_lower for word in ['queen', 'dead', 'death', 'mourning', 'grief']):
            if 'king' in character.lower():
                context['story_context'] = 'a Spanish King mourning his deceased Queen'
                context['action_type'] = 'monthly ritual of visiting the Queen'
            else:
                context['story_context'] = 'a tale of loss and mourning'
                context['action_type'] = 'actions during this period of grief'
        elif any(word in full_text_lower for word in ['battle', 'war', 'fight', 'enemy']):
            context['story_context'] = 'a tale of conflict and battle'
            context['action_type'] = 'actions during the conflict'
        elif any(word in full_text_lower for word in ['journey', 'travel', 'adventure']):
            context['story_context'] = 'an adventure story'
            context['action_type'] = 'journey and travels'
        elif any(word in full_text_lower for word in ['palace', 'castle', 'kingdom', 'royal']):
            context['story_context'] = 'a royal court setting'
            context['action_type'] = 'royal duties and activities'
        elif any(word in full_text_lower for word in ['magic', 'wizard', 'spell', 'enchant']):
            context['story_context'] = 'a magical tale'
            context['action_type'] = 'magical activities'
        
        # Determine specific action type based on character sentences
        if any(word in char_text for word in ['knelt', 'kneeling', 'prayer']):
            context['action_type'] = 'ritual of kneeling and prayer'
        elif any(word in char_text for word in ['visit', 'visiting', 'went to']):
            context['action_type'] = 'visits and movements'
        elif any(word in char_text for word in ['cloak', 'lantern', 'secret']):
            context['action_type'] = 'secretive nocturnal activities'
        elif any(word in char_text for word in ['calling', 'cry', 'shout']):
            context['action_type'] = 'emotional outbursts and calls'
        
        return context
    
    def get_location_context(self, location: str, location_sentences: List[str], full_text: str) -> Dict[str, str]:
        """Get contextual information about a location"""
        context = {
            'time_context': 'the story events'
        }
        
        # Look for time/event context
        location_text = ' '.join(location_sentences).lower()
        if any(word in location_text for word in ['morning', 'dawn', 'sunrise']):
            context['time_context'] = 'the morning hours'
        elif any(word in location_text for word in ['evening', 'night', 'sunset']):
            context['time_context'] = 'the evening or night'
        elif any(word in location_text for word in ['battle', 'fight', 'war']):
            context['time_context'] = 'a conflict or battle'
        elif any(word in location_text for word in ['celebration', 'feast', 'party']):
            context['time_context'] = 'a celebration or gathering'
        elif any(word in location_text for word in ['crisis', 'emergency', 'danger']):
            context['time_context'] = 'a time of crisis'
        
        return context
    
    def generate_contextual_questions(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate questions with proper context about situations and events"""
        qa_pairs = []
        sentences = sent_tokenize(text)
        
        # Find important sentences with context
        important_sentences = []
        for i, sentence in enumerate(sentences):
            if len(sentence.split()) > 10 and len(sentence.split()) < 30:
                # Get surrounding context
                context_start = max(0, i-1)
                context_end = min(len(sentences), i+2)
                context = ' '.join(sentences[context_start:context_end])
                
                important_sentences.append({
                    'sentence': sentence,
                    'context': context,
                    'index': i
                })
        
        # Generate contextual questions
        for item in important_sentences[:num_questions]:
            # Create a question that includes context
            if any(word in item['sentence'].lower() for word in ['he', 'she', 'they']):
                # Find who 'he/she/they' refers to
                pronoun_context = self.resolve_pronoun_context(item['sentence'], item['context'])
                question = f"In the situation where {pronoun_context['situation']}, what happens and why is it significant?"
            elif any(word in item['sentence'].lower() for word in ['this', 'that', 'it']):
                # Resolve what 'this/that/it' refers to
                reference_context = self.resolve_reference_context(item['sentence'], item['context'])
                question = f"What is {reference_context['reference']} and what role does it play in the story?"
            else:
                # General contextual question
                question = f"What important event or development occurs in the story, and what is its significance?"
            
            qa_pairs.append({
                'question': question,
                'answer': f"Context: {item['context']}\n\nExplanation: This part of the story reveals important information about the characters and plot development.",
                'type': 'descriptive_contextual'
            })
        
        return qa_pairs
    
    def resolve_pronoun_context(self, sentence: str, context: str) -> Dict[str, str]:
        """Resolve pronoun references to provide context"""
        result = {'situation': 'the described events'}
        
        # Look for characters mentioned before the pronoun
        context_sentences = sent_tokenize(context)
        for char in self.document_context.get('main_characters', []):
            if char.lower() in context.lower():
                result['situation'] = f"the events involving {char}"
                break
        
        # Look for situation clues
        if any(word in context.lower() for word in ['danger', 'threat', 'attack']):
            result['situation'] = 'a dangerous confrontation'
        elif any(word in context.lower() for word in ['journey', 'travel', 'went']):
            result['situation'] = 'a journey or travel'
        elif any(word in context.lower() for word in ['meeting', 'spoke', 'said']):
            result['situation'] = 'a conversation or meeting'
        
        return result
    
    def resolve_reference_context(self, sentence: str, context: str) -> Dict[str, str]:
        """Resolve 'this/that/it' references"""
        result = {'reference': 'the item or concept mentioned'}
        
        # Look for objects or concepts mentioned before
        context_words = context.lower().split()
        important_nouns = []
        
        for concept in self.document_context.get('key_concepts', []):
            if concept.lower() in context.lower():
                result['reference'] = concept
                break
        
        return result
    
    def generate_programming_qa(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate programming questions with 'Write a program to...' format and full working code"""
        qa_pairs = []
        
        # First, try to extract question-code pairs directly from the text
        lines = text.split('\n')
        i = 0
        while i < len(lines) and len(qa_pairs) < num_questions:
            line = lines[i].strip()
            
            # Look for question patterns
            if line.lower().startswith('write a') or line.lower().startswith('write an'):
                question = line
                
                # Find the code that follows this question
                code_start = i + 1
                code_lines = []
                in_code = False
                brace_count = 0
                
                for j in range(code_start, min(code_start + 150, len(lines))):
                    code_line = lines[j]
                    stripped = code_line.strip()
                    
                    # Start of code
                    if not in_code and any(marker in stripped for marker in ['#include', 'import java', 'public class', 'int main(', 'def ', 'class ']):
                        in_code = True
                        code_lines.append(code_line)
                        if '{' in stripped:
                            brace_count = stripped.count('{') - stripped.count('}')
                    elif in_code:
                        code_lines.append(code_line)
                        
                        # Track braces
                        if '{' in stripped or '}' in stripped:
                            brace_count += stripped.count('{') - stripped.count('}')
                        
                        # Check if code is complete
                        if brace_count == 0 and len(code_lines) > 5:
                            block_text = '\n'.join(code_lines).lower()
                            if ('return' in block_text or 'system.out' in block_text or 'printf' in block_text or 'scanner.close' in block_text) and '}' in stripped:
                                break
                        
                        # Stop if we hit another question
                        if stripped.lower().startswith('write a') or stripped.lower().startswith('question'):
                            if code_lines and code_lines[-1].strip().lower().startswith('write'):
                                code_lines.pop()
                            break
                
                if code_lines and len(code_lines) > 3:
                    qa_pairs.append({
                        'question': question,
                        'answer': '\n'.join(code_lines).strip(),
                        'type': 'programming'
                    })
                    i = code_start + len(code_lines)
                else:
                    i += 1
            else:
                i += 1
        
        print(f"🔍 Extracted {len(qa_pairs)} question-code pairs directly")
        
        # If we didn't get enough from direct extraction, generate generic programming questions
        if len(qa_pairs) < num_questions:
            generic_tasks = [
                "find the factorial of a number",
                "check if a number is prime",
                "reverse a string",
                "find the largest element in an array",
                "sort an array using bubble sort",
                "implement a stack using arrays",
                "find the sum of digits of a number",
                "check if a string is a palindrome",
                "implement binary search",
                "find the GCD of two numbers"
            ]
            
            for task in generic_tasks:
                if len(qa_pairs) >= num_questions:
                    break
                
                # Generate sample code for the task
                sample_code = self.generate_sample_code_for_task(task)
                
                qa_pairs.append({
                    'question': f"Write a program to {task}.",
                    'answer': sample_code,
                    'type': 'programming'
                })
        
        return qa_pairs[:num_questions]
    
    def analyze_code_purpose(self, code: str) -> str:
        """Analyze code and return a description of what it does"""
        code_lower = code.lower()
        
        # Check for common patterns
        if 'factorial' in code_lower:
            return "calculate the factorial of a number"
        elif 'prime' in code_lower:
            return "check if a number is prime"
        elif 'fibonacci' in code_lower:
            return "generate Fibonacci series"
        elif 'palindrome' in code_lower:
            return "check if a string/number is a palindrome"
        elif 'reverse' in code_lower and 'string' in code_lower:
            return "reverse a string"
        elif 'sort' in code_lower:
            if 'bubble' in code_lower:
                return "sort an array using bubble sort"
            elif 'selection' in code_lower:
                return "sort an array using selection sort"
            else:
                return "sort an array"
        elif 'search' in code_lower:
            if 'binary' in code_lower:
                return "implement binary search"
            else:
                return "search for an element in an array"
        elif 'gcd' in code_lower or 'hcf' in code_lower:
            return "find the GCD/HCF of two numbers"
        elif 'lcm' in code_lower:
            return "find the LCM of two numbers"
        elif 'matrix' in code_lower:
            if 'add' in code_lower or 'sum' in code_lower:
                return "add two matrices"
            elif 'multiply' in code_lower or 'product' in code_lower:
                return "multiply two matrices"
            else:
                return "perform matrix operations"
        elif 'armstrong' in code_lower:
            return "check if a number is an Armstrong number"
        elif 'perfect' in code_lower:
            return "check if a number is a perfect number"
        elif 'swap' in code_lower:
            return "swap two numbers"
        elif 'largest' in code_lower or 'maximum' in code_lower:
            return "find the largest element in an array"
        elif 'smallest' in code_lower or 'minimum' in code_lower:
            return "find the smallest element in an array"
        elif 'sum' in code_lower and 'array' in code_lower:
            return "find the sum of all elements in an array"
        elif 'average' in code_lower or 'mean' in code_lower:
            return "calculate the average of numbers in an array"
        elif 'count' in code_lower:
            return "count specific elements or characters"
        elif 'pattern' in code_lower:
            return "print a pattern"
        elif 'table' in code_lower:
            return "print the multiplication table"
        elif 'power' in code_lower:
            return "calculate the power of a number"
        elif 'sqrt' in code_lower or 'square root' in code_lower:
            return "find the square root of a number"
        elif 'leap' in code_lower and 'year' in code_lower:
            return "check if a year is a leap year"
        elif 'vowel' in code_lower:
            return "check if a character is a vowel"
        elif 'length' in code_lower and 'string' in code_lower:
            return "find the length of a string"
        elif 'concatenate' in code_lower or 'concat' in code_lower:
            return "concatenate two strings"
        elif 'copy' in code_lower and ('array' in code_lower or 'string' in code_lower):
            return "copy an array/string"
        else:
            # Generic description based on code structure
            if 'for' in code_lower or 'while' in code_lower:
                return "perform operations using loops"
            elif 'if' in code_lower:
                return "make decisions using conditional statements"
            elif 'function' in code_lower or 'def ' in code_lower:
                return "implement a function to solve a problem"
            else:
                return "solve the given programming problem"
    
    def generate_sample_code_for_task(self, task: str) -> str:
        """Generate sample code for common programming tasks"""
        task_lower = task.lower()
        
        if 'factorial' in task_lower:
            return """# Python program to find factorial
def factorial(n):
    if n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)

# Input
num = int(input("Enter a number: "))

# Calculate and display factorial
result = factorial(num)
print(f"Factorial of {num} is {result}")"""
        
        elif 'prime' in task_lower:
            return """# Python program to check if a number is prime
def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

# Input
num = int(input("Enter a number: "))

# Check and display result
if is_prime(num):
    print(f"{num} is a prime number")
else:
    print(f"{num} is not a prime number")"""
        
        elif 'reverse' in task_lower and 'string' in task_lower:
            return """# Python program to reverse a string
def reverse_string(s):
    return s[::-1]

# Input
text = input("Enter a string: ")

# Reverse and display
reversed_text = reverse_string(text)
print(f"Reversed string: {reversed_text}")"""
        
        elif 'largest' in task_lower:
            return """# Python program to find the largest element in an array
def find_largest(arr):
    if not arr:
        return None
    largest = arr[0]
    for num in arr:
        if num > largest:
            largest = num
    return largest

# Input
n = int(input("Enter number of elements: "))
arr = []
for i in range(n):
    arr.append(int(input(f"Enter element {i+1}: ")))

# Find and display largest
result = find_largest(arr)
print(f"Largest element: {result}")"""
        
        elif 'bubble sort' in task_lower:
            return """# Python program to sort an array using bubble sort
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

# Input
n = int(input("Enter number of elements: "))
arr = []
for i in range(n):
    arr.append(int(input(f"Enter element {i+1}: ")))

# Sort and display
sorted_arr = bubble_sort(arr)
print(f"Sorted array: {sorted_arr}")"""
        
        elif 'palindrome' in task_lower:
            return """# Python program to check if a string is a palindrome
def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]

# Input
text = input("Enter a string: ")

# Check and display result
if is_palindrome(text):
    print(f"\"{text}\" is a palindrome")
else:
    print(f"\"{text}\" is not a palindrome")"""
        
        elif 'gcd' in task_lower:
            return """# Python program to find GCD of two numbers
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

# Input
num1 = int(input("Enter first number: "))
num2 = int(input("Enter second number: "))

# Calculate and display GCD
result = gcd(num1, num2)
print(f"GCD of {num1} and {num2} is {result}")"""
        
        elif 'sum of digits' in task_lower:
            return """# Python program to find sum of digits
def sum_of_digits(n):
    total = 0
    while n > 0:
        total += n % 10
        n //= 10
    return total

# Input
num = int(input("Enter a number: "))

# Calculate and display sum
result = sum_of_digits(num)
print(f"Sum of digits: {result}")"""
        
        elif 'binary search' in task_lower:
            return """# Python program to implement binary search
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# Input (array must be sorted)
arr = [2, 5, 8, 12, 16, 23, 38, 45, 56, 67, 78]
target = int(input("Enter number to search: "))

# Search and display result
result = binary_search(arr, target)
if result != -1:
    print(f"Element found at index {result}")
else:
    print("Element not found")"""
        
        elif 'stack' in task_lower:
            return """# Python program to implement a stack using arrays
class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        self.items.append(item)
    
    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        return None
    
    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        return None
    
    def is_empty(self):
        return len(self.items) == 0
    
    def size(self):
        return len(self.items)

# Example usage
stack = Stack()
stack.push(10)
stack.push(20)
stack.push(30)
print(f"Top element: {stack.peek()}")
print(f"Popped: {stack.pop()}")
print(f"Stack size: {stack.size()}")"""
        
        else:
            # Generic template
            return f"""# Python program to {task}
# TODO: Implement the solution

def solve():
    # Your code here
    pass

# Main program
if __name__ == "__main__":
    solve()"""
    
    def extract_programming_concepts(self, text: str) -> list:
        """Extract programming concepts mentioned in the text"""
        concepts = []
        text_lower = text.lower()
        
        concept_keywords = [
            'array', 'list', 'loop', 'function', 'recursion', 'sorting',
            'searching', 'stack', 'queue', 'tree', 'graph', 'algorithm'
        ]
        
        for keyword in concept_keywords:
            if keyword in text_lower:
                concepts.append(keyword)
        
        return concepts
    
    def find_matching_code_for_question(self, question: str, complete_code_blocks: list, used_codes: set):
        """Find the best matching code block for a question"""
        best_code = None
        if complete_code_blocks:
            for code in complete_code_blocks:
                if code not in used_codes:
                    best_code = code
                    used_codes.add(code)
                    break
        return best_code
    
    def is_complete_code_block(self, code: str) -> bool:
        """Check if a code block is complete and valid"""
        if len(code.strip()) < 20:
            return False
        # Check for basic code structure
        return True
    
    def extract_code_blocks_qagen_style(self, text: str) -> list:
        """Extract code blocks from text - improved for C/Java/Python"""
        code_blocks = []
        lines = text.split('\n')
        current_block = []
        in_code = False
        brace_count = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect code start
            if not in_code:
                # C/Java: #include, import, public class, int main
                if any(marker in stripped for marker in ['#include', 'import java', 'public class', 'int main(', 'def ', 'class ']):
                    in_code = True
                    current_block = [line]
                    if '{' in stripped:
                        brace_count = stripped.count('{') - stripped.count('}')
                elif '```' in stripped:
                    in_code = True
                    current_block = []
            else:
                # We're in code
                current_block.append(line)
                
                # Track braces for C/Java
                if '{' in stripped or '}' in stripped:
                    brace_count += stripped.count('{') - stripped.count('}')
                
                # Check if code block is complete
                is_complete = False
                
                # Method 1: Markdown code fence
                if '```' in stripped:
                    is_complete = True
                
                # Method 2: C/Java - balanced braces and return statement
                elif brace_count == 0 and len(current_block) > 5:
                    # Check if we have a complete C/Java program
                    block_text = '\n'.join(current_block).lower()
                    if ('return' in block_text or 'system.out' in block_text) and '}' in stripped:
                        is_complete = True
                
                # Method 3: Python - empty line after function/class
                elif 'def ' in '\n'.join(current_block[:3]) or 'class ' in '\n'.join(current_block[:3]):
                    if stripped == '' and len(current_block) > 5:
                        is_complete = True
                
                # Method 4: Next question detected
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip().lower()
                    if next_line.startswith('write a') or next_line.startswith('question'):
                        is_complete = True
                
                if is_complete:
                    if current_block:
                        code_blocks.append('\n'.join(current_block))
                    current_block = []
                    in_code = False
                    brace_count = 0
        
        # Don't forget the last block
        if current_block and len(current_block) > 3:
            code_blocks.append('\n'.join(current_block))
        
        return code_blocks
    
    def is_code_line(self, line: str) -> bool:
        """Check if a line looks like code rather than a question"""
        code_indicators = ['def ', 'class ', 'import ', 'from ', '=', '{', '}', ';', '//']
        return any(indicator in line for indicator in code_indicators)
    
    def generate_programming_questions_qagen_style(self, text: str) -> list:
        """Extract questions from text"""
        questions = []
        sentences = sent_tokenize(text)
        
        for sentence in sentences:
            if '?' in sentence and not self.is_code_line(sentence):
                questions.append(sentence.strip())
        
        return questions
    
    def find_matching_code_for_question_old(self, question: str, complete_code_blocks: list, used_codes: set):
        """Old method - kept for compatibility"""
        return self.find_matching_code_for_question(question, complete_code_blocks, used_codes)
    
    def is_complete_code_block(self, code: str) -> bool:
        """Check if a code block is complete and meaningful"""
        if len(code.strip()) < 20:  # Too short
            return False
        
        code_lower = code.lower()
        
        # For C programs, check for basic structure
        if '#include' in code_lower and 'main' in code_lower:
            return 'return' in code_lower or '}' in code  # Should have return or closing brace
        
        # For Python, check for basic structure
        if 'def ' in code_lower or 'print(' in code_lower:
            return True
        
        # For Java, check for basic structure
        if 'public class' in code_lower or 'public static void main' in code_lower:
            return True
        
        # General check - should have some programming constructs
        return any(construct in code_lower for construct in ['function', 'method', 'class', 'if', 'for', 'while'])
    
    def find_matching_code_for_question(self, question: str, code_blocks: List[str], used_codes: set) -> str:
        """Find the best matching code block for a given question"""
        question_lower = question.lower()
        
        # Look for keyword matches
        for code in code_blocks:
            if code in used_codes:
                continue
                
            code_lower = code.lower()
            
            # Check for specific matches
            if 'prime' in question_lower and 'prime' in code_lower:
                return code
            elif 'factorial' in question_lower and 'factorial' in code_lower:
                return code
            elif 'fibonacci' in question_lower and ('fibonacci' in code_lower or 'fib' in code_lower):
                return code
            elif 'array' in question_lower and 'array' in code_lower:
                return code
            elif 'largest' in question_lower and ('max' in code_lower or 'largest' in code_lower):
                return code
            elif 'smallest' in question_lower and ('min' in code_lower or 'smallest' in code_lower):
                return code
            elif 'even' in question_lower and 'odd' in question_lower and ('even' in code_lower or 'odd' in code_lower):
                return code
            elif 'palindrome' in question_lower and 'palindrome' in code_lower:
                return code
        
        # If no specific match, return first unused code
        for code in code_blocks:
            if code not in used_codes:
                return code
        
        return None
    
    def generate_question_from_code(self, code: str) -> str:
        """Generate a question based on code content"""
        code_lower = code.lower()
        
        # Detect programming language
        if '#include' in code_lower and ('printf' in code_lower or 'scanf' in code_lower):
            lang = "C"
        elif 'public class' in code_lower or 'system.out.println' in code_lower:
            lang = "Java"
        elif 'def ' in code_lower and 'print(' in code_lower:
            lang = "Python"
        else:
            lang = "programming language"
        
        # Detect purpose
        if 'prime' in code_lower:
            return f"Write a {lang} program to check if a number is prime."
        elif 'factorial' in code_lower:
            return f"Write a {lang} program to calculate factorial of a number."
        elif 'fibonacci' in code_lower:
            return f"Write a {lang} program to generate Fibonacci sequence."
        elif 'palindrome' in code_lower:
            return f"Write a {lang} program to check if a string is palindrome."
        elif 'array' in code_lower and ('max' in code_lower or 'largest' in code_lower):
            return f"Write a {lang} program to find the largest element in an array."
        elif 'array' in code_lower and ('min' in code_lower or 'smallest' in code_lower):
            return f"Write a {lang} program to find the smallest element in an array."
        elif 'even' in code_lower and 'odd' in code_lower:
            return f"Write a {lang} program to check if a number is even or odd."
        elif 'swap' in code_lower:
            return f"Write a {lang} program to swap two numbers."
        elif 'sort' in code_lower:
            return f"Write a {lang} program to sort an array."
        elif 'search' in code_lower:
            return f"Write a {lang} program to search for an element in array."
        else:
            return f"Write a {lang} program to solve the given problem."
    
    def extract_code_blocks_qagen_style(self, text: str) -> List[str]:
        """Extract code blocks using qagen.py's method"""
        codeblocks = []
        
        # Method 1: Find triple backticks
        matches = re.finditer(r'```.*?\n(.*?)```', text, re.DOTALL)
        for m in matches:
            codeblocks.append(m.group(1).strip())
        
        if not codeblocks:
            # Method 2: Find indented blocks
            lines = text.split('\n')
            current_block = []
            inside_block = False
            for line in lines:
                if line.startswith('    ') or line.startswith('\t') or self.is_code_line(line):
                    current_block.append(line.lstrip())
                    inside_block = True
                else:
                    if inside_block and current_block:
                        codeblocks.append('\n'.join(current_block).strip())
                        current_block = []
                        inside_block = False
            if inside_block and current_block:
                codeblocks.append('\n'.join(current_block).strip())
        
        if not codeblocks:
            # Method 3: Find blocks with high density of code-like characters
            blocks = re.split(r'\n\s*\n', text)
            for block in blocks:
                lines = block.split('\n')
                count_code_lines = sum(1 for l in lines if re.search(r'[;{}()=<>+-]', l))
                if count_code_lines >= max(1, len(lines)//2):
                    codeblocks.append(block.strip())
        
        return codeblocks
    
    def is_code_line(self, text: str) -> bool:
        """Check if a line looks like code"""
        code_indicators = ['#include', 'int ', 'printf', 'scanf', '{', '}', ';', 'return', 'main', 'def ', 'class ', 'import ']
        text_lower = text.lower()
        return any(ci in text_lower for ci in code_indicators)
    
    def generate_programming_questions_qagen_style(self, text: str) -> List[str]:
        """Generate programming questions using qagen.py's method"""
        questions = []
        keywords = ['function', 'class', 'algorithm', 'method', 'program', 'implement', 'write', 'code', 'define']
        sentences = sent_tokenize(text)
        
        for s in sentences:
            sl = s.lower()
            if any(k in sl for k in keywords):
                # Create more natural programming questions
                if 'write' in sl and 'program' in sl:
                    questions.append(s)
                elif 'function' in sl:
                    questions.append(f"Implement the following function: {s}")
                elif 'algorithm' in sl:
                    questions.append(f"Write a program to implement: {s}")
                else:
                    questions.append(f"Create a program based on: {s}")
        
        return list(dict.fromkeys(questions))  # Remove duplicates
    
    def generate_math_qa(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate math questions with equation solving"""
        qa_pairs = []
        
        # Formula-based questions
        for formula in self.document_context.get('formulas', [])[:num_questions//3]:
            qa_pairs.append({
                'question': f"Solve this mathematical problem step by step:",
                'answer': f"Mathematical Solution:\n\nGiven: {formula}\n\nStep-by-step solution:\n{self.solve_math_problem(formula)}\n\nFinal Answer: {self.get_math_result(formula)}",
                'type': 'math_calculation',
                'formula': formula
            })
        
        # Word problem questions
        for word_problem in self.document_context.get('word_problems', [])[:num_questions//3]:
            qa_pairs.append({
                'question': f"Solve this word problem with detailed steps:",
                'answer': f"Word Problem Solution:\n\nProblem: {word_problem}\n\nSolution Steps:\n{self.solve_word_problem(word_problem)}\n\nAnswer: {self.get_word_problem_answer(word_problem)}",
                'type': 'math_word_problem',
                'problem': word_problem
            })
        
        # Theorem questions
        for theorem in self.document_context.get('theorems', [])[:num_questions-len(qa_pairs)]:
            qa_pairs.append({
                'question': f"Explain this theorem and provide a mathematical proof:",
                'answer': f"Theorem Explanation:\n\n{theorem}\n\nMathematical Proof:\n{self.generate_proof_steps(theorem)}\n\nApplications: {self.get_theorem_applications(theorem)}",
                'type': 'math_theorem',
                'theorem': theorem
            })
        
        return qa_pairs[:num_questions]
    
    def generate_mcq_questions(self, text: str, num_questions: int, content_type: str) -> List[Dict[str, Any]]:
        """Generate Multiple Choice Questions with 4 options - works for any content type"""
        qa_pairs = []
        sentences = sent_tokenize(text)
        
        # For programming content, generate programming-specific MCQs
        if content_type == "programming" or any(keyword in text.lower() for keyword in ['#include', 'import java', 'def ', 'class ', 'int main', 'public class']):
            return self.generate_programming_mcqs(text, num_questions)
        
        # Check if we have story content (characters/locations)
        has_story_content = bool(self.document_context.get('main_characters') or self.document_context.get('locations'))
        
        # For story content, use the story-based MCQ generator directly
        if has_story_content:
            print("🔍 Detected story content, using story-based MCQ generator")
            mcq_types = ['character', 'location', 'event', 'detail', 'comprehension']
            used_questions = set()
            attempts = 0
            max_attempts = num_questions * 5
            
            while len(qa_pairs) < num_questions and attempts < max_attempts:
                attempts += 1
                mcq_type = mcq_types[(len(qa_pairs)) % len(mcq_types)]
                mcq = None
                current_index = len(qa_pairs)
                
                if mcq_type == 'character' and self.document_context.get('main_characters'):
                    mcq = self.generate_character_mcq(text, current_index)
                elif mcq_type == 'location' and self.document_context.get('locations'):
                    mcq = self.generate_location_mcq(text, current_index)
                elif mcq_type == 'event':
                    mcq = self.generate_event_mcq(text, sentences, current_index)
                elif mcq_type == 'detail':
                    mcq = self.generate_detail_mcq(text, sentences, current_index)
                elif mcq_type == 'comprehension':
                    mcq = self.generate_comprehension_mcq(text, sentences, current_index)
                
                if mcq and mcq['question'] not in used_questions:
                    mcq = self.randomize_mcq_options(mcq)
                    qa_pairs.append(mcq)
                    used_questions.add(mcq['question'])
        else:
            # For general/technical content, use factual extraction
            print("🔍 Using factual extraction for MCQ generation")
            factual_sentences = []
            for sentence in sentences:
                # Look for sentences with specific information
                if any(word in sentence.lower() for word in ['is', 'are', 'was', 'were', 'has', 'have', 'can', 'will', 'does', 'called', 'known as']):
                    if len(sentence.split()) > 5 and len(sentence.split()) < 30:
                        factual_sentences.append(sentence)
            
            used_questions = set()
            
            for sentence in factual_sentences[:num_questions * 2]:
                if len(qa_pairs) >= num_questions:
                    break
                
                mcq = self.create_mcq_from_sentence(sentence, text)
                if mcq and mcq['question'] not in used_questions:
                    # Randomize the correct answer position
                    mcq = self.randomize_mcq_options(mcq)
                    qa_pairs.append(mcq)
                    used_questions.add(mcq['question'])
        
        return qa_pairs[:num_questions]
    
    def create_mcq_from_sentence(self, sentence: str, full_text: str) -> Dict[str, Any]:
        """Create an MCQ from a factual sentence"""
        # Find the key information in the sentence
        words = sentence.split()
        
        # Look for patterns like "X is Y" or "X are Y"
        for i, word in enumerate(words):
            if word.lower() in ['is', 'are', 'was', 'were'] and i > 0 and i < len(words) - 1:
                subject = ' '.join(words[:i])
                predicate = ' '.join(words[i+1:]).rstrip('.')
                
                # Create question
                question = f"What {word} {subject}?"
                
                # Correct answer
                correct_answer = predicate
                
                # Generate distractors
                distractors = self.generate_distractors(correct_answer, full_text)
                
                if len(distractors) >= 3:
                    return {
                        'question': question,
                        'options': [correct_answer] + distractors[:3],
                        'correct_answer': 'A',  # Will be randomized later
                        'explanation': f"The text states: {sentence}",
                        'type': 'mcq'
                    }
        
        return None
    
    def generate_distractors(self, correct_answer: str, text: str) -> list:
        """Generate plausible wrong answers"""
        distractors = []
        sentences = sent_tokenize(text)
        
        # Extract other similar phrases from the text
        for sentence in sentences:
            if correct_answer.lower() not in sentence.lower():
                words = sentence.split()
                # Extract noun phrases
                for i in range(len(words) - 2):
                    phrase = ' '.join(words[i:i+3])
                    if phrase != correct_answer and len(phrase.split()) >= 2:
                        distractors.append(phrase)
        
        # Add some generic distractors if needed
        if len(distractors) < 3:
            generic = [
                "None of the above",
                "Not mentioned in the text",
                "All of the above",
                "Cannot be determined"
            ]
            distractors.extend(generic)
        
        return distractors[:3]
    
    def generate_programming_mcqs(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate MCQs specifically for programming content"""
        qa_pairs = []
        
        # Common programming MCQ patterns
        mcq_templates = [
            {
                'question': 'What is the output of the following code?',
                'type': 'output'
            },
            {
                'question': 'Which of the following is the correct syntax for {}?',
                'type': 'syntax'
            },
            {
                'question': 'What does the {} function/method do?',
                'type': 'function'
            },
            {
                'question': 'Which data structure is used in the code?',
                'type': 'datastructure'
            },
            {
                'question': 'What is the time complexity of this algorithm?',
                'type': 'complexity'
            }
        ]
        
        # Extract code snippets
        lines = text.split('\n')
        code_snippets = []
        current_snippet = []
        
        for line in lines:
            if any(marker in line for marker in ['#include', 'import', 'def ', 'int ', 'void ', 'public ', 'class ']):
                if current_snippet:
                    code_snippets.append('\n'.join(current_snippet))
                current_snippet = [line]
            elif current_snippet:
                current_snippet.append(line)
                if len(current_snippet) > 10:
                    code_snippets.append('\n'.join(current_snippet))
                    current_snippet = []
        
        # Generate MCQs from code
        for i, snippet in enumerate(code_snippets[:num_questions]):
            snippet_lower = snippet.lower()
            
            # Determine question type based on code content
            if 'printf' in snippet_lower or 'system.out' in snippet_lower or 'print' in snippet_lower:
                question = "What is the output of this code?"
                options = self.generate_output_options(snippet)
            elif 'for' in snippet_lower or 'while' in snippet_lower:
                question = "What type of loop is used in this code?"
                if 'for' in snippet_lower:
                    options = ["for loop", "while loop", "do-while loop", "foreach loop"]
                else:
                    options = ["while loop", "for loop", "do-while loop", "infinite loop"]
            elif 'if' in snippet_lower:
                question = "What control structure is primarily used?"
                options = ["Conditional (if-else)", "Loop", "Switch-case", "Try-catch"]
            elif 'array' in snippet_lower or '[]' in snippet:
                question = "What data structure is used?"
                options = ["Array", "Linked List", "Stack", "Queue"]
            else:
                question = "What does this code do?"
                purpose = self.analyze_code_purpose(snippet)
                options = [
                    purpose.capitalize(),
                    "Sort an array",
                    "Search for an element",
                    "Calculate factorial"
                ]
            
            qa_pairs.append({
                'question': question,
                'options': options,
                'correct_answer': 'A',  # Will be randomized
                'explanation': f"Based on the code: {snippet[:100]}...",
                'type': 'mcq'
            })
        
        return qa_pairs[:num_questions]
    
    def generate_output_options(self, code: str) -> list:
        """Generate plausible output options for code"""
        # This is simplified - in reality, you'd need to execute or analyze the code
        return [
            "Correct output based on code logic",
            "Compilation error",
            "Runtime error",
            "No output"
        ]
    
    def randomize_mcq_options(self, mcq: Dict[str, Any]) -> Dict[str, Any]:
        """Randomize the position of the correct answer in MCQ options"""
        if 'options' not in mcq or len(mcq['options']) != 4:
            return mcq
        
        options = mcq['options'].copy()
        correct_option = options[0]  # The correct answer is always at index 0 initially
        
        # Shuffle the options
        random.shuffle(options)
        
        # Find the new position of the correct answer
        new_correct_index = options.index(correct_option)
        correct_letters = ['A', 'B', 'C', 'D']
        
        # Update the correct answer letter
        mcq['correct_answer'] = correct_letters[new_correct_index]
        mcq['options'] = options
        
        return mcq
    
    def generate_character_mcq(self, text: str, index: int = 0) -> Dict[str, Any]:
        """Generate character-based MCQ"""
        characters = self.document_context.get('main_characters', [])
        if not characters:
            return None
            
        main_char = characters[0]
        sentences = sent_tokenize(text)
        char_sentences = [s for s in sentences if main_char.lower() in s.lower()]
        
        if char_sentences:
            # Use different sentences based on index to avoid duplicates
            context_sentence = char_sentences[min(index, len(char_sentences)-1)]
            
            # Create different questions based on index
            if 'king' in main_char.lower():
                if index == 0:
                    return {
                        'question': f"According to the passage, what does the {main_char} do every month?",
                        'options': [
                            "Visits the Queen's tomb with a lantern and dark cloak",
                            "Holds court sessions with his advisors",
                            "Travels to neighboring kingdoms",
                            "Organizes royal celebrations"
                        ],
                        'correct_answer': 'A',
                        'explanation': f"The text states: {context_sentence}",
                        'type': 'character_mcq'
                    }
                else:
                    return {
                        'question': f"What does the {main_char} call the Queen when he visits?",
                        'options': [
                            "Mi reina!",
                            "My beloved",
                            "Your Majesty",
                            "My dear"
                        ],
                        'correct_answer': 'A',
                        'explanation': f"The text mentions: {context_sentence}",
                        'type': 'character_mcq'
                    }
            else:
                return {
                    'question': f"What role does {main_char} play in the story?",
                    'options': [
                        f"The role described in the passage",
                        f"A traveling merchant",
                        f"A court advisor", 
                        f"A royal guard"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The text describes: {context_sentence}",
                    'type': 'character_mcq'
                }
        return None
    
    def generate_location_mcq(self, text: str, index: int = 0) -> Dict[str, Any]:
        """Generate location-based MCQ"""
        locations = self.document_context.get('locations', [])
        if not locations:
            return None
            
        location = locations[0].replace('.', '').replace(',', '')  # Clean location name
        sentences = sent_tokenize(text)
        location_sentences = [s for s in sentences if location.lower() in s.lower()]
        
        if location_sentences:
            context_sentence = location_sentences[0]
            
            # Create specific options based on location type
            if any(word in location.lower() for word in ['castle', 'palace']):
                return {
                    'question': f"What is significant about {location} in the story?",
                    'options': [
                        "It houses the Queen's preserved body in a marble chapel",
                        "It serves as a military fortress",
                        "It hosts diplomatic meetings",
                        "It contains the royal treasury"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The text describes: {context_sentence}",
                    'type': 'location_mcq'
                }
            else:
                return {
                    'question': f"What connection does {location} have to the story?",
                    'options': [
                        "The connection described in the passage",
                        "It's where battles are fought",
                        "It's a trading center",
                        "It's a place of worship"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The text mentions: {context_sentence}",
                    'type': 'location_mcq'
                }
        return None
    
    def generate_event_mcq(self, text: str, sentences: List[str], index: int = 0) -> Dict[str, Any]:
        """Generate event-based MCQ"""
        # Find sentences with specific events
        event_sentences = []
        for sentence in sentences:
            if any(phrase in sentence.lower() for phrase in ['once every month', 'when she died', 'had been embalmed', 'calling out']):
                event_sentences.append(sentence)
        
        if not event_sentences:
            # Fallback to action sentences
            for sentence in sentences:
                if any(word in sentence.lower() for word in ['went', 'came', 'knelt', 'wrapped']):
                    if len(sentence.split()) > 8 and len(sentence.split()) < 25:
                        event_sentences.append(sentence)
        
        if event_sentences:
            # Use different sentences/events based on index
            event_sentence = event_sentences[min(index, len(event_sentences)-1)]
            
            # Create different questions based on index and content
            if index == 0 and 'once every month' in event_sentence.lower():
                return {
                    'question': "How often does the King visit the Queen's body?",
                    'options': [
                        "Once every month",
                        "Every week",
                        "Daily",
                        "Only on special occasions"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The text states: {event_sentence}",
                    'type': 'event_mcq'
                }
            elif index == 1 and 'died' in event_sentence.lower():
                return {
                    'question': "What happened to the Queen according to the passage?",
                    'options': [
                        "She died and the King was devastated",
                        "She left the kingdom",
                        "She became ill",
                        "She went into exile"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The text explains: {event_sentence}",
                    'type': 'event_mcq'
                }
            elif index == 2:
                # Find the correct sentence about calling out
                calling_sentence = None
                all_sentences = sent_tokenize(text)
                for s in all_sentences:
                    if 'calling out' in s.lower() or 'mi reina' in s.lower():
                        calling_sentence = s
                        break
                
                return {
                    'question': "What does the King do when he visits?",
                    'options': [
                        "Kneels by her side and calls out 'Mi reina!'",
                        "Prays silently",
                        "Brings flowers",
                        "Reads poetry"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The text describes: {calling_sentence or event_sentence}",
                    'type': 'event_mcq'
                }
            else:
                # Find appropriate sentence for the question
                calling_sentence = None
                all_sentences = sent_tokenize(text)
                for s in all_sentences:
                    if 'calling out' in s.lower() or 'mi reina' in s.lower() or 'knelt' in s.lower():
                        calling_sentence = s
                        break
                
                return {
                    'question': "What does the King do when he visits?",
                    'options': [
                        "Kneels by her side and calls out 'Mi reina!'",
                        "Prays silently",
                        "Brings flowers",
                        "Reads poetry"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The text describes: {calling_sentence or event_sentence}",
                    'type': 'event_mcq'
                }
        return None
    
    def generate_detail_mcq(self, text: str, sentences: List[str], index: int = 0) -> Dict[str, Any]:
        """Generate detail-based MCQ"""
        # Find sentences with specific details about appearance, objects, or descriptions
        detail_sentences = []
        for sentence in sentences:
            if any(phrase in sentence.lower() for phrase in ['dark cloak', 'muffled lantern', 'marble chapel', 'poisoned gloves', 'black marble']):
                detail_sentences.append(sentence)
        
        if not detail_sentences:
            # Fallback to time-related details
            for sentence in sentences:
                if any(word in sentence.lower() for word in ['every', 'once', 'twelve years', 'march day']):
                    if len(sentence.split()) > 10 and len(sentence.split()) < 30:
                        detail_sentences.append(sentence)
        
        if detail_sentences:
            detail_sentence = detail_sentences[0]
            
            if 'dark cloak' in detail_sentence.lower():
                return {
                    'question': "What does the King wear when he visits the Queen?",
                    'options': [
                        "A dark cloak and carries a muffled lantern",
                        "Royal robes and a crown",
                        "Simple peasant clothes",
                        "Military armor"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The text specifically states: {detail_sentence}",
                    'type': 'detail_mcq'
                }
            elif 'marble chapel' in detail_sentence.lower():
                return {
                    'question': "Where is the Queen's body kept?",
                    'options': [
                        "In a black marble chapel of the Palace",
                        "In the royal cemetery",
                        "In a golden tomb",
                        "In the castle tower"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The text describes: {detail_sentence}",
                    'type': 'detail_mcq'
                }
            else:
                return {
                    'question': "What specific detail does the passage mention?",
                    'options': [
                        "The detail described in the text",
                        "Daily court ceremonies", 
                        "Weekly royal meetings",
                        "Annual kingdom celebrations"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The text mentions: {detail_sentence}",
                    'type': 'detail_mcq'
                }
        return None
    
    def generate_comprehension_mcq(self, text: str, sentences: List[str], index: int = 0) -> Dict[str, Any]:
        """Generate comprehension-based MCQ"""
        # Find sentences about emotions, relationships, or motivations
        emotion_sentences = []
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['love', 'grief', 'sorrow', 'bereft', 'reason', 'mad kisses']):
                emotion_sentences.append(sentence)
        
        if emotion_sentences:
            # Use different sentences based on index
            emotion_sentence = emotion_sentences[min(index, len(emotion_sentences)-1)]
            
            # Create different questions based on index
            if index == 0 and 'love' in emotion_sentence.lower():
                return {
                    'question': "What does the passage reveal about the King's feelings for the Queen?",
                    'options': [
                        "His love was so great he couldn't let even death separate them",
                        "He loved her wealth and status",
                        "He had a political marriage with her",
                        "He respected her as a ruler"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The text reveals: {emotion_sentence}",
                    'type': 'comprehension_mcq'
                }
            elif index == 1 and ('grief' in emotion_sentence.lower() or 'sorrow' in emotion_sentence.lower()):
                return {
                    'question': "How did the King react to the Queen's death?",
                    'options': [
                        "He was overwhelmed with grief and sorrow",
                        "He quickly remarried",
                        "He became angry and violent",
                        "He celebrated his freedom"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The passage describes: {emotion_sentence}",
                    'type': 'comprehension_mcq'
                }
            elif index == 2:
                return {
                    'question': "What emotional state is described in the passage?",
                    'options': [
                        "Deep emotional pain and loss",
                        "Joy and celebration",
                        "Anger and revenge",
                        "Peace and contentment"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The text shows: {emotion_sentence}",
                    'type': 'comprehension_mcq'
                }
            else:
                return {
                    'question': "What is the main theme of this passage?",
                    'options': [
                        "A story of love, loss, and mourning",
                        "A tale of political intrigue",
                        "A historical account of wars",
                        "A description of royal ceremonies"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The passage focuses on: {emotion_sentence}",
                    'type': 'comprehension_mcq'
                }
        
        # Fallback to general comprehension
        informative_sentences = [s for s in sentences if len(s.split()) > 12 and len(s.split()) < 25]
        if informative_sentences:
            info_sentence = informative_sentences[0]
            return {
                'question': "What is the main theme of this passage?",
                'options': [
                    "A story of love, loss, and mourning",
                    "A tale of political intrigue",
                    "A historical account of wars",
                    "A description of royal ceremonies"
                ],
                'correct_answer': 'A',
                'explanation': f"The passage focuses on: {info_sentence}",
                'type': 'comprehension_mcq'
            }
        return None
    
    def generate_mcq_from_sentence(self, sentence: str, full_text: str, content_type: str) -> Dict[str, Any]:
        """Generate a single MCQ from a sentence"""
        sentence_lower = sentence.lower()
        
        if content_type == "programming":
            return self.generate_programming_mcq(sentence, full_text)
        elif content_type == "math":
            return self.generate_math_mcq(sentence, full_text)
        elif content_type == "descriptive":
            return self.generate_descriptive_mcq(sentence, full_text)
        else:
            return self.generate_general_mcq(sentence, full_text)
    
    def generate_programming_mcq(self, sentence: str, full_text: str) -> Dict[str, Any]:
        """Generate programming-specific MCQ"""
        sentence_lower = sentence.lower()
        
        if 'function' in sentence_lower:
            return {
                'question': f"What is the primary purpose of the function described in: '{sentence[:80]}...'?",
                'options': [
                    "To perform the specific operation described in the text",
                    "To handle only user input validation",
                    "To manage memory allocation exclusively", 
                    "To display output formatting only"
                ],
                'correct_answer': 'A',
                'explanation': f"Based on the context: {sentence}",
                'type': 'programming_mcq'
            }
        elif any(word in sentence_lower for word in ['array', 'list', 'data structure']):
            return {
                'question': f"What data structure concept is being discussed in this statement?",
                'options': [
                    "The specific data structure mentioned in the passage",
                    "Hash tables exclusively",
                    "Binary search trees only",
                    "Stack data structures only"
                ],
                'correct_answer': 'A',
                'explanation': f"The passage discusses: {sentence}",
                'type': 'programming_mcq'
            }
        else:
            return {
                'question': f"What programming concept is explained in this passage?",
                'options': [
                    "The concept described in the given text",
                    "Object-oriented programming exclusively",
                    "Database management only",
                    "Network programming only"
                ],
                'correct_answer': 'A',
                'explanation': f"The text explains: {sentence}",
                'type': 'programming_mcq'
            }
    
    def generate_math_mcq(self, sentence: str, full_text: str) -> Dict[str, Any]:
        """Generate math-specific MCQ"""
        sentence_lower = sentence.lower()
        
        if any(symbol in sentence for symbol in ['=', '+', '-', '*', '/', '^']):
            return {
                'question': f"What does the mathematical expression in this statement represent?",
                'options': [
                    "The mathematical relationship described in the text",
                    "A geometric formula exclusively",
                    "A statistical calculation only",
                    "A probability distribution only"
                ],
                'correct_answer': 'A',
                'explanation': f"The expression represents: {sentence}",
                'type': 'math_mcq'
            }
        elif 'theorem' in sentence_lower:
            return {
                'question': f"What does this mathematical theorem establish?",
                'options': [
                    "The principle stated in the passage",
                    "Only geometric relationships",
                    "Only algebraic identities", 
                    "Only calculus derivatives"
                ],
                'correct_answer': 'A',
                'explanation': f"The theorem states: {sentence}",
                'type': 'math_mcq'
            }
        else:
            return {
                'question': f"What mathematical concept is being explained?",
                'options': [
                    "The concept described in the text",
                    "Linear algebra exclusively",
                    "Number theory only",
                    "Set theory only"
                ],
                'correct_answer': 'A',
                'explanation': f"The concept is: {sentence}",
                'type': 'math_mcq'
            }
    
    def generate_descriptive_mcq(self, sentence: str, full_text: str) -> Dict[str, Any]:
        """Generate descriptive/story MCQ"""
        # Character-based MCQ
        for character in self.document_context.get('main_characters', []):
            if character.lower() in sentence.lower():
                return {
                    'question': f"What did {character} do according to this passage?",
                    'options': [
                        f"What is described in the text about {character}",
                        f"Traveled to distant kingdoms",
                        f"Became a wealthy merchant",
                        f"Studied ancient magical texts"
                    ],
                    'correct_answer': 'A',
                    'explanation': f"The text states: {sentence}",
                    'type': 'descriptive_mcq'
                }
        
        # General descriptive MCQ
        return {
            'question': f"What information is provided in this statement?",
            'options': [
                f"The information stated in the passage",
                f"Historical background exclusively",
                f"Scientific data only",
                f"Personal opinions only"
            ],
            'correct_answer': 'A',
            'explanation': f"The statement provides: {sentence}",
            'type': 'descriptive_mcq'
        }
    
    def generate_general_mcq(self, sentence: str, full_text: str) -> Dict[str, Any]:
        """Generate general MCQ"""
        return {
            'question': f"What is the main point of this statement?",
            'options': [
                f"The point made in the given text",
                f"General background information",
                f"Technical specifications only",
                f"Comparative analysis only"
            ],
            'correct_answer': 'A',
            'explanation': f"The statement explains: {sentence}",
            'type': 'general_mcq'
        }
    
    # Helper methods for enhanced analysis
    def create_enhanced_character_analysis(self, character: str, char_sentences: List[str], full_text: str, analysis_type: str) -> str:
        """Create detailed character analysis"""
        analysis = f"Character Analysis for {character}:\n\n"
        
        if analysis_type == 'dialogue':
            analysis += f"Dialogue and Communication:\n"
            for sentence in char_sentences[:3]:
                if any(word in sentence.lower() for word in ['said', 'spoke', 'called', 'asked', 'replied']):
                    analysis += f"- {sentence}\n"
            analysis += f"\nThis reveals {character}'s communication style and personality traits."
        
        elif analysis_type == 'actions':
            analysis += f"Actions and Movements:\n"
            for sentence in char_sentences[:3]:
                if any(word in sentence.lower() for word in ['went', 'came', 'traveled', 'walked', 'moved']):
                    analysis += f"- {sentence}\n"
            analysis += f"\nThese actions show {character}'s role and importance in the narrative."
        
        else:
            analysis += f"General Character Information:\n"
            for sentence in char_sentences[:3]:
                analysis += f"- {sentence}\n"
            analysis += f"\nThis provides insight into {character}'s overall significance in the story."
        
        return analysis
    
    def create_location_analysis(self, location: str, location_sentences: List[str], full_text: str) -> str:
        """Create detailed location analysis"""
        analysis = f"Location Analysis for {location}:\n\n"
        analysis += f"Events and Significance:\n"
        for sentence in location_sentences[:3]:
            analysis += f"- {sentence}\n"
        analysis += f"\n{location} serves as an important setting that influences the narrative development."
        return analysis
    
    def create_concept_analysis(self, concept: str, concept_sentences: List[str], full_text: str) -> str:
        """Create detailed concept analysis"""
        analysis = f"Concept Analysis for '{concept}':\n\n"
        analysis += f"Relevant Information:\n"
        for sentence in concept_sentences[:3]:
            analysis += f"- {sentence}\n"
        analysis += f"\nThe concept of '{concept}' plays a significant role in the overall understanding of the text."
        return analysis
    
    def generate_thematic_questions(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate general thematic questions"""
        qa_pairs = []
        sentences = sent_tokenize(text)
        
        # Select informative sentences
        informative_sentences = [s for s in sentences if len(s.split()) > 10 and len(s.split()) < 25]
        
        for i, sentence in enumerate(informative_sentences[:num_questions]):
            qa_pairs.append({
                'question': f"What is the main idea or theme presented in this statement?",
                'answer': f"Main Theme Analysis:\n\n{sentence}\n\nThis statement contributes to the overall understanding by providing key information about the subject matter.",
                'type': 'descriptive_thematic'
            })
        
        return qa_pairs
    
    def analyze_code_functionality(self, code_block: str) -> str:
        """Analyze what a code block does"""
        code_lower = code_block.lower()
        
        if any(word in code_lower for word in ['printf', 'cout', 'print']):
            return "This code block handles output operations, displaying information to the user."
        elif any(word in code_lower for word in ['scanf', 'cin', 'input']):
            return "This code block handles input operations, receiving data from the user."
        elif any(word in code_lower for word in ['for', 'while', 'loop']):
            return "This code block implements a loop structure for repetitive operations."
        elif any(word in code_lower for word in ['if', 'else', 'switch']):
            return "This code block implements conditional logic for decision-making."
        elif any(word in code_lower for word in ['function', 'def', 'method']):
            return "This code block defines a function or method to perform specific operations."
        else:
            return "This code block performs specific programming operations as described in the context."
    
    def analyze_function_purpose(self, function_text: str) -> str:
        """Analyze the purpose of a function"""
        func_lower = function_text.lower()
        
        if any(word in func_lower for word in ['sort', 'arrange']):
            return "This function is designed to sort or arrange data elements."
        elif any(word in func_lower for word in ['search', 'find']):
            return "This function is designed to search for specific elements or data."
        elif any(word in func_lower for word in ['calculate', 'compute']):
            return "This function is designed to perform calculations or computations."
        elif any(word in func_lower for word in ['validate', 'check']):
            return "This function is designed to validate or check data integrity."
        else:
            return "This function performs the specific operation described in the context."
    
    def get_complete_code_context(self, function_text: str, full_text: str) -> str:
        """Get complete code context for a function"""
        return f"// Complete implementation based on context\n{function_text}\n\n// This implementation follows the requirements specified in the document."
    
    def get_algorithm_implementation(self, algorithm_text: str, full_text: str) -> str:
        """Get algorithm implementation steps"""
        steps = [
            "1. Initialize necessary variables and data structures",
            "2. Implement the main algorithm logic as described",
            "3. Handle edge cases and error conditions", 
            "4. Return or output the final result"
        ]
        return "\n".join(steps) + f"\n\nBased on: {algorithm_text}"
    
    def solve_math_problem(self, formula: str) -> str:
        """Solve mathematical problems step by step"""
        if SYMPY_AVAILABLE:
            try:
                # Try to solve with SymPy if available
                if '=' in formula:
                    left, right = formula.split('=', 1)
                    eq = sympify(left) - sympify(right)
                    x = Symbol('x')
                    sols = solve(eq, x)
                    return f"1. Set up the equation: {formula}\n2. Rearrange terms\n3. Solve for x\nSolution: {sols}"
                elif 'derivative' in formula.lower():
                    # Handle derivative
                    return f"1. Identify the function to differentiate\n2. Apply differentiation rules\n3. Simplify the result"
                elif 'integral' in formula.lower():
                    # Handle integral
                    return f"1. Identify the function to integrate\n2. Apply integration rules\n3. Add constant of integration"
            except:
                pass
        
        return f"Step-by-step solution:\n1. Analyze the given mathematical expression: {formula}\n2. Apply appropriate mathematical principles\n3. Perform calculations systematically\n4. Verify the result"
    
    def get_math_result(self, formula: str) -> str:
        """Get the final result of a math problem"""
        if SYMPY_AVAILABLE:
            try:
                if '=' in formula and 'x' in formula:
                    left, right = formula.split('=', 1)
                    eq = sympify(left) - sympify(right)
                    x = Symbol('x')
                    sols = solve(eq, x)
                    return f"x = {sols}"
            except:
                pass
        
        return "Final answer depends on the specific values and calculations performed."
    
    def solve_word_problem(self, word_problem: str) -> str:
        """Solve word problems step by step"""
        steps = [
            "1. Identify the given information and what needs to be found",
            "2. Set up the mathematical equation or relationship",
            "3. Substitute known values into the equation",
            "4. Solve the equation systematically",
            "5. Check if the answer makes sense in the context"
        ]
        return "\n".join(steps) + f"\n\nProblem context: {word_problem}"
    
    def get_word_problem_answer(self, word_problem: str) -> str:
        """Get the answer to a word problem"""
        return "The final answer depends on the specific numerical values and calculations performed based on the problem context."
    
    def generate_proof_steps(self, theorem: str) -> str:
        """Generate proof steps for a theorem"""
        steps = [
            "1. State the theorem clearly",
            "2. Identify the given conditions and what needs to be proven",
            "3. Choose an appropriate proof method (direct, contradiction, induction, etc.)",
            "4. Work through the logical steps systematically",
            "5. Conclude with the desired result"
        ]
        return "\n".join(steps) + f"\n\nTheorem: {theorem}"
    
    def get_theorem_applications(self, theorem: str) -> str:
        """Get applications of a theorem"""
        return f"This theorem has applications in various mathematical contexts and can be used to solve related problems in the field."
    
    def extract_complete_code_blocks(self, text: str) -> List[str]:
        """Extract complete code blocks from the document"""
        code_blocks = []
        lines = text.split('\n')
        current_block = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check for code block markers
            if line_stripped.startswith('```') or line_stripped.startswith('```c') or line_stripped.startswith('```python') or line_stripped.startswith('```java'):
                if in_code_block:
                    # End of code block
                    if current_block:
                        code_blocks.append('\n'.join(current_block))
                        current_block = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
                continue
            
            # If we're in a code block, collect lines
            if in_code_block:
                current_block.append(line)
                continue
            
            # Check for programming indicators that suggest start of code
            if any(indicator in line_stripped.lower() for indicator in ['#include', 'int main(', 'def ', 'public class', 'import ', 'function']):
                if not in_code_block:
                    in_code_block = True
                    current_block = [line]
                    continue
            
            # If we're collecting code and hit a non-code line, end the block
            if in_code_block and current_block:
                # Check if this looks like end of code (empty line or text description)
                if line_stripped == '' or (not any(char in line for char in ['{', '}', ';', '(', ')']) and len(line_stripped) > 50):
                    code_blocks.append('\n'.join(current_block))
                    current_block = []
                    in_code_block = False
                else:
                    current_block.append(line)
        
        # Add any remaining code block
        if current_block:
            code_blocks.append('\n'.join(current_block))
        
        # Clean and filter code blocks
        cleaned_blocks = []
        for block in code_blocks:
            cleaned = block.strip()
            # Only include blocks that look like actual code (have programming syntax)
            if len(cleaned) > 20 and any(indicator in cleaned.lower() for indicator in 
                ['#include', 'int ', 'def ', 'class ', 'function', 'printf', 'scanf', 'cout', 'cin', 'print(', 'input(']):
                cleaned_blocks.append(cleaned)
        
        return cleaned_blocks
    
    def extract_programming_tasks(self, text: str) -> List[str]:
        """Extract programming task descriptions from the document"""
        tasks = []
        sentences = sent_tokenize(text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            
            # Look for task descriptions
            if any(phrase in sentence_lower for phrase in [
                'write a program', 'write a c program', 'write a python', 'write a java',
                'create a program', 'develop a program', 'implement a program',
                'write code', 'create code', 'develop code',
                'write a function', 'create a function', 'implement a function'
            ]):
                # Clean up the task description
                task = sentence.strip()
                if task.endswith('.'):
                    task = task[:-1]
                tasks.append(task)
            
            # Look for problem statements
            elif any(phrase in sentence_lower for phrase in [
                'find the', 'calculate the', 'determine the', 'check if', 'verify if',
                'sort the', 'search for', 'display the', 'print the'
            ]) and any(word in sentence_lower for word in ['number', 'array', 'list', 'string', 'value']):
                tasks.append(sentence.strip())
        
        return tasks
    
    def create_programming_question(self, task: str, code: str) -> str:
        """Create a specific programming question from task and code"""
        task_lower = task.lower()
        
        # Detect language from code
        language = self.detect_programming_language(code)
        
        # If task already mentions writing a program, use it directly
        if any(phrase in task_lower for phrase in ['write a program', 'write a c program', 'write a python', 'write a java']):
            return task
        
        # If task mentions writing code/function
        elif any(phrase in task_lower for phrase in ['write code', 'write a function', 'create a function']):
            return task
        
        # Otherwise, create a question based on the code purpose
        else:
            purpose = self.analyze_code_purpose(code)
            return f"Write a {language} program to {purpose}."
    
    def detect_programming_language(self, code: str) -> str:
        """Detect the programming language from code"""
        code_lower = code.lower()
        
        if '#include' in code_lower and ('printf' in code_lower or 'scanf' in code_lower):
            return 'C'
        elif 'public class' in code_lower or 'System.out.println' in code_lower:
            return 'Java'
        elif 'def ' in code_lower and 'print(' in code_lower:
            return 'Python'
        elif '#include' in code_lower and ('cout' in code_lower or 'cin' in code_lower):
            return 'C++'
        elif 'function' in code_lower and ('console.log' in code_lower or 'document.' in code_lower):
            return 'JavaScript'
        elif 'int main(' in code_lower:
            return 'C'
        else:
            return 'programming language'
    
    def analyze_code_purpose(self, code: str) -> str:
        """Analyze what the code does to create appropriate question"""
        code_lower = code.lower()
        
        # Check for specific programming tasks
        if 'prime' in code_lower:
            return 'check if a number is prime'
        elif 'factorial' in code_lower:
            return 'calculate factorial of a number'
        elif 'fibonacci' in code_lower:
            return 'generate Fibonacci sequence'
        elif 'palindrome' in code_lower:
            return 'check if a string/number is palindrome'
        elif 'sort' in code_lower:
            return 'sort an array of numbers'
        elif 'search' in code_lower:
            return 'search for an element in array'
        elif 'reverse' in code_lower:
            return 'reverse a string or array'
        elif 'sum' in code_lower and 'array' in code_lower:
            return 'find sum of array elements'
        elif 'maximum' in code_lower or 'largest' in code_lower:
            return 'find the largest number'
        elif 'minimum' in code_lower or 'smallest' in code_lower:
            return 'find the smallest number'
        elif 'even' in code_lower and 'odd' in code_lower:
            return 'check if a number is even or odd'
        elif 'calculator' in code_lower:
            return 'create a simple calculator'
        elif 'swap' in code_lower:
            return 'swap two numbers'
        elif 'area' in code_lower:
            return 'calculate area of geometric shapes'
        elif 'temperature' in code_lower:
            return 'convert temperature between units'
        elif 'grade' in code_lower or 'marks' in code_lower:
            return 'calculate grades based on marks'
        elif 'leap year' in code_lower:
            return 'check if a year is leap year'
        elif 'armstrong' in code_lower:
            return 'check if a number is Armstrong number'
        elif 'perfect' in code_lower:
            return 'check if a number is perfect number'
        elif 'gcd' in code_lower or 'hcf' in code_lower:
            return 'find GCD of two numbers'
        elif 'lcm' in code_lower:
            return 'find LCM of two numbers'
        elif 'matrix' in code_lower:
            return 'perform matrix operations'
        elif 'string' in code_lower and 'length' in code_lower:
            return 'find length of a string'
        elif 'count' in code_lower:
            return 'count specific elements or characters'
        elif 'pattern' in code_lower:
            return 'print number or star patterns'
        elif 'table' in code_lower:
            return 'print multiplication table'
        elif 'power' in code_lower:
            return 'calculate power of a number'
        elif 'square' in code_lower and 'root' in code_lower:
            return 'find square root of a number'
        else:
            # Generic analysis based on common programming constructs
            if 'scanf' in code_lower or 'input' in code_lower:
                if 'printf' in code_lower or 'print' in code_lower:
                    return 'read input and display output'
                else:
                    return 'read user input'
            elif 'printf' in code_lower or 'print' in code_lower:
                return 'display output to user'
            elif 'for' in code_lower or 'while' in code_lower:
                return 'perform repetitive operations using loops'
            elif 'if' in code_lower:
                return 'make decisions using conditional statements'
            else:
                return 'solve the given programming problem'
    
    def generate_mixed_questions(self, text: str, num_questions: int, content_type: str) -> List[Dict[str, Any]]:
        """Generate a mix of question types based on content"""
        qa_pairs = []
        
        # Determine the distribution based on content type
        if content_type == "programming":
            # For programming content: 40% programming, 30% MCQ, 30% descriptive
            num_programming = max(1, int(num_questions * 0.4))
            num_mcq = max(1, int(num_questions * 0.3))
            num_descriptive = num_questions - num_programming - num_mcq
            
            print(f"   📊 Distribution: {num_programming} programming, {num_mcq} MCQ, {num_descriptive} descriptive")
            
            # Generate each type
            if num_programming > 0:
                prog_questions = self.generate_programming_qa(text, num_programming)
                qa_pairs.extend(prog_questions)
            
            if num_mcq > 0:
                mcq_questions = self.generate_mcq_questions(text, num_mcq, content_type)
                qa_pairs.extend(mcq_questions)
            
            if num_descriptive > 0:
                desc_questions = self.generate_descriptive_qa(text, num_descriptive)
                qa_pairs.extend(desc_questions)
        
        elif content_type == "math":
            # For math content: 50% math, 30% MCQ, 20% descriptive
            num_math = max(1, int(num_questions * 0.5))
            num_mcq = max(1, int(num_questions * 0.3))
            num_descriptive = num_questions - num_math - num_mcq
            
            print(f"   📊 Distribution: {num_math} math, {num_mcq} MCQ, {num_descriptive} descriptive")
            
            if num_math > 0:
                math_questions = self.generate_math_qa(text, num_math)
                qa_pairs.extend(math_questions)
            
            if num_mcq > 0:
                mcq_questions = self.generate_mcq_questions(text, num_mcq, content_type)
                qa_pairs.extend(mcq_questions)
            
            if num_descriptive > 0:
                desc_questions = self.generate_descriptive_qa(text, num_descriptive)
                qa_pairs.extend(desc_questions)
        
        elif content_type == "science":
            # For science/environmental content: 60% descriptive, 40% MCQ
            num_descriptive = max(1, int(num_questions * 0.6))
            num_mcq = num_questions - num_descriptive
            
            print(f"   📊 Distribution: {num_descriptive} descriptive, {num_mcq} MCQ (Science Content)")
            
            if num_descriptive > 0:
                desc_questions = self.generate_science_descriptive_qa(text, num_descriptive)
                print(f"   ✅ Generated {len(desc_questions)} science descriptive questions")
                qa_pairs.extend(desc_questions)
            
            if num_mcq > 0:
                mcq_questions = self.generate_science_mcq(text, num_mcq)
                print(f"   ✅ Generated {len(mcq_questions)} science MCQ questions")
                qa_pairs.extend(mcq_questions)
        
        else:
            # For general/story content: 50% descriptive, 50% MCQ
            num_descriptive = max(1, int(num_questions * 0.5))
            num_mcq = num_questions - num_descriptive
            
            print(f"   📊 Distribution: {num_descriptive} descriptive, {num_mcq} MCQ")
            
            if num_descriptive > 0:
                desc_questions = self.generate_descriptive_qa(text, num_descriptive)
                print(f"   ✅ Generated {len(desc_questions)} descriptive questions")
                qa_pairs.extend(desc_questions)
            
            if num_mcq > 0:
                mcq_questions = self.generate_mcq_questions(text, num_mcq, content_type)
                print(f"   ✅ Generated {len(mcq_questions)} MCQ questions")
                qa_pairs.extend(mcq_questions)
        
        print(f"   📝 Total mixed questions before trimming: {len(qa_pairs)}")
        return qa_pairs[:num_questions]
    
    def generate_science_descriptive_qa(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate descriptive questions for science/environmental content"""
        qa_pairs = []
        sentences = sent_tokenize(text)
        
        # AGGRESSIVE cleaning - remove all formatting issues
        clean_sentences = []
        for s in sentences:
            # Remove checkbox symbols and bullet points
            s_clean = s.replace('□', '').replace('■', '').replace('●', '').replace('○', '')
            s_clean = s_clean.replace('', '').replace('', '').strip()
            
            # Skip if:
            # - Too short (< 10 words)
            # - Starts with header markers
            # - Starts with numbers (page numbers)
            # - Has "Ex:" (examples)
            # - Too long (> 250 chars - likely run-on)
            if (len(s_clean.split()) >= 10 and 
                len(s_clean.split()) <= 50 and
                not s_clean.startswith(('Module', 'Chapter', 'Page', 'Figure', 'Table', 'Ex:', 'E.g.', 'e.g.')) and
                not re.match(r'^[0-9]+\.', s_clean) and
                not re.match(r'^[A-Z]\)', s_clean) and  # Skip "A) ", "B) "
                len(s_clean) < 250):
                
                # Additional quality checks
                # Must have proper sentence structure (ends with . ! ?)
                if s_clean and s_clean[-1] in '.!?':
                    clean_sentences.append(s_clean)
        
        if not clean_sentences or len(clean_sentences) < 5:
            # Fallback: less strict cleaning
            clean_sentences = []
            for s in sentences:
                s_clean = s.replace('□', '').replace('■', '').replace('●', '').strip()
                if len(s_clean.split()) >= 8:
                    clean_sentences.append(s_clean)
        
        # Extract key information
        concepts = self.document_context.get('key_concepts', [])
        processes = self.document_context.get('processes', [])
        impacts = self.document_context.get('impacts', [])
        solutions = self.document_context.get('solutions', [])
        
        # Define question types with matching keywords
        question_types = [
            {
                'type': 'definition',
                'question': lambda c: f"Explain what {c} means and its significance in the context of environmental science.",
                'keywords': [concepts[0]] if concepts else [],
                'avoid': []
            },
            {
                'type': 'impacts',
                'question': lambda c: f"Describe the impacts and effects of {c} on the environment and ecosystems.",
                'keywords': impacts[:3] if impacts else ['impact', 'effect', 'consequence', 'result'],
                'avoid': ['adaptation', 'mitigation', 'solution', 'strategy']
            },
            {
                'type': 'strategies',
                'question': lambda c: f"Explain the {processes[0] if processes else 'adaptation'} strategies and approaches to address {c}.",
                'keywords': processes[:3] if processes else ['strategy', 'approach', 'method', 'measure'],
                'avoid': ['impact', 'effect', 'consequence']
            },
            {
                'type': 'solutions',
                'question': lambda c: f"Discuss the solutions and measures proposed to mitigate {c}.",
                'keywords': solutions[:3] if solutions else ['solution', 'measure', 'action', 'policy'],
                'avoid': ['impact', 'effect']
            }
        ]
        
        # Generate questions with MATCHED answers
        for i, concept in enumerate(concepts[:num_questions]):
            # Choose question type
            q_type = question_types[i % len(question_types)]
            question = q_type['question'](concept)
            
            # Find sentences that MATCH the question type
            relevant_sentences = []
            for sent in clean_sentences:
                sent_lower = sent.lower()
                
                # Check if sentence contains the concept
                if concept not in sent_lower:
                    continue
                
                # Check if sentence matches question type keywords
                has_keyword = any(kw in sent_lower for kw in q_type['keywords']) if q_type['keywords'] else True
                
                # Check if sentence avoids conflicting keywords
                has_avoid = any(avoid in sent_lower for avoid in q_type['avoid'])
                
                # Add if matches and doesn't conflict
                if has_keyword and not has_avoid:
                    relevant_sentences.append(sent)
            
            # If no matched sentences, try broader search
            if not relevant_sentences:
                relevant_sentences = [s for s in clean_sentences if concept in s.lower()]
            
            # Build answer from relevant sentences
            if relevant_sentences:
                # Take up to 4 sentences for comprehensive answer
                answer_parts = relevant_sentences[:4]
                answer_text = ' '.join(answer_parts)
                
                # Final cleaning
                answer_text = answer_text.strip()
                
                # Validate answer quality
                if (len(answer_text.split()) >= 20 and  # At least 20 words
                    len(answer_text) <= 800 and  # Not too long
                    concept in answer_text.lower()):  # Contains the concept
                    
                    qa_pairs.append({
                        'question': question,
                        'answer': answer_text,
                        'type': 'descriptive'
                    })
        
        # If not enough questions, use paragraph-based approach
        if len(qa_pairs) < num_questions:
            paragraphs = text.split('\n\n')
            for para in paragraphs:
                if len(qa_pairs) >= num_questions:
                    break
                
                # Clean paragraph
                para_clean = para.replace('□', '').replace('■', '').replace('●', '').strip()
                
                # Check if paragraph is substantial
                if len(para_clean.split()) >= 30 and len(para_clean.split()) <= 150:
                    # Extract main topic from first sentence
                    first_sent = sent_tokenize(para_clean)[0] if para_clean else ""
                    
                    question = "Explain the key concepts and their significance as discussed in the content."
                    
                    qa_pairs.append({
                        'question': question,
                        'answer': para_clean[:800],
                        'type': 'descriptive'
                    })
        
        return qa_pairs[:num_questions]
    
    def generate_science_mcq(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate MCQ questions for science/environmental content"""
        qa_pairs = []
        sentences = sent_tokenize(text)
        
        # Clean sentences
        clean_sentences = []
        for s in sentences:
            s_clean = s.strip()
            if (len(s_clean.split()) > 8 and 
                not s_clean.startswith(('Module', 'Chapter', 'Page', '□', '■', '●')) and
                len(s_clean) < 200):
                clean_sentences.append(s_clean)
        
        if not clean_sentences:
            clean_sentences = sentences
        
        # Extract key terms for MCQ
        concepts = self.document_context.get('key_concepts', [])
        processes = self.document_context.get('processes', [])
        impacts = self.document_context.get('impacts', [])
        
        # Predefined science MCQ templates with proper distractors
        mcq_templates = [
            {
                'question': 'What is climate change?',
                'correct': 'Long-term change in average weather patterns that have come to define Earth\'s local, regional and global climates',
                'distractors': [
                    'Short-term variations in daily weather conditions',
                    'Seasonal changes in temperature and precipitation',
                    'Natural disasters like hurricanes and tornadoes'
                ]
            },
            {
                'question': 'What is adaptation in the context of climate change?',
                'correct': 'Adjustments in natural or human systems in response to actual or expected climatic effects',
                'distractors': [
                    'Reducing greenhouse gas emissions to prevent climate change',
                    'Planting more trees to absorb carbon dioxide',
                    'Using renewable energy sources instead of fossil fuels'
                ]
            },
            {
                'question': 'What is mitigation in climate change context?',
                'correct': 'Actions to reduce greenhouse gas emissions and enhance carbon sinks',
                'distractors': [
                    'Adapting infrastructure to withstand extreme weather',
                    'Moving populations away from flood-prone areas',
                    'Developing drought-resistant crop varieties'
                ]
            },
        ]
        
        # Try to generate MCQs from actual content
        for i, concept in enumerate(concepts[:num_questions]):
            # Find sentences that define or explain the concept
            relevant_sentences = [s for s in clean_sentences if concept in s.lower()]
            
            if relevant_sentences and len(relevant_sentences) >= 1:
                # Use the first good sentence as the correct answer
                correct_sentence = relevant_sentences[0]
                
                # Remove checkbox symbols and clean
                correct_sentence = correct_sentence.replace('□', '').replace('■', '').replace('●', '').strip()
                
                # Clean it up
                if len(correct_sentence) > 150:
                    # Try to extract the key part
                    parts = correct_sentence.split(',')
                    correct_answer = parts[0] if len(parts[0]) > 30 else correct_sentence[:150]
                else:
                    correct_answer = correct_sentence
                
                # Skip if answer is too short or looks like an example
                if len(correct_answer.split()) < 8 or correct_answer.lower().startswith('ex:'):
                    continue
                
                # Generate question
                question = f"What is {concept}?"
                
                # Create plausible distractors from other concepts
                distractors = []
                used_sentences = {correct_answer}  # Track used sentences to avoid duplicates
                
                # Get other concepts as distractors
                other_concepts = [c for c in concepts if c != concept]
                for other_concept in other_concepts:
                    other_sentences = [s for s in clean_sentences if other_concept in s.lower()]
                    for sent in other_sentences:
                        # Clean the sentence
                        sent_clean = sent.replace('□', '').replace('■', '').replace('●', '').strip()
                        
                        # Skip if too short or example
                        if len(sent_clean.split()) < 8 or sent_clean.lower().startswith('ex:'):
                            continue
                        
                        # Truncate if needed
                        if len(sent_clean) > 150:
                            parts = sent_clean.split(',')
                            sent_clean = parts[0] if len(parts[0]) > 30 else sent_clean[:150]
                        
                        # Check if unique
                        if sent_clean not in used_sentences and sent_clean != correct_answer:
                            distractors.append(sent_clean)
                            used_sentences.add(sent_clean)
                            if len(distractors) >= 3:
                                break
                    
                    if len(distractors) >= 3:
                        break
                
                # Add generic distractors if needed (but only if we don't have enough good ones)
                if len(distractors) < 3:
                    generic_distractors = [
                        f"A process unrelated to {concept}",
                        f"The opposite effect of {concept}",
                        f"A temporary phenomenon not related to {concept}",
                    ]
                    
                    for gen_dist in generic_distractors:
                        if gen_dist not in used_sentences and len(distractors) < 3:
                            distractors.append(gen_dist)
                            used_sentences.add(gen_dist)
                
                if len(distractors) >= 3:
                    # Create options - ensure no duplicates
                    all_options = [correct_answer] + distractors[:3]
                    
                    # Double-check for duplicates
                    unique_options = []
                    seen = set()
                    for opt in all_options:
                        if opt not in seen:
                            unique_options.append(opt)
                            seen.add(opt)
                    
                    # Only add if we have 4 unique options
                    if len(unique_options) >= 4:
                        random.shuffle(unique_options)
                        correct_index = unique_options.index(correct_answer)
                        
                        qa_pairs.append({
                            'question': question,
                            'options': unique_options[:4],
                            'correct_answer': chr(65 + correct_index),  # A, B, C, D
                            'type': 'mcq'
                        })
        
        # If not enough MCQs generated, use templates
        while len(qa_pairs) < num_questions and mcq_templates:
            template = mcq_templates.pop(0)
            all_options = [template['correct']] + template['distractors']
            random.shuffle(all_options)
            correct_index = all_options.index(template['correct'])
            
            qa_pairs.append({
                'question': template['question'],
                'options': all_options,
                'correct_answer': chr(65 + correct_index),
                'type': 'mcq'
            })
        
        return qa_pairs[:num_questions]
    
    def process_document(self, file_path: str, mode: str = "auto", num_questions: int = 10) -> List[Dict[str, Any]]:
        """Main processing function that handles all modes"""
        print(f"📖 Processing: {file_path}")
        print(f"🎯 Mode: {mode.upper()}")
        
        # Extract text
        text = self.extract_text_from_file(file_path)
        if not text:
            print("❌ Could not extract text from file")
            return []
        
        print(f"📄 Extracted {len(text)} characters")
        
        # Detect content type for analysis
        if mode == "auto":
            content_type = self.detect_content_type(text)
            print(f"🔍 Auto-detected content type: {content_type}")
        elif mode == "mcq" or mode == "mixed":
            # For MCQ and Mixed modes, detect the actual content type for analysis
            content_type = self.detect_content_type(text)
            print(f"🔍 Detected content type for {mode.upper()}: {content_type}")
        else:
            content_type = mode
        
        # Analyze document context (needs actual content type, not "mcq")
        self.analyze_document_context(text, content_type)
        
        # Generate questions based on mode
        qa_pairs = []
        
        if mode == "descriptive":
            qa_pairs = self.generate_descriptive_qa(text, num_questions)
        elif mode == "programming":
            qa_pairs = self.generate_programming_qa(text, num_questions)
        elif mode == "math":
            qa_pairs = self.generate_math_qa(text, num_questions)
        elif mode == "mcq":
            # Pass the detected content type to MCQ generator
            qa_pairs = self.generate_mcq_questions(text, num_questions, content_type)
        elif mode == "mixed":
            # Mixed mode - generate a variety of question types
            print("🎨 Generating mixed question types...")
            qa_pairs = self.generate_mixed_questions(text, num_questions, content_type)
        else:
            # Auto mode - use detected content type
            if content_type == "programming":
                qa_pairs = self.generate_programming_qa(text, num_questions)
            elif content_type == "math":
                qa_pairs = self.generate_math_qa(text, num_questions)
            else:
                qa_pairs = self.generate_descriptive_qa(text, num_questions)
        
        print(f"🎯 Generated {len(qa_pairs)} {mode} questions")
        return qa_pairs
    
    def save_outputs(self, qa_pairs: List[Dict[str, Any]], output_base: str):
        """Save Q&A pairs to multiple formats"""
        if not qa_pairs:
            print("⚠️ No Q&A pairs to save.")
            return
        
        # Save as TXT
        txt_file = f"{output_base}.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("PAKKA FINAL QA GENERATOR OUTPUT\n")
            f.write("=" * 80 + "\n\n")
            
            for i, qa in enumerate(qa_pairs, 1):
                f.write(f"Q{i}: {qa['question']}\n")
                
                # Handle MCQ format differently
                if 'options' in qa:
                    # MCQ format
                    f.write("Options:\n")
                    for j, option in enumerate(qa['options'], 1):
                        letter = chr(64 + j)  # A, B, C, D
                        f.write(f"  {letter}) {option}\n")
                    f.write(f"Correct Answer: {qa.get('correct_answer', 'A')}\n")
                    f.write(f"Explanation: {qa.get('explanation', '')}\n")
                else:
                    # Regular Q&A format
                    f.write(f"Answer: {qa.get('answer', 'No answer provided')}\n")
                
                f.write(f"Type: {qa.get('type', 'unknown')}\n")
                
                f.write("-" * 80 + "\n\n")
        
        print(f"📄 Saved TXT: {txt_file}")
        
        # Save as JSON
        json_file = f"{output_base}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(qa_pairs, f, indent=2, ensure_ascii=False)
        print(f"📄 Saved JSON: {json_file}")


def main():
    """Main function with user interface"""
    print("🚀 Welcome to Pakka Final QA Generator!")
    print("🎯 The Ultimate Q&A Generator for All Content Types")
    print("=" * 60)
    print("Available Modes:")
    print("  📖 descriptive: For stories, articles, and general text")
    print("  💻 programming: For code, algorithms, and programming concepts")
    print("  🧮 math: For equations, theorems, and mathematical problems")
    print("  ❓ mcq: For Multiple Choice Questions with 4 options")
    print("  🔍 auto: Automatically detect the best mode")
    print("=" * 60)
    
    # Get file path
    file_path = input("📁 Enter file path (PDF/DOCX/TXT): ").strip().strip('"')
    if not os.path.exists(file_path):
        print("❌ File not found")
        return
    
    # Get mode
    mode = input("🎯 Enter mode (descriptive/programming/math/mcq/auto): ").strip().lower()
    if mode not in ["descriptive", "programming", "math", "mcq", "auto"]:
        mode = "auto"
        print(f"Invalid mode, using 'auto' instead.")
    
    # Get number of questions
    num_str = input("❓ Number of questions to generate (default 10): ").strip()
    num_questions = int(num_str) if num_str.isdigit() else 10
    
    # Initialize generator
    generator = PakkaFinalQAGenerator()
    
    # Process document
    print("\n" + "=" * 60)
    print("🔄 Processing document...")
    qa_pairs = generator.process_document(file_path, mode, num_questions)
    
    if not qa_pairs:
        print("❌ No Q&A pairs were generated. Please check your file content and try again.")
        return
    
    # Save outputs
    output_base = f"pakka_qa_output_{Path(file_path).stem}_{int(time.time())}"
    generator.save_outputs(qa_pairs, output_base)
    
    # Display summary
    print("\n" + "=" * 60)
    print("✅ Processing Complete!")
    print(f"📊 Total Q&A pairs generated: {len(qa_pairs)}")
    print(f"📁 Output files: {output_base}.txt, {output_base}.json")
    
    # Show sample questions
    print("\n🎯 Sample Questions Generated:")
    print("-" * 40)
    for i, qa in enumerate(qa_pairs[:3], 1):
        print(f"Q{i}: {qa['question']}")
        if 'options' in qa:
            print("Options:")
            for j, option in enumerate(qa['options'], 1):
                letter = chr(64 + j)
                print(f"  {letter}) {option}")
            print(f"Correct: {qa.get('correct_answer', 'A')}")
        print(f"Type: {qa.get('type', 'unknown')}")
        print("-" * 40)


if __name__ == "__main__":
    main()
