"""
Configuration file for Biometric Assessment System
Contains all system settings and parameters
"""

import os

class Config:
    # Directories
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    FACES_DIR = os.path.join(DATA_DIR, "faces")
    LOGS_DIR = os.path.join(DATA_DIR, "logs")
    MODELS_DIR = os.path.join(DATA_DIR, "models")
    
    # Database
    DATABASE_PATH = os.path.join(DATA_DIR, "students.db")
    
    # Camera settings
    CAMERA_INDEX = 0
    CAMERA_WIDTH = 960   # Lower resolution for smoother preview (was 1280)
    CAMERA_HEIGHT = 540  # Lower resolution for smoother preview (was 720)
    CAMERA_FPS = 30
    
    # Face detection/recognition settings
    FACE_DETECTION_CONFIDENCE = 0.5
    FACE_RECOGNITION_THRESHOLD = 0.42  # Stricter - won't accept random people
    MIN_FACE_SIZE = (50, 50)
    # ArcFace (InsightFace) cosine similarity threshold (higher = stricter)
    # Typical values: 0.30 (lenient) .. 0.60 (very strict). Recommended ~0.38-0.45
    ARC_FACE_SIM_THRESHOLD = 0.40
    
    # Registration settings
    PHOTOS_PER_REGISTRATION = 20  # More photos for maximum accuracy
    AUGMENTATION_COUNT = 6  # Balanced augmentations for speed
    AUGMENTATION_ENABLED = True  # Allow disabling to speed up
    AUGMENTATION_MAX_SECONDS = 20  # Cap augmentation time per registration
    FAST_MODE_DEFAULT = True  # Skip augmentation by default for speed
    FACE_ENCODING_MODEL = "hog"  # or "cnn" for better accuracy but slower
    
    # Monitoring settings
    MAX_WARNINGS = 10  # More forgiving (was 5)
    WARNING_COOLDOWN = 3  # seconds between warnings (increased)
    MONITORING_INTERVAL = 0.05  # main loop sleep (lower = more responsive)
    IDENTITY_CHECK_INTERVAL = 0.8  # seconds between ArcFace checks
    OBJECT_CHECK_INTERVAL = 1.0  # seconds between YOLO checks
    PREVIEW_FPS_MS = 100  # ms between GUI preview updates
    DRAW_BOXES_IN_PREVIEW = False  # Skip heavy detection overlays in preview for speed
    
    # Object detection settings
    ENABLE_YOLO = True
    PHONE_DETECTION_CONFIDENCE = 0.10  # Very sensitive for smaller/angled phones
    YOLO_INPUT_SIZE = 416  # better small-object detection
    YOLO_CONFIG_PATH = os.path.join(MODELS_DIR, "yolo", "yolov4-tiny.cfg")
    YOLO_WEIGHTS_PATH = os.path.join(MODELS_DIR, "yolo", "yolov4-tiny.weights")
    YOLO_CLASSES_PATH = os.path.join(MODELS_DIR, "yolo", "coco.names")
    
    # Phone/mobile related class IDs from COCO dataset
    PHONE_CLASS_IDS = [67]  # cell phone class ID in COCO
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # UI Settings
    WINDOW_TITLE = "Biometric Anti-Cheating System"
    MAIN_WINDOW_SIZE = "800x600"
    MONITOR_WINDOW_SIZE = "1000x700"
    
    # Colors (hex codes)
    PRIMARY_COLOR = "#3498db"
    SUCCESS_COLOR = "#27ae60"
    WARNING_COLOR = "#f39c12"
    ERROR_COLOR = "#e74c3c"
    BACKGROUND_COLOR = "#f0f0f0"
    TEXT_COLOR = "#2c3e50"
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [
            cls.DATA_DIR,
            cls.FACES_DIR,
            cls.LOGS_DIR,
            cls.MODELS_DIR,
            os.path.join(cls.MODELS_DIR, "yolo")
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    @classmethod
    def get_student_face_dir(cls, student_id):
        """Get the directory path for a specific student's face data"""
        return os.path.join(cls.FACES_DIR, f"student_{student_id}")
    
    @classmethod
    def get_log_file_path(cls, log_type="main"):
        """Get the path for log files"""
        return os.path.join(cls.LOGS_DIR, f"{log_type}.log")
