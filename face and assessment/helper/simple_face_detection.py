"""
Simple Face Detection Module using OpenCV
A basic implementation that works without complex dependencies
"""

import cv2
import numpy as np
import os
import pickle
import logging
from sklearn.metrics.pairwise import euclidean_distances

class SimpleFaceRecognition:
    def __init__(self):
        # Load OpenCV's pre-trained face detection model
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.logger = logging.getLogger(__name__)
        
        # Note: Using basic feature extraction without cv2.face module
        
    def detect_faces(self, image):
        """Detect faces in an image and return bounding boxes"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
        
        # Convert to (top, right, bottom, left) format for compatibility
        face_locations = []
        for (x, y, w, h) in faces:
            # Correct format: (top, right, bottom, left)
            face_locations.append((y, x + w, y + h, x))
        
        return face_locations
    
    def extract_face_features(self, image, face_location=None):
        """Extract robust face features using multiple techniques"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            if face_location:
                top, right, bottom, left = face_location
                face_roi = gray[top:bottom, left:right]
            else:
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
                if len(faces) == 0:
                    return None
                x, y, w, h = faces[0]
                face_roi = gray[y:y+h, x:x+w]
            
            # Check if face_roi is valid
            if face_roi.size == 0:
                return None
            
            # Resize face to standard size
            face_roi = cv2.resize(face_roi, (100, 100))
            
            # Normalize the image
            face_roi = cv2.equalizeHist(face_roi)
            
            # Extract multiple features
            # 1. Histogram features
            hist = cv2.calcHist([face_roi], [0], None, [64], [0, 256])
            hist = hist.flatten()
            hist = hist / (np.sum(hist) + 1e-7)
            
            # 2. HOG-like features using gradients
            sobelx = cv2.Sobel(face_roi, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(face_roi, cv2.CV_64F, 0, 1, ksize=3)
            gradient_mag = np.sqrt(sobelx**2 + sobely**2)
            gradient_hist = np.histogram(gradient_mag.flatten(), bins=32)[0]
            gradient_hist = gradient_hist / (np.sum(gradient_hist) + 1e-7)
            
            # 3. Pixel intensity features (downsampled)
            pixel_features = cv2.resize(face_roi, (20, 20)).flatten()
            pixel_features = pixel_features / 255.0
            
            # Combine all features
            combined_features = np.concatenate([hist, gradient_hist, pixel_features])
            
            return combined_features
        except Exception as e:
            self.logger.error(f"Error extracting face features: {str(e)}")
            return None
    
    def compare_faces(self, known_encodings, face_encoding, tolerance=0.42):
        """Compare face encodings using euclidean distance"""
        if not known_encodings or face_encoding is None:
            return []
        
        # Calculate euclidean distances
        distances = euclidean_distances([face_encoding], known_encodings)[0]
        
        # Use a stricter threshold to reject unknown people
        # Lower distance = more similar
        # Stricter multiplier to only accept registered student
        threshold = tolerance * 11  # Stricter - won't accept random people
        matches = distances <= threshold
        
        return matches.tolist()
    
    def face_distance(self, known_encodings, face_encoding):
        """Calculate face distances using euclidean distance"""
        if not known_encodings or face_encoding is None:
            return []
        
        distances = euclidean_distances([face_encoding], known_encodings)[0]
        
        # Normalize distances
        max_distance = np.max(distances) if len(distances) > 0 else 1
        normalized_distances = distances / (max_distance + 1e-7)
        
        return normalized_distances.tolist()

# Global instance for easy access
simple_face_recognition = SimpleFaceRecognition()

# Compatibility functions to match face_recognition library API
def face_locations(image, number_of_times_to_upsample=1, model="hog"):
    """Detect face locations in an image"""
    return simple_face_recognition.detect_faces(image)

def face_encodings(image, known_face_locations=None, num_jitters=1, model="small"):
    """Extract face encodings from an image"""
    encodings = []
    
    if known_face_locations is None:
        known_face_locations = face_locations(image)
    
    for face_location in known_face_locations:
        encoding = simple_face_recognition.extract_face_features(image, face_location)
        if encoding is not None:
            encodings.append(encoding)
    
    return encodings

def compare_faces(known_face_encodings, face_encoding_to_check, tolerance=0.6):
    """Compare face encodings"""
    return simple_face_recognition.compare_faces(known_face_encodings, face_encoding_to_check, tolerance)

def face_distance(face_encodings, face_to_compare):
    """Calculate face distances"""
    return simple_face_recognition.face_distance(face_encodings, face_to_compare)
