import sqlite3

conn = sqlite3.connect('assessment_platform.db.before_cascade.backup')
cursor = conn.cursor()

tables = ['users', 'assessments', 'questions', 'submissions', 'answer_submissions']

for table in tables:
    print(f"\n{table}:")
    print("=" * 60)
    cursor.execute(f'PRAGMA table_info({table})')
    for row in cursor.fetchall():
        print(f"  {row[1]}: {row[2]}")
