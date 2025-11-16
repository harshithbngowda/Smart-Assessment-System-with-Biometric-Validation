"""
Answer Evaluation Module
Integrates with Gemini API for automatic evaluation
"""

import os
import json
import threading
from datetime import datetime

# Import from modules directory
try:
    # Set UTF-8 encoding for Windows
    import sys
    import os
    if sys.platform == "win32":
        os.environ["PYTHONIOENCODING"] = "utf-8"
    
    from modules.answer_evaluator_gemini import AnswerEvaluatorGemini
    print("✅ Advanced AI evaluator loaded successfully")
except Exception as e:
    print(f"⚠️ Warning: Advanced AI evaluator not available ({type(e).__name__}). Using fallback evaluator.")
    AnswerEvaluatorGemini = None

def evaluate_submission(submission_id, app_instance, gemini_api_key):
    """Evaluate submission asynchronously"""
    def evaluate_async():
        try:
            from models import db, Submission, AnswerSubmission, Question
            
            with app_instance.app_context():
                print(f"[EVAL] Starting evaluation for submission {submission_id}")
                print(f"[EVAL] Database URI: {app_instance.config['SQLALCHEMY_DATABASE_URI']}")
                
                # Retry mechanism in case submission isn't visible yet
                submission = None
                for attempt in range(5):
                    # Use db.session.get() instead of query.get() and expire_all to refresh
                    db.session.expire_all()
                    submission = db.session.get(Submission, submission_id)
                    if submission:
                        print(f"[EVAL] Found submission {submission_id} on attempt {attempt + 1}")
                        break
                    print(f"[EVAL] Submission {submission_id} not found, retrying... (attempt {attempt + 1}/5)")
                    import time
                    time.sleep(0.5)
                
                if not submission:
                    print(f"[EVAL] Submission {submission_id} not found after 5 attempts")
                    print(f"[EVAL] Checking all submissions in database...")
                    all_subs = db.session.query(Submission).all()
                    print(f"[EVAL] Total submissions in DB: {len(all_subs)}, IDs: {[s.id for s in all_subs]}")
                    return
                
                # Get all answers for this submission
                answers = AnswerSubmission.query.filter_by(submission_id=submission_id).all()
                
                if AnswerEvaluatorGemini and gemini_api_key:
                    # Use Gemini evaluator
                    try:
                        evaluator = AnswerEvaluatorGemini(api_key=gemini_api_key)
                        print(f"[EVAL] Using Gemini evaluator for submission {submission_id}")
                    except Exception as e:
                        print(f"[EVAL] Failed to initialize Gemini evaluator: {e}")
                        print(f"[EVAL] Falling back to simple evaluation")
                        evaluator = None
                    
                    if evaluator:
                        # Evaluate each answer
                        total_marks = 0
                        for answer in answers:
                            question = Question.query.get(answer.question_id)
                            
                            try:
                                print(f"[EVAL] Evaluating Q{answer.question_number} (type: {question.question_type})")
                                
                                # Call appropriate evaluation method based on question type
                                if question.question_type == 'mcq':
                                    marks, feedback = evaluator.evaluate_mcq(
                                        answer.student_answer,
                                        question.correct_answer
                                    )
                                elif question.question_type in ['short', 'long', 'descriptive']:
                                    # Scale marks to question's actual marks
                                    raw_marks, feedback = evaluator.evaluate_descriptive(
                                        question.question_text,
                                        answer.student_answer,
                                        question.correct_answer
                                    )
                                    # Scale from evaluator's default (10) to question's marks
                                    marks = (raw_marks / evaluator.descriptive_marks) * question.marks
                                elif question.question_type == 'programming':
                                    # Scale marks to question's actual marks
                                    raw_marks, feedback = evaluator.evaluate_programming(
                                        question.question_text,
                                        answer.student_answer,
                                        question.correct_answer
                                    )
                                    # Scale from evaluator's default (10) to question's marks
                                    marks = (raw_marks / evaluator.programming_marks) * question.marks
                                else:
                                    # Default to descriptive evaluation
                                    raw_marks, feedback = evaluator.evaluate_descriptive(
                                        question.question_text,
                                        answer.student_answer,
                                        question.correct_answer
                                    )
                                    marks = (raw_marks / evaluator.descriptive_marks) * question.marks
                                
                                answer.marks_obtained = float(marks)
                                answer.ai_feedback = feedback
                                total_marks += answer.marks_obtained
                                
                                print(f"[EVAL] Q{answer.question_number}: {marks:.2f}/{question.marks} - {feedback[:50]}...")
                                
                            except Exception as e:
                                print(f"[EVAL] Error evaluating Q{answer.question_number}: {e}")
                                import traceback
                                traceback.print_exc()
                                answer.marks_obtained = 0
                                answer.ai_feedback = f"Evaluation error: {str(e)}"
                    
                        submission.total_marks = total_marks
                        submission.evaluated = True
                        submission.evaluated_at = datetime.utcnow()
                        print(f"[EVAL] Gemini evaluation complete. Total: {total_marks}/{submission.assessment.total_marks}")
                    else:
                        # Gemini init failed, use fallback
                        total_marks = 0
                        for answer in answers:
                            question = Question.query.get(answer.question_id)
                            
                            marks = evaluate_answer_fallback(
                                answer.student_answer,
                                question.correct_answer,
                                question.marks
                            )
                            
                            answer.marks_obtained = marks
                            answer.ai_feedback = "Automated evaluation completed (fallback)."
                            total_marks += marks
                        
                        submission.total_marks = total_marks
                        submission.evaluated = True
                        submission.evaluated_at = datetime.utcnow()
                    
                else:
                    # Fallback evaluation
                    total_marks = 0
                    for answer in answers:
                        question = Question.query.get(answer.question_id)
                        
                        # Simple keyword matching for fallback
                        marks = evaluate_answer_fallback(
                            answer.student_answer,
                            question.correct_answer,
                            question.marks
                        )
                        
                        answer.marks_obtained = marks
                        answer.ai_feedback = "Automated evaluation completed."
                        total_marks += marks
                    
                    submission.total_marks = total_marks
                    submission.evaluated = True
                    submission.evaluated_at = datetime.utcnow()
                
                db.session.commit()
                print(f"[EVAL] ✅ Submission {submission_id} evaluated successfully. Total marks: {total_marks}")
                
        except Exception as e:
            print(f"[EVAL] ❌ Error evaluating submission {submission_id}: {e}")
            import traceback
            traceback.print_exc()
            # Try to mark as evaluated with 0 marks so it doesn't stay pending
            try:
                from models import db, Submission
                from app import app
                with app.app_context():
                    submission = Submission.query.get(submission_id)
                    if submission and not submission.evaluated:
                        submission.evaluated = True
                        submission.total_marks = 0
                        submission.evaluated_at = datetime.utcnow()
                        db.session.commit()
                        print(f"[EVAL] Marked submission {submission_id} as evaluated with 0 marks due to error")
            except Exception as inner_e:
                print(f"[EVAL] Failed to mark submission as evaluated: {inner_e}")
    
    # Start evaluation in background thread
    thread = threading.Thread(target=evaluate_async)
    thread.daemon = True
    thread.start()

def evaluate_answer_fallback(student_answer, correct_answer, max_marks):
    """Fallback evaluation using simple keyword matching"""
    if not student_answer or not correct_answer:
        return 0
    
    student_lower = student_answer.lower()
    correct_lower = correct_answer.lower()
    
    # Simple keyword matching
    student_words = set(student_lower.split())
    correct_words = set(correct_lower.split())
    
    # Calculate similarity
    common_words = student_words.intersection(correct_words)
    similarity = len(common_words) / len(correct_words) if correct_words else 0
    
    # Award marks based on similarity
    if similarity >= 0.8:
        return max_marks
    elif similarity >= 0.6:
        return max_marks * 0.8
    elif similarity >= 0.4:
        return max_marks * 0.6
    elif similarity >= 0.2:
        return max_marks * 0.4
    else:
        return max_marks * 0.2

def evaluate_mcq_answer(student_answer, correct_answer, options):
    """Evaluate MCQ answers"""
    if not student_answer or not correct_answer:
        return 0
    
    # For MCQ, exact match is required
    if student_answer.strip().upper() == correct_answer.strip().upper():
        return 1  # Full marks for MCQ
    else:
        return 0

def evaluate_programming_answer(student_answer, correct_answer, max_marks):
    """Evaluate programming answers"""
    if not student_answer:
        return 0
    
    # For programming, check for key concepts
    student_lower = student_answer.lower()
    
    # Look for programming keywords
    programming_keywords = ['function', 'def', 'class', 'import', 'return', 'if', 'else', 'for', 'while']
    found_keywords = sum(1 for keyword in programming_keywords if keyword in student_lower)
    
    # Award partial marks based on programming concepts
    if found_keywords >= 5:
        return max_marks
    elif found_keywords >= 3:
        return max_marks * 0.7
    elif found_keywords >= 1:
        return max_marks * 0.4
    else:
        return max_marks * 0.1