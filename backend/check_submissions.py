from models import db, Submission, AnswerSubmission, Question
from app import app

with app.app_context():
    submissions = Submission.query.all()
    print(f"\n{'='*80}")
    print(f"Total submissions: {len(submissions)}")
    print(f"{'='*80}\n")
    
    for sub in submissions:
        print(f"Submission ID: {sub.id}")
        print(f"Student ID: {sub.student_id}")
        print(f"Assessment ID: {sub.assessment_id}")
        print(f"Evaluated: {sub.evaluated}")
        print(f"Total Marks: {sub.total_marks}")
        print(f"Submitted At: {sub.submitted_at}")
        print(f"Evaluated At: {sub.evaluated_at}")
        
        # Get answers
        answers = AnswerSubmission.query.filter_by(submission_id=sub.id).all()
        print(f"Number of answers: {len(answers)}")
        
        for ans in answers:
            question = Question.query.get(ans.question_id)
            print(f"  Q{ans.question_number}: Type={question.question_type}, "
                  f"Marks={ans.marks_obtained}/{question.marks}, "
                  f"Answer='{ans.student_answer[:50]}...'")
        
        print(f"{'-'*80}\n")
