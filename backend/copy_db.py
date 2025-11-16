"""Copy instance database to main location"""
import os
import shutil

backend_dir = os.path.dirname(os.path.abspath(__file__))
instance_db = os.path.join(backend_dir, 'instance', 'assessment_platform.db')
main_db = os.path.join(backend_dir, 'assessment_platform.db')

print(f"Source: {instance_db}")
print(f"Destination: {main_db}")

if os.path.exists(instance_db):
    print(f"\n✓ Source database exists ({os.path.getsize(instance_db)} bytes)")
    
    # Backup existing main DB if it exists
    if os.path.exists(main_db):
        backup = main_db + '.backup'
        shutil.copy2(main_db, backup)
        print(f"✓ Backed up existing database to: {backup}")
        os.remove(main_db)
    
    # Copy instance DB to main location
    shutil.copy2(instance_db, main_db)
    print(f"✓ Copied database to: {main_db}")
    print(f"✓ New database size: {os.path.getsize(main_db)} bytes")
    print(f"\n✅ Database migration complete!")
else:
    print(f"❌ Source database not found!")
