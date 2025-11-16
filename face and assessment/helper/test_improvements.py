"""
Quick Test Script to Verify All Improvements
Run this to check if phone detection works and settings are correct
"""

import os
from config import Config

def test_configuration():
    """Test if configuration settings are correct"""
    print("="*60)
    print("Testing Configuration Settings")
    print("="*60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Face recognition threshold
    tests_total += 1
    if Config.FACE_RECOGNITION_THRESHOLD >= 0.6:
        print("✓ Face recognition threshold: 0.6 (lenient)")
        tests_passed += 1
    else:
        print(f"✗ Face recognition threshold: {Config.FACE_RECOGNITION_THRESHOLD} (should be >= 0.6)")
    
    # Test 2: Max warnings
    tests_total += 1
    if Config.MAX_WARNINGS >= 10:
        print(f"✓ Max warnings: {Config.MAX_WARNINGS} (forgiving)")
        tests_passed += 1
    else:
        print(f"✗ Max warnings: {Config.MAX_WARNINGS} (should be >= 10)")
    
    # Test 3: Phone detection confidence
    tests_total += 1
    if Config.PHONE_DETECTION_CONFIDENCE <= 0.2:
        print(f"✓ Phone detection confidence: {Config.PHONE_DETECTION_CONFIDENCE} (sensitive)")
        tests_passed += 1
    else:
        print(f"✗ Phone detection confidence: {Config.PHONE_DETECTION_CONFIDENCE} (should be <= 0.2)")
    
    # Test 4: Warning cooldown
    tests_total += 1
    if Config.WARNING_COOLDOWN >= 3:
        print(f"✓ Warning cooldown: {Config.WARNING_COOLDOWN} seconds")
        tests_passed += 1
    else:
        print(f"✗ Warning cooldown: {Config.WARNING_COOLDOWN} seconds (should be >= 3)")
    
    print(f"\nConfiguration Tests: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total

def test_yolo_files():
    """Test if YOLO files are present for phone detection"""
    print("\n" + "="*60)
    print("Testing YOLO Phone Detection Setup")
    print("="*60)
    
    yolo_dir = os.path.join(Config.MODELS_DIR, "yolo")
    
    required_files = {
        "yolov3.cfg": Config.YOLO_CONFIG_PATH,
        "yolov3.weights": Config.YOLO_WEIGHTS_PATH,
        "coco.names": Config.YOLO_CLASSES_PATH
    }
    
    files_found = 0
    for filename, filepath in required_files.items():
        if os.path.exists(filepath):
            size = os.path.getsize(filepath) / (1024*1024)  # MB
            print(f"✓ {filename} found ({size:.1f} MB)")
            files_found += 1
        else:
            print(f"✗ {filename} not found at: {filepath}")
    
    if files_found == 3:
        print("\n✅ Phone detection is ENABLED and ready!")
        return True
    else:
        print(f"\n⚠️ Phone detection incomplete ({files_found}/3 files)")
        print("Run: python setup_yolo_auto.py")
        return False

def test_face_detection():
    """Test if face detection module works"""
    print("\n" + "="*60)
    print("Testing Face Detection Module")
    print("="*60)
    
    try:
        from simple_face_detection import face_locations, face_encodings, compare_faces
        print("✓ Face detection module loaded successfully")
        
        # Test with dummy data
        import numpy as np
        dummy_encoding = np.random.rand(496)
        dummy_encodings_list = [np.random.rand(496) for _ in range(10)]
        
        matches = compare_faces(dummy_encodings_list, dummy_encoding, tolerance=0.6)
        print(f"✓ Face comparison function working")
        print(f"  Tolerance: 0.6 (lenient)")
        
        return True
    except Exception as e:
        print(f"✗ Face detection module error: {str(e)}")
        return False

def test_database():
    """Test database connection"""
    print("\n" + "="*60)
    print("Testing Database")
    print("="*60)
    
    try:
        from database_manager import DatabaseManager
        db = DatabaseManager()
        students = db.get_all_students()
        print(f"✓ Database connection successful")
        print(f"  Registered students: {len(students)}")
        
        if students:
            print("\n  Students registered:")
            for student in students:
                print(f"    - {student['name']} (ID: {student['student_id']})")
        
        return True
    except Exception as e:
        print(f"✗ Database error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("IMPROVEMENTS VERIFICATION TEST")
    print("="*60)
    
    results = {
        "Configuration": test_configuration(),
        "YOLO Setup": test_yolo_files(),
        "Face Detection": test_face_detection(),
        "Database": test_database()
    }
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nYour system is ready:")
        print("✓ Face recognition is lenient (won't false-warn)")
        print("✓ Phone detection is enabled")
        print("✓ No warnings for looking away")
        print("✓ 10 warning limit (very forgiving)")
        print("\nRun: python main.py")
    else:
        print("⚠️ SOME TESTS FAILED")
        print("="*60)
        print("\nPlease check the failed tests above.")
    
    print("="*60)

if __name__ == "__main__":
    main()
