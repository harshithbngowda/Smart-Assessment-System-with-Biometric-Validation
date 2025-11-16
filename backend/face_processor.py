"""
Face Processing Module
Integrates face recognition functionality from main.py
"""

import cv2
import numpy as np
import face_recognition
import pickle
import os
from datetime import datetime

def save_face_encoding(user, image):
    """Save face encoding for a user"""
    try:
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Find face locations
        face_locations = face_recognition.face_locations(rgb_image)
        
        if not face_locations:
            return False, "No face detected in the image"
        
        if len(face_locations) > 1:
            return False, "Multiple faces detected. Please ensure only one face is visible"
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        if not face_encodings:
            return False, "Could not extract face features"
        
        # Save face encoding
        face_encoding = face_encodings[0]
        user.face_encoding = pickle.dumps(face_encoding)
        user.face_registered_at = datetime.utcnow()
        
        return True, "Face registered successfully"
        
    except Exception as e:
        return False, f"Error processing face: {str(e)}"

def verify_face(user, image, tolerance=0.6):
    """Verify if the face matches the registered user"""
    try:
        if not user.face_encoding:
            return False, 0.0
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Find face locations
        face_locations = face_recognition.face_locations(rgb_image)
        
        if not face_locations:
            return False, 0.0
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        if not face_encodings:
            return False, 0.0
        
        # Load stored face encoding
        stored_encoding = pickle.loads(user.face_encoding)
        
        # Compare faces
        matches = face_recognition.compare_faces([stored_encoding], face_encodings[0], tolerance=tolerance)
        distances = face_recognition.face_distance([stored_encoding], face_encodings[0])
        
        if matches[0]:
            confidence = 1 - distances[0]
            return True, confidence
        else:
            return False, 1 - distances[0]
            
    except Exception as e:
        print(f"Error verifying face: {e}")
        return False, 0.0

def detect_multiple_faces(image):
    """Detect if multiple faces are present in the image"""
    try:
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Find face locations
        face_locations = face_recognition.face_locations(rgb_image)
        
        return len(face_locations) > 1, len(face_locations)
        
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