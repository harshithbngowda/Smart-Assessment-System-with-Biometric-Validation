"""
Test face verification - Check if registered face is recognized correctly
"""
import argparse
import cv2
import sys
from pathlib import Path

# Make parent (backend/) importable
PARENT_DIR = str(Path(__file__).resolve().parents[1])
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from app import app
from models import db, User
from face_processor_advanced import verify_face

def capture_single_frame(device_index=0):
    """Capture a single frame from webcam"""
    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam")
    
    print("Webcam opened. Press SPACE to capture, ESC to cancel...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Show preview
        cv2.imshow('Face Verification Test - Press SPACE to capture, ESC to cancel', frame)
        
        key = cv2.waitKey(1)
        if key == 32:  # SPACE key
            cap.release()
            cv2.destroyAllWindows()
            return frame
        elif key == 27:  # ESC key
            cap.release()
            cv2.destroyAllWindows()
            return None
    
    cap.release()
    cv2.destroyAllWindows()
    return None

def main():
    parser = argparse.ArgumentParser(description="Test face verification against registered user")
    parser.add_argument('--email', required=True, help='Email of registered user to verify against')
    parser.add_argument('--device', type=int, default=0, help='Camera device index (default: 0)')
    
    args = parser.parse_args()
    
    with app.app_context():
        # Get user
        user = User.query.filter_by(email=args.email).first()
        if not user:
            print(f"❌ No user found with email: {args.email}")
            sys.exit(1)
        
        if not user.face_encoding:
            print(f"❌ User {args.email} has no face registered")
            sys.exit(1)
        
        print(f"✅ Found user: {user.name} ({user.email})")
        print(f"✅ User has face encodings registered")
        print()
        print("=" * 60)
        print("INSTRUCTIONS:")
        print("1. Position yourself in front of the camera")
        print("2. Press SPACE when ready to capture")
        print("3. The system will verify if your face matches the registered face")
        print("=" * 60)
        print()
        
        # Capture frame
        frame = capture_single_frame(args.device)
        
        if frame is None:
            print("❌ Capture cancelled")
            sys.exit(0)
        
        print("✅ Frame captured. Verifying...")
        
        # Verify face
        matches, confidence = verify_face(user, frame)
        
        print()
        print("=" * 60)
        print("VERIFICATION RESULTS:")
        print("=" * 60)
        print(f"Match: {'✅ YES' if matches else '❌ NO'}")
        print(f"Confidence: {confidence:.2%}")
        print()
        
        if matches:
            print("🎉 SUCCESS! The face matches the registered user.")
            print(f"   The system correctly identified you as {user.name}")
        else:
            print("⚠️  FAILED! The face does NOT match the registered user.")
            print(f"   This person is NOT {user.name}")
        
        print("=" * 60)
        
        # Interpretation
        print()
        print("WHAT THIS MEANS:")
        if matches:
            print("✅ Your face is correctly registered")
            print("✅ The system will recognize YOU during exams")
            print("✅ It will reject other people trying to use your account")
        else:
            print("❌ Either:")
            print("   1. You are testing with a different person (expected)")
            print("   2. Lighting is very different from registration")
            print("   3. Camera angle is too different")
            print()
            print("💡 TIP: If this is YOU and it failed:")
            print("   - Try with similar lighting as registration")
            print("   - Face the camera directly")
            print("   - Move to the same distance from camera")

if __name__ == '__main__':
    main()
