import sqlite3

conn = sqlite3.connect('assessment_platform.db')
cursor = conn.cursor()

print("\n" + "="*80)
print("LATEST SUBMISSION CHECK")
print("="*80)

# Get latest submission
cursor.execute("""
    SELECT id, student_id, assessment_id, total_marks, evaluated, submitted_at, evaluated_at
    FROM submissions
    ORDER BY id DESC
    LIMIT 1
""")

sub = cursor.fetchone()
if sub:
    print(f"\nSubmission ID: {sub[0]}")
    print(f"Student ID: {sub[1]}")
    print(f"Assessment ID: {sub[2]}")
    print(f"Total Marks: {sub[3]}")
    print(f"Evaluated: {sub[4]}")
    print(f"Submitted At: {sub[5]}")
    print(f"Evaluated At: {sub[6]}")
    
    # Get answers
    cursor.execute("""
        SELECT question_number, marks_obtained, ai_feedback
        FROM answer_submissions
        WHERE submission_id = ?
        ORDER BY question_number
    """, (sub[0],))
    
    print(f"\nAnswers:")
    print("-" * 80)
    for ans in cursor.fetchall():
        print(f"Q{ans[0]}: {ans[1]} marks - {ans[2][:60]}...")
else:
    print("\nNo submissions found!")

print("\n" + "="*80)
conn.close()
