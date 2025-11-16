"""
Migrate database to support CASCADE delete while preserving data
"""
import sqlite3
import os
import shutil

backend_dir = os.path.dirname(os.path.abspath(__file__))
old_db = os.path.join(backend_dir, 'assessment_platform.db')
new_db = os.path.join(backend_dir, 'assessment_platform_new.db')
backup_db = old_db + '.before_cascade.backup'

print("=" * 80)
print("Database Migration: Adding CASCADE Delete Support")
print("=" * 80)

# Backup
if os.path.exists(old_db):
    print(f"\n1. Creating backup...")
    shutil.copy2(old_db, backup_db)
    print(f"   ✓ Backup: {backup_db}")
else:
    print(f"\n❌ Database not found: {old_db}")
    exit(1)

# Connect to old database
print(f"\n2. Reading data from old database...")
old_conn = sqlite3.connect(old_db)
old_conn.row_factory = sqlite3.Row
old_cursor = old_conn.cursor()

# Get all data
users = old_cursor.execute("SELECT * FROM users").fetchall()
assessments = old_cursor.execute("SELECT * FROM assessments").fetchall()
questions = old_cursor.execute("SELECT * FROM questions").fetchall()
submissions = old_cursor.execute("SELECT * FROM submissions").fetchall()
answers = old_cursor.execute("SELECT * FROM answer_submissions").fetchall()

print(f"   ✓ Users: {len(users)}")
print(f"   ✓ Assessments: {len(assessments)}")
print(f"   ✓ Questions: {len(questions)}")
print(f"   ✓ Submissions: {len(submissions)}")
print(f"   ✓ Answers: {len(answers)}")

old_conn.close()

# Create new database with CASCADE
print(f"\n3. Creating new database with CASCADE delete...")
if os.path.exists(new_db):
    os.remove(new_db)

new_conn = sqlite3.connect(new_db)
new_cursor = new_conn.cursor()

# Enable foreign keys
new_cursor.execute("PRAGMA foreign_keys = ON")

# Create tables with CASCADE
new_cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    department VARCHAR(100),
    student_id VARCHAR(50),
    year VARCHAR(20),
    face_encoding BLOB,
    face_registered_at DATETIME,
    created_at DATETIME,
    updated_at DATETIME
)
""")

new_cursor.execute("""
CREATE TABLE assessments (
    id INTEGER PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    teacher_id INTEGER NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    total_marks REAL DEFAULT 0,
    enable_anti_cheating BOOLEAN DEFAULT 1,
    enable_fullscreen BOOLEAN DEFAULT 1,
    enable_webcam BOOLEAN DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
)
""")

new_cursor.execute("""
CREATE TABLE questions (
    id INTEGER PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) NOT NULL,
    correct_answer TEXT,
    options TEXT,
    marks REAL DEFAULT 1,
    created_at DATETIME,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
)
""")

new_cursor.execute("""
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    submitted_at DATETIME,
    total_marks REAL DEFAULT 0,
    evaluated BOOLEAN DEFAULT 0,
    evaluated_at DATETIME,
    teacher_comments TEXT,
    face_verification_passed BOOLEAN,
    cheating_attempts INTEGER,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
)
""")

new_cursor.execute("""
CREATE TABLE answer_submissions (
    id INTEGER PRIMARY KEY,
    submission_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    student_answer TEXT,
    marks_obtained REAL DEFAULT 0,
    ai_feedback TEXT,
    teacher_feedback TEXT,
    created_at DATETIME,
    FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
)
""")

print("   ✓ Tables created with CASCADE delete")

# Copy data
print(f"\n4. Copying data to new database...")

for user in users:
    new_cursor.execute("""
        INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(user))

for assessment in assessments:
    new_cursor.execute("""
        INSERT INTO assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(assessment))

for question in questions:
    new_cursor.execute("""
        INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(question))

for submission in submissions:
    new_cursor.execute("""
        INSERT INTO submissions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(submission))

for answer in answers:
    new_cursor.execute("""
        INSERT INTO answer_submissions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(answer))

new_conn.commit()
print("   ✓ Data copied successfully")

# Verify
new_cursor.execute("SELECT COUNT(*) FROM users")
print(f"   ✓ Verified users: {new_cursor.fetchone()[0]}")

new_conn.close()

# Replace old database with new one
print(f"\n5. Replacing old database...")
os.remove(old_db)
os.rename(new_db, old_db)
print(f"   ✓ Database updated: {old_db}")

print("\n" + "=" * 80)
print("✅ Migration Complete!")
print("=" * 80)
print(f"\nYou can now delete users with assessments.")
print(f"Backup available at: {backup_db}")
print("\nRestart your backend to use the updated database.")
