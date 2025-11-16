"""
Handwritten Assessment Evaluator
Extracts handwritten Q&A and evaluates against subject content using Gemini Vision API
"""

import os
import base64
import json
from typing import Dict, List, Tuple
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import io

class HandwrittenEvaluator:
    """
    Evaluates handwritten answers against subject content
    Uses Gemini Vision for handwriting recognition and Gemini Pro for evaluation
    """
    
    def __init__(self, api_key: str = None):
        """Initialize with Gemini API key"""
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("Gemini API key required")
        
        genai.configure(api_key=api_key)
        # Use gemini-2.5-flash (same as handwriting converter)
        self.vision_model = genai.GenerativeModel('gemini-2.5-flash')
        self.text_model = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Handwritten Evaluator initialized with Gemini Vision API")
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """Extract text from PDF, DOCX, or TXT file"""
        try:
            if file_type == 'pdf':
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
            
            elif file_type == 'docx':
                doc = Document(file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                return text.strip()
            
            elif file_type == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
    
    def extract_handwritten_qa(self, image_path: str) -> Dict:
        """
        Extract questions and answers from handwritten image using Gemini Vision
        Returns structured Q&A data
        """
        try:
            print(f"[HANDWRITING] Extracting Q&A from: {image_path}")
            
            # Read image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Prepare prompt for Gemini Vision
            prompt = """You are an expert at reading handwritten text. 
            
Analyze this image containing handwritten questions and answers.

Extract ALL questions and their corresponding answers. For each question:
1. Extract the question number
2. Extract the complete question text
3. Extract the complete answer text

Return the data in this EXACT JSON format:
{
    "questions": [
        {
            "number": 1,
            "question": "extracted question text",
            "answer": "extracted answer text"
        }
    ]
}

IMPORTANT:
- Be very careful to read handwriting accurately
- Include ALL questions found in the image
- If answer is missing, use empty string
- Preserve the original meaning even if handwriting is unclear
- Return ONLY valid JSON, no other text

Your response:"""

            # Upload image and get response
            response = self.vision_model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])
            
            response_text = response.text.strip()
            print(f"[HANDWRITING] Raw response length: {len(response_text)}")
            
            # Try to parse JSON from response
            # Sometimes Gemini wraps JSON in markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            qa_data = json.loads(response_text)
            print(f"[HANDWRITING] Extracted {len(qa_data.get('questions', []))} questions")
            
            return qa_data
        
        except json.JSONDecodeError as e:
            print(f"[HANDWRITING] JSON parse error: {e}")
            print(f"[HANDWRITING] Response was: {response_text[:500]}")
            return {"questions": [], "error": "Failed to parse handwriting"}
        
        except Exception as e:
            print(f"[HANDWRITING] Error: {e}")
            return {"questions": [], "error": str(e)}
    
    def evaluate_answer(self, question: str, student_answer: str, 
                       subject_content: str, max_marks: float = 10.0) -> Tuple[float, str]:
        """
        Evaluate a single answer against subject content using Gemini
        Returns (marks, feedback)
        """
        try:
            prompt = f"""You are a fair and balanced academic evaluator. Evaluate the student's answer based on the provided subject content.

SUBJECT CONTENT (Reference Material):
{subject_content[:4000]}  

QUESTION:
{question}

STUDENT'S ANSWER:
{student_answer}

EVALUATION CRITERIA:
- Maximum Marks: {max_marks}
- Award marks for CORRECT information present in the answer
- The answer doesn't need to match the reference word-for-word
- Focus on KEY CONCEPTS and MAIN POINTS being covered
- Give credit for correct understanding even if expressed differently
- Ignore minor grammar/spelling errors and handwriting issues
- Be LENIENT - if the core concept is correct, award good marks

SCORING GUIDE (Be Generous):
- {max_marks}-{max_marks*0.85:.1f}: Excellent - Core concepts correct, main points covered
- {max_marks*0.65:.1f}-{max_marks*0.84:.1f}: Good - Most key points present, minor details missing
- {max_marks*0.45:.1f}-{max_marks*0.64:.1f}: Average - Some correct concepts, needs more detail
- {max_marks*0.25:.1f}-{max_marks*0.44:.1f}: Below Average - Few correct points
- 0-{max_marks*0.24:.1f}: Poor - Mostly incorrect or completely irrelevant

IMPORTANT:
- If the student's answer contains the MAIN IDEAS from the subject content, award at least 60-70% marks
- Don't penalize for brevity if key points are covered
- Don't require exact wording from reference material
- Focus on conceptual understanding, not memorization

Respond in this EXACT format:
MARKS: <number between 0 and {max_marks}>
FEEDBACK: <detailed explanation of marks awarded, what was correct, what was missing>

Your evaluation:"""

            response = self.text_model.generate_content(prompt)
            evaluation = response.text.strip()
            
            # Parse response
            marks = 0.0
            feedback = "Evaluation completed"
            
            lines = evaluation.split('\n')
            for line in lines:
                if line.startswith('MARKS:'):
                    marks_str = line.replace('MARKS:', '').strip()
                    try:
                        marks = float(marks_str)
                        marks = max(0.0, min(marks, max_marks))
                    except ValueError:
                        marks = 0.0
                elif line.startswith('FEEDBACK:'):
                    feedback = line.replace('FEEDBACK:', '').strip()
            
            # If parsing failed, try to find numbers
            if marks == 0.0 and "MARKS:" in evaluation:
                import re
                numbers = re.findall(r'\d+\.?\d*', evaluation)
                if numbers:
                    marks = float(numbers[0])
                    marks = max(0.0, min(marks, max_marks))
            
            return marks, feedback
        
        except Exception as e:
            print(f"[EVALUATION] Error: {e}")
            return 0.0, f"Evaluation error: {str(e)}"
    
    def evaluate_handwritten_assessment(self, subject_file_path: str, 
                                       subject_file_type: str,
                                       handwritten_image_path: str,
                                       marks_per_question: float = 10.0) -> Dict:
        """
        Complete evaluation pipeline:
        1. Extract subject content
        2. Extract handwritten Q&A
        3. Evaluate each answer
        4. Return results with marks and feedback
        """
        print("\n" + "="*80)
        print("HANDWRITTEN ASSESSMENT EVALUATION")
        print("="*80)
        
        # Step 1: Extract subject content
        print("\n[1/3] Extracting subject content...")
        subject_content = self.extract_text_from_file(subject_file_path, subject_file_type)
        
        if not subject_content:
            return {
                "success": False,
                "error": "Failed to extract subject content",
                "results": []
            }
        
        print(f"✓ Extracted {len(subject_content)} characters of subject content")
        
        # Step 2: Extract handwritten Q&A
        print("\n[2/3] Extracting handwritten questions and answers...")
        qa_data = self.extract_handwritten_qa(handwritten_image_path)
        
        if "error" in qa_data or not qa_data.get("questions"):
            return {
                "success": False,
                "error": qa_data.get("error", "No questions found"),
                "results": []
            }
        
        questions = qa_data["questions"]
        print(f"✓ Found {len(questions)} questions")
        
        # Step 3: Evaluate each answer
        print("\n[3/3] Evaluating answers...")
        results = []
        total_marks = 0.0
        max_possible = len(questions) * marks_per_question
        
        for i, qa in enumerate(questions, 1):
            question_text = qa.get("question", "")
            answer_text = qa.get("answer", "")
            
            print(f"\n  Evaluating Q{i}...")
            marks, feedback = self.evaluate_answer(
                question_text, 
                answer_text, 
                subject_content,
                marks_per_question
            )
            
            total_marks += marks
            
            results.append({
                "question_number": qa.get("number", i),
                "question": question_text,
                "student_answer": answer_text,
                "marks_obtained": marks,
                "max_marks": marks_per_question,
                "feedback": feedback
            })
            
            print(f"  ✓ Q{i}: {marks}/{marks_per_question} marks")
        
        percentage = (total_marks / max_possible * 100) if max_possible > 0 else 0
        
        print("\n" + "="*80)
        print(f"EVALUATION COMPLETE")
        print(f"Total Score: {total_marks:.1f}/{max_possible} ({percentage:.1f}%)")
        print("="*80 + "\n")
        
        return {
            "success": True,
            "total_marks": total_marks,
            "max_marks": max_possible,
            "percentage": percentage,
            "total_questions": len(questions),
            "results": results,
            "subject_content_length": len(subject_content)
        }


# Test function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python handwritten_evaluator.py <subject_file> <handwritten_image>")
        print("\nExample:")
        print("  python handwritten_evaluator.py notes.pdf answers.jpg")
        sys.exit(1)
    
    subject_file = sys.argv[1]
    handwritten_file = sys.argv[2]
    
    # Determine file type
    file_ext = subject_file.split('.')[-1].lower()
    
    try:
        evaluator = HandwrittenEvaluator()
        results = evaluator.evaluate_handwritten_assessment(
            subject_file, 
            file_ext,
            handwritten_file
        )
        
        if results["success"]:
            print("\n📊 RESULTS:")
            print(f"Total Questions: {results['total_questions']}")
            print(f"Total Score: {results['total_marks']:.1f}/{results['max_marks']}")
            print(f"Percentage: {results['percentage']:.1f}%")
            
            print("\n📝 DETAILED FEEDBACK:")
            for r in results["results"]:
                print(f"\nQ{r['question_number']}: {r['question'][:60]}...")
                print(f"Answer: {r['student_answer'][:60]}...")
                print(f"Marks: {r['marks_obtained']}/{r['max_marks']}")
                print(f"Feedback: {r['feedback'][:100]}...")
        else:
            print(f"\n❌ Error: {results['error']}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
