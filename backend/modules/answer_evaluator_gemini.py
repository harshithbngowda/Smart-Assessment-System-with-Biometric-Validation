"""
Answer Evaluation System using Google Gemini (Free Alternative)
Evaluates student answers using Google's free Gemini API
"""

import json
import os
from typing import Dict, List, Tuple
import google.generativeai as genai


class AnswerEvaluatorGemini:
    """
    Evaluates student answers using Google Gemini (Free tier available).
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the evaluator with Google Gemini API key.
        
        Args:
            api_key: Google Gemini API key. If None, reads from environment variable GEMINI_API_KEY
        """
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("Gemini API key not provided. Set GEMINI_API_KEY environment variable or pass it to constructor.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')  # Latest free model
        
        # Scoring criteria
        self.mcq_marks = 1
        self.descriptive_marks = 10
        self.programming_marks = 10
    
    def load_json(self, file_path: str) -> Dict:
        """Load assessment data from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def evaluate_mcq(self, student_answer: str, correct_answer: str) -> Tuple[float, str]:
        """Evaluate MCQ answer."""
        if not student_answer or student_answer.strip() == "":
            return 0.0, "No answer provided"
        
        if student_answer.strip().upper() == correct_answer.strip().upper():
            return self.mcq_marks, "Correct answer"
        else:
            return 0.0, f"Incorrect. Correct answer is {correct_answer}"
    
    def evaluate_descriptive(self, question: str, student_answer: str, correct_answer: str) -> Tuple[float, str]:
        """Evaluate descriptive answer using Gemini."""
        if not student_answer or student_answer.strip() == "":
            return 0.0, "No answer provided"
        
        prompt = f"""You are a STRICT academic evaluator. Evaluate based on content accuracy, NOT grammar.

Question: {question}

Reference Answer (Key Points): {correct_answer}

Student's Answer: {student_answer}

STRICT Evaluation Criteria:
- Maximum Marks: {self.descriptive_marks}
- IGNORE grammatical errors, spelling mistakes, language quality
- Focus ONLY on factual correctness and key concepts covered
- Be critical about missing information

Scoring Guide:
- 9-10/10: Covers all key concepts, thorough and accurate
- 7-8/10: Most key points covered, minor gaps
- 5-6/10: Some key concepts present, significant gaps
- 3-4/10: Few correct points, mostly incomplete
- 1-2/10: Very little correct information
- 0/10: Wrong, irrelevant, or random text

Compare student's answer to reference carefully. Deduct marks for each missing key concept!

Respond ONLY in this format:
MARKS: <number 0-{self.descriptive_marks}>
FEEDBACK: <explanation mentioning which key points were covered/missed and why marks deducted>

Your evaluation:"""

        try:
            response = self.model.generate_content(prompt)
            evaluation = response.text.strip()
            
            # Parse the response
            marks = 0.0
            feedback = "Evaluation completed"
            
            lines = evaluation.split('\n')
            for line in lines:
                if line.startswith('MARKS:'):
                    marks_str = line.replace('MARKS:', '').strip()
                    try:
                        marks = float(marks_str)
                        marks = max(0.0, min(marks, self.descriptive_marks))
                    except ValueError:
                        marks = 0.0
                elif line.startswith('FEEDBACK:'):
                    feedback = line.replace('FEEDBACK:', '').strip()
            
            # If parsing failed, try to find any number in the response
            if marks == 0.0 and "MARKS:" in evaluation:
                import re
                numbers = re.findall(r'\d+\.?\d*', evaluation)
                if numbers:
                    marks = float(numbers[0])
                    marks = max(0.0, min(marks, self.descriptive_marks))
            
            return marks, feedback
            
        except Exception as e:
            return 0.0, f"Error during evaluation: {str(e)}"
    
    def evaluate_programming(self, question: str, student_answer: str, correct_answer: str) -> Tuple[float, str]:
        """Evaluate programming answer using Gemini."""
        if not student_answer or student_answer.strip() == "":
            return 0.0, "No answer provided"
        
        prompt = f"""You are a STRICT programming instructor evaluating student code. Be critical and thorough.

Question: {question}

Reference Solution: {correct_answer}

Student's Solution: {student_answer}

STRICT Evaluation Criteria:
- Maximum Marks: {self.programming_marks}
- BE CRITICAL - Look for errors, incomplete code, missing logic
- Check:
  * Is the code complete or cut off? (Deduct heavily if incomplete)
  * Are there syntax errors? (Deduct marks)
  * Does the logic actually solve the problem?
  * Are there missing parts compared to reference?
  * Would this code run without errors?

Scoring Guide:
- 10/10: Perfect, complete, correct logic, would run without errors
- 7-9/10: Good logic, minor issues or missing small parts
- 4-6/10: Partial solution, significant issues or incomplete
- 1-3/10: Wrong approach or mostly incorrect
- 0/10: Random text, completely wrong, or gibberish

BE STRICT: If code is incomplete (cut off mid-line), deduct at least 2-3 marks!

Provide your evaluation in this exact format:
MARKS: <number between 0 and {self.programming_marks}>
FEEDBACK: <detailed explanation of what's right, what's wrong, and why marks were deducted>

Your evaluation:"""

        try:
            response = self.model.generate_content(prompt)
            evaluation = response.text.strip()
            
            # Parse the response
            marks = 0.0
            feedback = "Evaluation completed"
            
            lines = evaluation.split('\n')
            for line in lines:
                if line.startswith('MARKS:'):
                    marks_str = line.replace('MARKS:', '').strip()
                    try:
                        marks = float(marks_str)
                        marks = max(0.0, min(marks, self.programming_marks))
                    except ValueError:
                        marks = 0.0
                elif line.startswith('FEEDBACK:'):
                    feedback = line.replace('FEEDBACK:', '').strip()
            
            # If parsing failed, try to find any number in the response
            if marks == 0.0 and "MARKS:" in evaluation:
                import re
                numbers = re.findall(r'\d+\.?\d*', evaluation)
                if numbers:
                    marks = float(numbers[0])
                    marks = max(0.0, min(marks, self.programming_marks))
            
            return marks, feedback
            
        except Exception as e:
            return 0.0, f"Error during evaluation: {str(e)}"
    
    def evaluate_assessment(self, json_file_path: str) -> Dict:
        """Evaluate complete assessment from JSON file."""
        data = self.load_json(json_file_path)
        
        results = {
            'student_name': data.get('student_name', 'Unknown'),
            'student_id': data.get('student_id', 'Unknown'),
            'timestamp': data.get('timestamp', 'Unknown'),
            'total_marks': 0.0,
            'questions_evaluated': [],
            'summary': {}
        }
        
        total_marks = 0.0
        mcq_count = 0
        descriptive_count = 0
        programming_count = 0
        mcq_marks = 0.0
        descriptive_marks = 0.0
        programming_marks = 0.0
        
        # Evaluate each question
        for answer in data.get('answers', []):
            question_num = answer['serial_no']
            question_text = answer['question']
            question_type = answer['type']
            student_ans = answer['student_answer']
            correct_ans = answer['correct_answer']
            
            print(f"Evaluating Question {question_num} ({question_type})...")
            
            if question_type == 'mcq':
                marks, feedback = self.evaluate_mcq(student_ans, correct_ans)
                mcq_count += 1
                mcq_marks += marks
            elif question_type == 'descriptive':
                marks, feedback = self.evaluate_descriptive(question_text, student_ans, correct_ans)
                descriptive_count += 1
                descriptive_marks += marks
            elif question_type == 'programming':
                marks, feedback = self.evaluate_programming(question_text, student_ans, correct_ans)
                programming_count += 1
                programming_marks += marks
            else:
                marks = 0.0
                feedback = "Unknown question type"
            
            total_marks += marks
            
            results['questions_evaluated'].append({
                'question_number': question_num,
                'question': question_text,
                'type': question_type,
                'marks_scored': marks,
                'max_marks': self.mcq_marks if question_type == 'mcq' 
                           else self.descriptive_marks if question_type == 'descriptive' 
                           else self.programming_marks,
                'feedback': feedback
            })
        
        results['total_marks'] = total_marks
        results['summary'] = {
            'mcq': {
                'count': mcq_count,
                'marks_scored': mcq_marks,
                'max_possible': mcq_count * self.mcq_marks
            },
            'descriptive': {
                'count': descriptive_count,
                'marks_scored': descriptive_marks,
                'max_possible': descriptive_count * self.descriptive_marks
            },
            'programming': {
                'count': programming_count,
                'marks_scored': programming_marks,
                'max_possible': programming_count * self.programming_marks
            }
        }
        
        return results
    
    def print_results(self, results: Dict):
        """Print evaluation results in a formatted manner."""
        print("\n" + "="*80)
        print("ASSESSMENT EVALUATION REPORT")
        print("="*80)
        print(f"Student Name: {results['student_name']}")
        print(f"Student ID: {results['student_id']}")
        print(f"Timestamp: {results['timestamp']}")
        print("="*80)
        
        print("\nQUESTION-WISE MARKS:")
        print("-"*80)
        
        for q in results['questions_evaluated']:
            print(f"\nQ{q['question_number']}. [{q['type'].upper()}] {q['question'][:60]}...")
            print(f"   Marks: {q['marks_scored']:.1f}/{q['max_marks']}")
            print(f"   Feedback: {q['feedback']}")
        
        print("\n" + "="*80)
        print("SUMMARY:")
        print("-"*80)
        
        summary = results['summary']
        if summary['mcq']['count'] > 0:
            print(f"MCQs: {summary['mcq']['marks_scored']:.1f}/{summary['mcq']['max_possible']} "
                  f"({summary['mcq']['count']} questions)")
        
        if summary['descriptive']['count'] > 0:
            print(f"Descriptive: {summary['descriptive']['marks_scored']:.1f}/{summary['descriptive']['max_possible']} "
                  f"({summary['descriptive']['count']} questions)")
        
        if summary['programming']['count'] > 0:
            print(f"Programming: {summary['programming']['marks_scored']:.1f}/{summary['programming']['max_possible']} "
                  f"({summary['programming']['count']} questions)")
        
        print("\n" + "="*80)
        total_possible = (summary['mcq']['max_possible'] + 
                         summary['descriptive']['max_possible'] + 
                         summary['programming']['max_possible'])
        percentage = (results['total_marks'] / total_possible * 100) if total_possible > 0 else 0
        
        print(f"TOTAL MARKS SCORED: {results['total_marks']:.1f}/{total_possible} ({percentage:.1f}%)")
        print("="*80 + "\n")
    
    def save_results(self, results: Dict, output_path: str):
        """Save evaluation results to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {output_path}")


# Main function
def evaluate_json_file_gemini(json_file_path: str, api_key: str = None) -> Dict:
    """Evaluate using Google Gemini (Free)."""
    evaluator = AnswerEvaluatorGemini(api_key=api_key)
    results = evaluator.evaluate_assessment(json_file_path)
    evaluator.print_results(results)
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python answer_evaluator_gemini.py <path_to_json_file>")
        print("\nMake sure to set GEMINI_API_KEY environment variable:")
        print("  Windows: set GEMINI_API_KEY=your_api_key_here")
        print("  Get free key: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"Error: File not found: {json_file}")
        sys.exit(1)
    
    try:
        results = evaluate_json_file_gemini(json_file)
        
        output_file = json_file.replace('.json', '_results_gemini.json')
        evaluator = AnswerEvaluatorGemini()
        evaluator.save_results(results, output_file)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
