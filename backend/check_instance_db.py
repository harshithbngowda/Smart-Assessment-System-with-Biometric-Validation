"""Check submissions in instance database"""
import sqlite3
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
instance_db = os.path.join(backend_dir, 'instance', 'assessment_platform.db')
main_db = os.path.join(backend_dir, 'assessment_platform.db')

print(f"Checking databases:")
print(f"=" * 80)

for db_name, db_path in [("Instance DB", instance_db), ("Main DB", main_db)]:
    print(f"\n{db_name}: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"  ❌ Does not exist")
        continue
    
    print(f"  ✓ Exists (size: {os.path.getsize(db_path)} bytes)")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check submissions
        cursor.execute("SELECT COUNT(*) FROM submissions")
        sub_count = cursor.fetchone()[0]
        print(f"  Submissions: {sub_count}")
        
        if sub_count > 0:
            cursor.execute("SELECT id, student_id, assessment_id, evaluated, total_marks FROM submissions")
            for row in cursor.fetchall():
                print(f"    - ID: {row[0]}, Student: {row[1]}, Assessment: {row[2]}, Evaluated: {row[3]}, Marks: {row[4]}")
        
        # Check users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"  Users: {user_count}")
        
        # Check assessments
        cursor.execute("SELECT COUNT(*) FROM assessments")
        assess_count = cursor.fetchone()[0]
        print(f"  Assessments: {assess_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

print(f"\n{'=' * 80}")
