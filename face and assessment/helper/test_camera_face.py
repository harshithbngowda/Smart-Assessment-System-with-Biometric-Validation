"""
Test Script to verify camera access and face detection
Run this to make sure your setup is working properly
"""

import cv2
import numpy as np
from simple_face_detection import face_locations, face_encodings
import time

def test_camera_access():
    """Test if camera can be accessed"""
    print("=" * 60)
    print("Testing Camera Access...")
    print("=" * 60)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ ERROR: Cannot access camera!")
        print("Please check:")
        print("  - Camera is connected")
        print("  - Camera permissions are granted")
        print("  - No other application is using the camera")
        return False
    
    print("✓ Camera accessed successfully!")
    cap.release()
    return True

def test_face_detection():
    """Test face detection in real-time"""
    print("\n" + "=" * 60)
    print("Testing Face Detection...")
    print("=" * 60)
    print("Look at your camera. Press 'q' to quit, 'c' to capture a test photo")
    
    cap = cv2.VideoCapture(0)
    face_detected_count = 0
    frame_count = 0
    captured_encodings = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ ERROR: Cannot read from camera")
            break
        
        frame_count += 1
        
        # Detect faces
        faces = face_locations(frame)
        
        # Draw rectangles around faces
        for (top, right, bottom, left) in faces:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, "Face Detected", (left, top - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            face_detected_count += 1
        
        # Display info on frame
        info_text = f"Faces: {len(faces)} | Frames: {frame_count}"
        cv2.putText(frame, info_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.putText(frame, "Press 'q' to quit, 'c' to capture", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Show the frame
        cv2.imshow('Face Detection Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('c') and len(faces) > 0:
            print("\n📸 Capturing face encoding...")
            encodings = face_encodings(frame, faces)
            if encodings:
                captured_encodings.append(encodings[0])
                print(f"✓ Captured! Total encodings: {len(captured_encodings)}")
                print(f"  Encoding shape: {encodings[0].shape}")
            else:
                print("❌ Failed to extract face encoding")
    
    cap.release()
    cv2.destroyAllWindows()
    
    print("\n" + "=" * 60)
    print("Face Detection Test Results:")
    print("=" * 60)
    print(f"Total frames processed: {frame_count}")
    print(f"Face detections: {face_detected_count}")
    print(f"Captured encodings: {len(captured_encodings)}")
    
    if face_detected_count > 0:
        print("\n✓ Face detection is working!")
        detection_rate = (face_detected_count / frame_count) * 100
        print(f"  Detection rate: {detection_rate:.1f}%")
    else:
        print("\n❌ No faces detected!")
        print("Please ensure:")
        print("  - You are in a well-lit area")
        print("  - Your face is clearly visible to the camera")
        print("  - You are facing the camera directly")
    
    return face_detected_count > 0, captured_encodings

def test_face_comparison(captured_encodings):
    """Test face comparison if we have captured encodings"""
    if len(captured_encodings) < 2:
        print("\n⚠ Not enough encodings captured to test comparison")
        print("  Capture at least 2 face encodings using 'c' key during test")
        return
    
    print("\n" + "=" * 60)
    print("Testing Face Comparison...")
    print("=" * 60)
    
    from simple_face_detection import compare_faces
    
    # Compare first encoding with all others
    reference = captured_encodings[0]
    others = captured_encodings[1:]
    
    matches = compare_faces(others, reference, tolerance=0.4)
    
    print(f"Reference encoding vs {len(others)} other encoding(s):")
    for i, match in enumerate(matches):
        status = "✓ MATCH" if match else "✗ NO MATCH"
        print(f"  Encoding {i+2}: {status}")
    
    match_rate = sum(matches) / len(matches) * 100 if matches else 0
    print(f"\nMatch rate: {match_rate:.1f}%")
    
    if match_rate > 70:
        print("✓ Face comparison is working well!")
    elif match_rate > 30:
        print("⚠ Face comparison is working but may need adjustment")
    else:
        print("❌ Face comparison may not be reliable")

def test_database_saving():
    """Test if database operations work"""
    print("\n" + "=" * 60)
    print("Testing Database Operations...")
    print("=" * 60)
    
    try:
        from database_manager import DatabaseManager
        import os
        
        db_manager = DatabaseManager()
        
        # Check if database file exists
        from config import Config
        if os.path.exists(Config.DATABASE_PATH):
            print(f"✓ Database file exists at: {Config.DATABASE_PATH}")
        else:
            print(f"❌ Database file not found at: {Config.DATABASE_PATH}")
        
        # Try to get all students
        students = db_manager.get_all_students()
        print(f"✓ Database query successful")
        print(f"  Registered students: {len(students)}")
        
        if students:
            print("\n  Student List:")
            for student in students:
                print(f"    - {student['name']} (ID: {student['student_id']})")
        
        print("\n✓ Database operations are working!")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("BIOMETRIC SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Test 1: Camera Access
    camera_ok = test_camera_access()
    if not camera_ok:
        print("\n❌ Camera test failed. Please fix camera issues before proceeding.")
        return
    
    # Test 2: Face Detection
    face_detection_ok, captured_encodings = test_face_detection()
    
    # Test 3: Face Comparison (if we captured encodings)
    if captured_encodings:
        test_face_comparison(captured_encodings)
    
    # Test 4: Database
    db_ok = test_database_saving()
    
    # Final Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Camera Access:     {'✓ PASS' if camera_ok else '✗ FAIL'}")
    print(f"Face Detection:    {'✓ PASS' if face_detection_ok else '✗ FAIL'}")
    print(f"Database Operations: {'✓ PASS' if db_ok else '✗ FAIL'}")
    
    if camera_ok and face_detection_ok and db_ok:
        print("\n✓ ALL TESTS PASSED!")
        print("\nYour system is ready to use. You can now run:")
        print("  python main.py")
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
