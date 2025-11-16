import argparse
import base64
import cv2
import sys
from io import BytesIO
from PIL import Image
from pathlib import Path

# Make parent (backend/) importable when running from tools/
PARENT_DIR = str(Path(__file__).resolve().parents[1])
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Import Flask app context and models
try:
    from app import app
    from models import db, User
    from face_processor_advanced import save_face_encoding
except Exception as e:
    print(f"Error importing backend modules: {e}")
    sys.exit(1)

def frame_to_base64(frame):
    # Kept for reference; not used in the raw-frame path
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    buf = BytesIO()
    pil_img.save(buf, format='JPEG', quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{b64}"

def capture_frames(device_index: int, frames: int, width: int, height: int):
    cap = cv2.VideoCapture(device_index)
    if width:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    if not cap.isOpened():
        raise RuntimeError("Could not open webcam. Ensure no other app is using it and camera permission is enabled.")

    images = []
    try:
        for i in range(frames):
            ok, frame = cap.read()
            if not ok or frame is None:
                raise RuntimeError("Failed to read frame from webcam")
            images.append(frame)  # pass raw numpy frames to processor
            # brief delay ~150ms
            cv2.waitKey(150)
        return images
    finally:
        cap.release()


def main():
    parser = argparse.ArgumentParser(description="Test face registration pipeline against the backend DB")
    parser.add_argument('--email', required=True, help='Student email to attach face encodings to')
    parser.add_argument('--frames', type=int, default=15, help='Number of frames to capture (default 15)')
    parser.add_argument('--device', type=int, default=0, help='Webcam device index (default 0)')
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--height', type=int, default=480)
    args = parser.parse_args()

    with app.app_context():
        user = User.query.filter_by(email=args.email).first()
        if not user:
            print(f"No user found with email: {args.email}")
            sys.exit(1)
        if user.role != 'student':
            print(f"User {args.email} is not a student (role={user.role}). Aborting.")
            sys.exit(1)

        print(f"Capturing {args.frames} frames from webcam device {args.device}...")
        images = capture_frames(args.device, args.frames, args.width, args.height)
        print(f"Captured {len(images)} frames. Uploading to processor (raw frames)...")

        ok, message = save_face_encoding(user, images)
        print(f"Processor response: ok={ok}, message='{message}'")

        if ok:
            db.session.commit()
            print("DB commit successful. Face data saved to user.face_encoding.")
        else:
            print("Processor reported failure. DB not committed.")
            sys.exit(2)

if __name__ == '__main__':
    main()
