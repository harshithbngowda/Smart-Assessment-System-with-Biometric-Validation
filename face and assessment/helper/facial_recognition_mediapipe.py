"""
Alternative Facial Recognition Module using MediaPipe
Replaces dlib-based face_recognition with MediaPipe for easier installation
"""

import cv2
import mediapipe as mp
import numpy as np
import os
import pickle
import logging
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

class MediaPipeFaceRecognition:
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize MediaPipe models
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.logger = logging.getLogger(__name__)
    
    def detect_faces(self, image):
        """Detect faces in an image and return bounding boxes"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_image)
        
        face_locations = []
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                h, w, _ = image.shape
                
                # Convert relative coordinates to absolute
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                # Return in (top, right, bottom, left) format for compatibility
                face_locations.append((y, x + width, y + height, x))
        
        return face_locations
    
    def extract_face_encoding(self, image, face_location=None):
        """Extract face encoding using MediaPipe face mesh landmarks"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            
            # Extract key landmark points for face encoding
            landmarks = []
            for landmark in face_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
            
            # Convert to numpy array and normalize
            encoding = np.array(landmarks, dtype=np.float32)
            encoding = normalize([encoding])[0]  # L2 normalization
            
            return encoding
        
        return None
    
    def compare_faces(self, known_encodings, face_encoding, tolerance=0.6):
        """Compare face encodings using cosine similarity"""
        if not known_encodings or face_encoding is None:
            return []
        
        # Calculate cosine similarities
        similarities = cosine_similarity([face_encoding], known_encodings)[0]
        
        # Convert similarity to distance (1 - similarity) and compare with tolerance
        distances = 1 - similarities
        matches = distances <= tolerance
        
        return matches.tolist()
    
    def face_distance(self, known_encodings, face_encoding):
        """Calculate face distances using cosine distance"""
        if not known_encodings or face_encoding is None:
            return []
        
        similarities = cosine_similarity([face_encoding], known_encodings)[0]
        distances = 1 - similarities
        
        return distances.tolist()

# Global instance for easy access
face_recognition_mp = MediaPipeFaceRecognition()

# Compatibility functions to match face_recognition library API
def face_locations(image, number_of_times_to_upsample=1, model="hog"):
    """Detect face locations in an image"""
    return face_recognition_mp.detect_faces(image)

def face_encodings(image, known_face_locations=None, num_jitters=1, model="small"):
    """Extract face encodings from an image"""
    encodings = []
    
    if known_face_locations is None:
        known_face_locations = face_locations(image)
    
    for face_location in known_face_locations:
        encoding = face_recognition_mp.extract_face_encoding(image, face_location)
        if encoding is not None:
            encodings.append(encoding)
    
    return encodings

def compare_faces(known_face_encodings, face_encoding_to_check, tolerance=0.6):
    """Compare face encodings"""
    return face_recognition_mp.compare_faces(known_face_encodings, face_encoding_to_check, tolerance)

def face_distance(face_encodings, face_to_compare):
    """Calculate face distances"""
    return face_recognition_mp.face_distance(face_encodings, face_to_compare)
