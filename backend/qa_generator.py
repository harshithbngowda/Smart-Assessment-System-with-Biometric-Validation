"""
Q&A Generator Module
Integrates with pakkafinalqa.py for question generation
"""

import os
import sys
import json
from pathlib import Path
import tempfile
from typing import Optional

# Import from modules directory
try:
    # Set UTF-8 encoding for Windows
    import sys
    import os
    if sys.platform == "win32":
        os.environ["PYTHONIOENCODING"] = "utf-8"
    
    try:
        from modules.pakkafinalqa import PakkaFinalQAGenerator
        print("✅ Advanced Q&A generator loaded successfully (with ML)")
    except Exception as e:
        print(f"⚠️ ML libraries unavailable ({type(e).__name__}), using simplified Q&A generator")
        from modules.pakkafinalqa_simplified import PakkaFinalQAGenerator
        print("✅ Simplified Q&A generator loaded (NLTK-based)")
except Exception as e:
    print(f"⚠️ Warning: Q&A generator not available ({type(e).__name__}). Using basic fallback.")
    PakkaFinalQAGenerator = None

# Handwriting OCR integration
from handwriting_converter import convert_image_to_text

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}

# Optional Gemini QG support
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

def _use_gemini() -> bool:
    return GEMINI_AVAILABLE and os.environ.get("USE_GEMINI_QG") == "1"

def generate_questions_with_gemini(text: str, num_questions: int = 10, mode: str = "auto"):
    """Generate high-quality questions and answers grounded in provided text using Gemini.
    Returns list of {question, type, answer, options}.
    """
    if not text or len(text.strip()) < 50:
        return []
    try:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("HANDWRITING_API_KEY")
        if not api_key:
            return []
        genai.configure(api_key=api_key)

        # Prefer a fast JSON-capable model
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={
                "temperature": 0.3,
                "top_p": 0.9,
                "response_mime_type": "application/json",
            },
        )

        schema_hint = {
            "instructions": "Return an array named items of question objects. Each object must include: question (string), type (one of mcq, descriptive, short, programming, math), options (array of 4 strings when type is mcq, else []), correct_answer (string, strictly grounded in the provided text). Do not invent facts not present in the text.",
            "num_questions": num_questions,
            "mode": mode,
        }

        prompt = f"""
You are an expert exam-setter. Read the STUDY_CONTENT below carefully and generate exactly {num_questions} high-quality exam questions WITH detailed answers.

IMPORTANT INSTRUCTIONS:
1. Analyze the SUBJECT and TYPE of content (technical, scientific, literary, theoretical, etc.)
2. Generate questions appropriate to the subject matter
3. Provide COMPLETE, DETAILED answers based strictly on the information provided
4. Questions should test understanding of KEY CONCEPTS in the content

QUESTION TYPES:
- MCQ: Multiple choice with 4 options (for factual/conceptual questions)
- Descriptive: Detailed explanation questions (5-10 marks) - can be:
  * Technical explanations (programming, algorithms, systems)
  * Scientific concepts (physics, chemistry, biology formulas/theories)
  * Theoretical concepts (definitions, processes, strategies)
  * Literary analysis (only if content is a story/passage/essay)
  * Problem-solving (step-by-step solutions)
- Short: Brief answer questions (2-3 marks)
- Programming: Code-based questions with code solutions
- Math: Mathematical problems with step-by-step solutions

RULES:
1. Identify the subject domain from the content (e.g., programming, physics, climate science, literature)
2. Generate questions specific to that domain
3. For TECHNICAL content (code, algorithms, formulas):
   - Ask about implementations, logic, time complexity, applications
   - Provide code/formula-based answers
4. For SCIENTIFIC content (physics, chemistry, biology):
   - Ask about concepts, laws, reactions, processes
   - Include formulas, equations, diagrams descriptions
5. For THEORETICAL content (strategies, concepts, definitions):
   - Ask about explanations, comparisons, applications
   - Provide structured, detailed answers
6. For LITERARY content (stories, passages, essays):
   - Ask about themes, characters, literary devices
   - Provide analytical answers
7. DO NOT assume content is literary unless it clearly contains a story/passage
8. Match question difficulty to content complexity

STUDY_CONTENT:
{text[:18000]}

Analyze the subject domain and generate {num_questions} questions with complete, detailed answers appropriate to the content type.
"""

        res = model.generate_content([
            {"text": json.dumps(schema_hint)},
            {"text": prompt},
        ])

        raw = res.text or ""
        # Some SDK versions still wrap JSON in fences; strip them
        data_str = raw.strip()
        if data_str.startswith("```"):
            data_str = data_str.strip("`\n").split('\n', 1)[-1]
        parsed = json.loads(data_str)
        items = parsed.get("items") if isinstance(parsed, dict) else parsed
        if not isinstance(items, list):
            return []

        qa_pairs = []
        for it in items[:num_questions]:
            q = (it.get("question") or "").strip()
            t = (it.get("type") or "descriptive").strip().lower()
            ans = (it.get("correct_answer") or "").strip()
            opts = it.get("options") or []
            qa_pairs.append({
                "question": q,
                "type": t,
                "answer": ans,
                "options": opts,
            })
        return qa_pairs
    except Exception as e:
        print(f"Gemini QG failed: {e}")
        return []

def _extract_text_any(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext in IMAGE_EXTS:
        try:
            print(f"[OCR] Extracting text from image: {file_path}")
            api_key = os.environ.get("HANDWRITING_API_KEY", "")
            text = convert_image_to_text(file_path, api_key)
            print(f"[OCR] Extracted {len(text) if text else 0} characters")
            if text:
                print(f"[OCR] Preview: {text[:200]}...")
            return text or ""
        except Exception as e:
            print(f"[OCR] Error: {e}")
            return ""
    if ext == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""
    if ext == ".docx":
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            return ""
    if ext == ".pdf":
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text() or ""
                    text += t + "\n"
            text = text.strip()
        except Exception:
            text = ""
        if len(text) >= 50:
            return text
        # OCR scanned PDFs if text too short
        try:
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                ocr_text = []
                max_pages = int(os.environ.get("MAX_OCR_PAGES", "5"))
                ocr_dpi = int(os.environ.get("OCR_DPI", "130"))
                ocr_max_w = int(os.environ.get("OCR_MAX_WIDTH", "1200"))
                for page in doc:
                    if len(ocr_text) >= max_pages:
                        break
                    pix = page.get_pixmap(dpi=ocr_dpi)
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
                        pix.save(tmp.name)
                        # Optional downscale for speed if very large
                        try:
                            from PIL import Image as _PIL_Image
                            im = _PIL_Image.open(tmp.name)
                            if im.width > ocr_max_w:
                                ratio = ocr_max_w / float(im.width)
                                new_h = max(1, int(im.height * ratio))
                                im = im.resize((ocr_max_w, new_h))
                                im.save(tmp.name, format="PNG")
                        except Exception:
                            pass
                        api_key = os.environ.get("HANDWRITING_API_KEY", "")
                        ocr_text.append(convert_image_to_text(tmp.name, api_key) or "")
                return "\n".join(ocr_text).strip()
            except ImportError:
                pass
        except Exception:
            pass
        return text or ""
    # Unknown file: best effort empty
    return ""

def generate_questions_from_file(file_path, num_questions=10, mode="auto"):
    """Generate questions from uploaded file"""
    try:
        # Extract text once for Gemini and for better fallback
        text = _extract_text_any(file_path)

        # First preference: Gemini (if available + API key)
        if _use_gemini():
            gem_qa = generate_questions_with_gemini(text, num_questions, mode)
            if gem_qa:
                questions = []
                for qa in gem_qa:
                    question_data = {
                        'question_text': qa['question'],
                        'question_type': qa.get('type', 'descriptive'),
                        'marks': 10 if qa.get('type', '').startswith('descriptive') else 1,
                        'correct_answer': qa.get('answer', '') or qa.get('correct_answer', ''),
                        'options': qa.get('options', []) or None
                    }
                    questions.append(question_data)
                return questions

        # Second: Pakka generator (advanced or simplified)
        if PakkaFinalQAGenerator:
            ext = Path(file_path).suffix.lower()
            use_path = file_path
            if (ext in IMAGE_EXTS or ext == ".pdf") and text and len(text) > 50:
                tmp_txt = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
                try:
                    with open(tmp_txt.name, "w", encoding="utf-8") as f:
                        f.write(text)
                    use_path = tmp_txt.name
                finally:
                    tmp_keep = tmp_txt.name
            generator = PakkaFinalQAGenerator()
            qa_pairs = generator.process_document(use_path, mode, num_questions)
            
            # Convert to our format
            questions = []
            for i, qa in enumerate(qa_pairs):
                # Get answer - handle both 'answer' and 'correct_answer' keys
                answer = qa.get('answer', '') or qa.get('correct_answer', '')
                
                # Debug: Print answer details
                print(f"   Q{i+1}: {qa.get('type', 'unknown')} - Answer length: {len(answer)} chars")
                if len(answer) < 50:
                    print(f"   ⚠️ Short answer: {answer[:100]}")
                
                question_data = {
                    'question_text': qa['question'],
                    'question_type': determine_question_type(qa),
                    'marks': 10 if qa.get('type', '').startswith('descriptive') else 1,
                    'correct_answer': answer,
                    'options': qa.get('options', []) if 'options' in qa else None
                }
                questions.append(question_data)
            
            return questions
        else:
            return generate_fallback_questions(file_path, num_questions)
            
    except Exception as e:
        print(f"Error generating questions: {e}")
        return generate_fallback_questions(file_path, num_questions)

def generate_questions_from_text(text, num_questions=10, mode="auto"):
    """Generate questions from text input"""
    try:
        print(f"📝 Generating questions from text (length: {len(text)}, mode: {mode})")
        
        # Prefer Gemini when available
        if _use_gemini():
            print("🤖 Using Gemini for question generation...")
            gem_qa = generate_questions_with_gemini(text, num_questions, mode)
            if gem_qa:
                print(f"✅ Gemini generated {len(gem_qa)} questions")
                questions = []
                for qa in gem_qa:
                    question_data = {
                        'question_text': qa['question'],
                        'question_type': qa.get('type', 'descriptive'),
                        'marks': 10 if qa.get('type', '').startswith('descriptive') else 1,
                        'correct_answer': qa.get('answer', '') or qa.get('correct_answer', ''),
                        'options': qa.get('options', []) or None
                    }
                    questions.append(question_data)
                return questions

        if PakkaFinalQAGenerator:
            # Use proper temporary file with absolute path
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(text)
                temp_file_path = tmp_file.name
            
            print(f"📄 Saved text to temporary file: {temp_file_path}")
            
            try:
                generator = PakkaFinalQAGenerator()
                qa_pairs = generator.process_document(temp_file_path, mode, num_questions)
                print(f"✅ Generated {len(qa_pairs)} questions from text")
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    print(f"🗑️ Cleaned up temporary file")
            
            # Convert to our format
            questions = []
            for i, qa in enumerate(qa_pairs):
                # Get answer - handle both 'answer' and 'correct_answer' keys
                answer = qa.get('answer', '') or qa.get('correct_answer', '')
                
                # Debug: Print answer length
                print(f"   Q{i+1}: {qa.get('type', 'unknown')} - Answer length: {len(answer)} chars")
                if len(answer) < 50:
                    print(f"   ⚠️ Short answer detected: {answer[:100]}")
                
                question_data = {
                    'question_text': qa['question'],
                    'question_type': determine_question_type(qa),
                    'marks': 10 if qa.get('type', '').startswith('descriptive') else 1,
                    'correct_answer': answer,
                    'options': qa.get('options', []) if 'options' in qa else None
                }
                questions.append(question_data)
            
            return questions
        else:
            # Fallback generator
            return generate_fallback_questions_from_text(text, num_questions)
            
    except Exception as e:
        print(f"Error generating questions from text: {e}")
        return generate_fallback_questions_from_text(text, num_questions)

def determine_question_type(qa_data):
    """Determine question type from QA data"""
    if 'options' in qa_data and qa_data['options']:
        return 'mcq'
    elif qa_data.get('type', '').startswith('programming'):
        return 'programming'
    elif qa_data.get('type', '').startswith('math'):
        return 'math'
    else:
        return 'descriptive'

def generate_fallback_questions(file_path, num_questions=10):
    """Fallback question generator when pakkafinalqa is not available"""
    questions = []
    
    # Extract text robustly (includes OCR for images/scanned PDFs)
    content = _extract_text_any(file_path)
    if not content or len(content.strip()) < 10:
        content = "Sample content for question generation."
    
    # Generate simple questions
    raw_sents = [s.strip() for s in content.replace('\n', ' ').split('.') if s.strip()]
    sentences = raw_sents[:max(1, num_questions)]
    
    for i, sentence in enumerate(sentences):
        if sentence.strip():
            # Create a clearer prompt and a grounded answer using the sentence itself
            q = f"What does the following mean in the context of the passage: \"{sentence.strip()}\"?"
            a = sentence.strip()
            questions.append({
                'question_text': q,
                'question_type': 'descriptive',
                'marks': 10,
                'correct_answer': a,
                'options': None
            })
    
    # Fill remaining with generic questions
    while len(questions) < num_questions:
        questions.append({
            'question_text': f"Based on the passage, describe the key idea presented in the previous lines.",
            'question_type': 'descriptive',
            'marks': 10,
            'correct_answer': "The key idea should be taken directly from the surrounding lines of the passage.",
            'options': None
        })
    
    return questions[:num_questions]

def generate_fallback_questions_from_text(text, num_questions=10):
    """Fallback question generator for text input"""
    questions = []
    
    # Split text into sentences
    raw_sents = [s.strip() for s in text.replace('\n', ' ').split('.') if s.strip()]
    sentences = raw_sents[:max(1, num_questions)]
    
    for i, sentence in enumerate(sentences):
        if sentence.strip():
            q = f"What does the following mean in the context of the passage: \"{sentence.strip()}\"?"
            a = sentence.strip()
            questions.append({
                'question_text': q,
                'question_type': 'descriptive',
                'marks': 10,
                'correct_answer': a,
                'options': None
            })
    
    # Fill remaining with generic questions
    while len(questions) < num_questions:
        questions.append({
            'question_text': f"Based on the passage, describe the key idea presented in the previous lines.",
            'question_type': 'descriptive',
            'marks': 10,
            'correct_answer': "The key idea should be taken directly from the surrounding lines of the passage.",
            'options': None
        })
    
    return questions[:num_questions]