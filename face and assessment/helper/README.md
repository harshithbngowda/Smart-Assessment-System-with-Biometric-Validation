# Biometric Anti-Cheating Assessment System

A comprehensive biometric system for preventing cheating during online assessments using facial recognition and object detection.

## Features

### 🔐 Student Registration
- **Multi-photo capture**: Takes multiple photos for high accuracy
- **Image augmentation**: Creates variations for better training
- **Secure storage**: Encrypted face encodings stored locally
- **Unique ID system**: Each student gets a unique identifier

### 👁️ Real-time Monitoring
- **Identity verification**: Continuous face matching during exams
- **Impersonation detection**: Alerts when unknown person detected
- **Multiple face detection**: Warns if multiple people present
- **Object detection**: Detects phones and mobile devices
- **Warning system**: 5-warning limit before exam termination

### 📊 Comprehensive Logging
- **Session tracking**: Complete exam session records
- **Violation logs**: Detailed warning and violation history
- **Database storage**: SQLite database for all data
- **Audit trail**: Full accountability system

## System Requirements

### Hardware
- **Camera**: Webcam or built-in camera
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 2GB free space
- **OS**: Windows 10/11, macOS, or Linux

### Software Dependencies
- Python 3.8 or higher
- OpenCV
- face_recognition library
- dlib
- tkinter (usually included with Python)

## Installation

### 1. Clone or Download
```bash
git clone <repository-url>
cd "face and assessment"
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install System Dependencies

#### Windows
- Install Microsoft Visual C++ 14.0 or greater
- Install CMake from https://cmake.org/download/

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev
```

#### macOS
```bash
brew install cmake
```

### 4. Download YOLO Model Files (Optional - for object detection)
Create a `data/models/yolo/` directory and download:
- [yolov3.weights](https://pjreddie.com/media/files/yolov3.weights)
- [yolov3.cfg](https://github.com/pjreddie/darknet/blob/master/cfg/yolov3.cfg)
- [coco.names](https://github.com/pjreddie/darknet/blob/master/data/coco.names)

## Usage

### Starting the Application
```bash
python main.py
```

### Student Registration Process
1. **Launch Application**: Run `main.py`
2. **Enter Details**: Input student name and unique ID
3. **Click "Register Student"**: Start the registration process
4. **Photo Capture**: 
   - Look directly at the camera
   - System will automatically capture 10 photos
   - Move head slightly between captures for better accuracy
5. **Processing**: System processes and augments images
6. **Completion**: Registration successful message appears

### Exam Monitoring Process
1. **Enter Student Details**: Input name and ID of registered student
2. **Click "Start Exam Monitoring"**: Begin monitoring session
3. **Identity Verification**: System continuously verifies student identity
4. **Violation Detection**: 
   - Unknown person detection
   - Multiple face detection
   - Phone/mobile device detection
5. **Warning System**: Up to 5 warnings before exam termination
6. **Session End**: Click "End Exam" or automatic termination

## File Structure

```
face and assessment/
├── main.py                 # Main application entry point
├── config.py              # Configuration settings
├── database_manager.py    # Database operations
├── facial_registration.py # Student registration module
├── exam_monitor.py        # Exam monitoring module
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── data/                 # Data directory (created automatically)
    ├── faces/            # Student face data
    ├── logs/             # System logs
    ├── models/           # YOLO model files
    └── students.db       # SQLite database
```

## Configuration

Edit `config.py` to customize:
- Camera settings (resolution, FPS)
- Face detection parameters
- Warning limits
- File paths
- UI colors and sizes

## Security Features

- **Local Storage**: All data stored locally, no cloud dependency
- **Encrypted Encodings**: Face data stored as mathematical encodings
- **No Raw Images**: Original photos not saved after processing
- **Audit Trail**: Complete logging of all activities
- **Session Isolation**: Each exam session tracked separately

## Troubleshooting

### Common Issues

#### Camera Not Working
- Check camera permissions
- Ensure no other applications are using the camera
- Try changing `CAMERA_INDEX` in config.py

#### Face Recognition Errors
- Ensure good lighting
- Look directly at camera during registration
- Re-register if accuracy is poor

#### Installation Issues
- Install Visual C++ redistributables on Windows
- Use Python 3.8-3.10 for best compatibility
- Install dlib separately if needed: `pip install dlib`

#### YOLO Model Not Loading
- Download all three YOLO files
- Check file paths in config.py
- Object detection will be disabled if files missing

### Performance Tips
- Use `hog` model for faster processing (default)
- Use `cnn` model for better accuracy (slower)
- Adjust `FACE_RECOGNITION_THRESHOLD` for sensitivity
- Close other applications during exams

## Technical Details

### Face Recognition Process
1. **Capture**: Multiple photos taken during registration
2. **Detection**: Face locations identified using HOG/CNN
3. **Encoding**: 128-dimensional face encodings generated
4. **Augmentation**: Images modified for better training
5. **Storage**: Encodings saved as pickle files
6. **Verification**: Real-time comparison during exams

### Object Detection
- Uses YOLOv3 for real-time object detection
- Specifically trained to detect mobile phones
- Configurable confidence thresholds
- Non-maximum suppression for accuracy

### Database Schema
- **Students**: Registration data and face encoding paths
- **Exam Sessions**: Session tracking and timing
- **Warnings**: Detailed violation records

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review log files in `data/logs/`
3. Ensure all dependencies are installed
4. Verify camera and system permissions

## License

This project is for educational and assessment purposes. Please ensure compliance with privacy laws and institutional policies when using biometric data.

## Version History

- **v1.0**: Initial release with basic functionality
- Face registration and verification
- Real-time monitoring
- Warning system
- Database logging
