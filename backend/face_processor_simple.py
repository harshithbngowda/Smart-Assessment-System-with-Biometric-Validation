"""
Simple Face Processing Module (Fallback)
Works without complex dependencies like dlib and face_recognition
"""

import cv2
import numpy as np
import pickle
import os
from datetime import datetime

def save_face_encoding(user, image_or_images):
    """Save face encoding for a user (simplified version). Accepts single image or list."""
    try:
        # Handle both single image and list of images
        if isinstance(image_or_images, list):
            images = [img for img in image_or_images if isinstance(img, np.ndarray) and img is not None]
            if not images:
                return False, "No valid images provided"
            # Use the first valid image for simplicity
            image = images[0]
        else:
            image = image_or_images
        
        if image is None or not isinstance(image, np.ndarray):
            return False, "Invalid image format"
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Simple face detection using OpenCV's Haar Cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
        # Use more lenient parameters for webcam frames
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30))
        
        if len(faces) == 0:
            return False, "No face detected in the image"
        
        # If multiple faces, use the largest one (primary person in frame)
        if len(faces) > 1:
            faces = sorted(faces, key=lambda face: face[2] * face[3], reverse=True)
        
        # Extract face region (largest face)
        (x, y, w, h) = faces[0]
        face_region = gray[y:y+h, x:x+w]
        
        # Resize to standard size
        face_region = cv2.resize(face_region, (100, 100))
        
        # Create a simple encoding (flatten the image)
        face_encoding = face_region.flatten()
        
        # Save face encoding
        user.face_encoding = pickle.dumps(face_encoding)
        user.face_registered_at = datetime.utcnow()
        
        return True, "Face registered successfully"
        
    except Exception as e:
        return False, f"Error processing face: {str(e)}"

def verify_face(user, image, tolerance=0.6):
    """Verify if the face matches the registered user (simplified version)"""
    try:
        if not user.face_encoding:
            return False, 0.0
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Simple face detection using OpenCV's Haar Cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return False, 0.0
        
        # Extract face region
        (x, y, w, h) = faces[0]
        face_region = gray[y:y+h, x:x+w]
        
        # Resize to standard size
        face_region = cv2.resize(face_region, (100, 100))
        
        # Create encoding
        current_encoding = face_region.flatten()
        
        # Load stored face encoding
        stored_encoding = pickle.loads(user.face_encoding)
        
        # Simple similarity check (normalized cross-correlation)
        similarity = np.corrcoef(stored_encoding, current_encoding)[0, 1]
        
        if np.isnan(similarity):
            similarity = 0.0
        
        # Convert to confidence (0-1 scale)
        confidence = max(0, min(1, (similarity + 1) / 2))
        
        # Check if it matches based on tolerance
        matches = confidence > tolerance
        
        return matches, confidence
            
    except Exception as e:
        print(f"Error verifying face: {e}")
        return False, 0.0

def detect_multiple_faces(image):
    """Detect if multiple faces are present in the image"""
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Simple face detection using OpenCV's Haar Cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        return len(faces) > 1, len(faces)
        
    except Exception as e:
        print(f"Error detecting multiple faces: {e}")
        return False, 0

def detect_phone_usage(image):
    """Detect if a phone is being used (basic implementation)"""
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Simple phone detection using edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Look for rectangular shapes that might be phones
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        phone_like_objects = 0
        for contour in contours:
            # Approximate the contour
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Check if it's roughly rectangular (4 corners)
            if len(approx) == 4:
                # Check aspect ratio (phones are typically taller than wide)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = h / w if w > 0 else 0
                
                if 1.5 < aspect_ratio < 3.0 and w > 50 and h > 100:
                    phone_like_objects += 1
        
        return phone_like_objects > 0, phone_like_objects
        
    except Exception as e:
        print(f"Error detecting phone usage: {e}")
        return False, 0

def monitor_cheating_attempts(image, user):
    """Monitor for various cheating attempts"""
    results = {
        'face_verified': False,
        'face_confidence': 0.0,
        'multiple_faces': False,
        'face_count': 0,
        'phone_detected': False,
        'phone_count': 0,
        'overall_status': 'safe'
    }
    
    try:
        # Face verification
        face_verified, confidence = verify_face(user, image)
        results['face_verified'] = face_verified
        results['face_confidence'] = confidence
        
        # Multiple face detection
        multiple_faces, face_count = detect_multiple_faces(image)
        results['multiple_faces'] = multiple_faces
        results['face_count'] = face_count
        
        # Phone detection
        phone_detected, phone_count = detect_phone_usage(image)
        results['phone_detected'] = phone_detected
        results['phone_count'] = phone_count
        
        # Determine overall status
        if not face_verified or confidence < 0.5:
            results['overall_status'] = 'face_mismatch'
        elif multiple_faces:
            results['overall_status'] = 'multiple_faces'
        elif phone_detected:
            results['overall_status'] = 'phone_detected'
        else:
            results['overall_status'] = 'safe'
        
        return results
        
    except Exception as e:
        print(f"Error monitoring cheating attempts: {e}")
        results['overall_status'] = 'error'
        return results
