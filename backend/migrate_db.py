"""
Migrate database from instance folder to backend folder
"""
import os
import shutil

# Paths
backend_dir = os.path.dirname(os.path.abspath(__file__))
instance_db = os.path.join(backend_dir, 'instance', 'assessment_platform.db')
new_db = os.path.join(backend_dir, 'assessment_platform.db')

print(f"Backend directory: {backend_dir}")
print(f"Instance DB: {instance_db}")
print(f"New DB location: {new_db}")

# Check if instance DB exists
if os.path.exists(instance_db):
    print(f"\n✓ Found database in instance folder")
    
    # Check if new location already has a DB
    if os.path.exists(new_db):
        print(f"⚠ Database already exists at new location")
        response = input("Do you want to replace it with the instance DB? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled")
            exit(0)
        os.remove(new_db)
        print(f"✓ Removed old database at new location")
    
    # Copy the database
    shutil.copy2(instance_db, new_db)
    print(f"✓ Database copied to: {new_db}")
    print(f"\n✅ Migration complete!")
    
else:
    print(f"\n⚠ No database found in instance folder")
    print(f"A new database will be created at: {new_db}")
