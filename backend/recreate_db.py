"""
Recreate database with updated foreign key constraints
This will backup the old database and create a new one with CASCADE delete
"""
import os
import shutil
from app import app, db
from models import User, Assessment, Question, Submission, AnswerSubmission

# Backup old database
backend_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(backend_dir, 'assessment_platform.db')
backup_path = db_path + '.before_cascade.backup'

if os.path.exists(db_path):
    print(f"Backing up database to: {backup_path}")
    shutil.copy2(db_path, backup_path)
    print("✓ Backup created")

# Drop and recreate all tables
with app.app_context():
    print("\nDropping all tables...")
    db.drop_all()
    print("✓ Tables dropped")
    
    print("\nCreating tables with CASCADE delete...")
    db.create_all()
    print("✓ Tables created")
    
    print("\n✅ Database recreated successfully!")
    print("\n⚠️  NOTE: All data has been cleared. You'll need to:")
    print("   1. Register users again")
    print("   2. Create assessments again")
    print("   3. Or restore from backup if needed")
