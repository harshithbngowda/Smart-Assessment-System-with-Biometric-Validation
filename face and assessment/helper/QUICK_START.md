# Quick Start Guide - Biometric Anti-Cheating System

## ✅ **FIXES APPLIED**

All critical bugs have been fixed:
- ✓ Face detection now working properly
- ✓ Face encodings save correctly to database
- ✓ Camera access improved
- ✓ Better error handling and feedback
- ✓ Detailed logging for debugging

---

## 📋 **Prerequisites**

1. **Python 3.8+** installed
2. **Webcam** connected and working
3. **Virtual environment** activated (recommended)

---

## 🚀 **Installation Steps**

### Step 1: Activate Virtual Environment
```powershell
cd "d:/hbngo/Desktop/face and assessment"
.\biometric_env\Scripts\Activate.ps1
```

### Step 2: Verify Installations
```powershell
pip list
```

You should see:
- opencv-python
- scikit-learn
- numpy
- Pillow

---

## 🧪 **Testing Before Use**

**IMPORTANT:** Run the test script first to verify everything works!

```powershell
python test_camera_face.py
```

This will:
- Test camera access
- Test face detection in real-time
- Show you a preview window
- Verify database operations

**Instructions during test:**
- Look at your camera when the window opens
- Press **'c'** to capture test face encodings
- Press **'q'** to quit the test
- Check if faces are detected (green rectangles)

---

## 🎯 **Running the Main Application**

```powershell
python main.py
```

---

## 📝 **How to Register a Student**

1. **Open the application** (`python main.py`)

2. **In the "Student Registration" section:**
   - Enter Student Name (e.g., "John Doe")
   - Enter Unique ID (e.g., "STU001")
   - Click **"Register Student"**

3. **Registration Window Opens:**
   - Your camera will activate
   - You'll see a live feed with face detection
   - Click **"Start Capture"** when ready

4. **During Capture:**
   - Look directly at the camera
   - Keep your face in the frame
   - The system will automatically take 15 photos
   - Move your head slightly between captures
   - Progress bar shows how many photos captured

5. **Processing:**
   - System creates face encodings
   - Augments images for better accuracy
   - Saves data to database
   - Shows success message with details

6. **Verification:**
   - Check the console/terminal output
   - Should show:
     ```
     📝 Registration Summary:
        Student: John Doe
        ID: STU001
        Photos captured: 15
        Face encodings: 90
        ✓ Encodings saved to: data/faces/student_STU001/face_encodings.pkl
        ✓ Student registered in database
     ```

---

## 🎓 **How to Start Exam Monitoring**

1. **In the "Exam Monitoring" section:**
   - Enter the registered student's name
   - Enter their unique ID
   - Click **"Start Exam Monitoring"**

2. **Monitoring Window Opens:**
   - Shows live camera feed
   - Displays identity verification status
   - Shows warning counter
   - Logs all violations

3. **What the System Monitors:**
   - ✓ Is the correct student taking the exam?
   - ✓ Are there multiple people in view?
   - ✓ Is the student's face visible?
   - ✓ Are there prohibited objects (if YOLO enabled)?

4. **Warning System:**
   - Max 5 warnings allowed
   - Each violation adds a warning
   - At 5 warnings, exam automatically terminates
   - All violations logged in database

5. **Ending the Exam:**
   - Click **"End Exam"** button
   - Shows exam summary
   - All data saved to database

---

## 🔍 **Checking Saved Data**

### Check Registered Students:
```python
from database_manager import DatabaseManager

db = DatabaseManager()
students = db.get_all_students()

for student in students:
    print(f"Name: {student['name']}, ID: {student['student_id']}")
```

### Check Face Encodings Folder:
```powershell
dir "data/faces"
```

You should see folders like `student_STU001` containing `face_encodings.pkl`

### Check Database:
```powershell
# View database file
dir "data/students.db"
```

---

## ⚠️ **Troubleshooting**

### Problem: "Cannot access camera"
**Solution:**
- Close other applications using the camera
- Check camera permissions in Windows Settings
- Try changing `CAMERA_INDEX` in `config.py` to 1

### Problem: "No face detected"
**Solution:**
- Ensure good lighting
- Look directly at camera
- Remove glasses if causing issues
- Move closer to camera

### Problem: "Face encodings not saving"
**Solution:**
- Check `data/faces/` folder exists
- Run with administrator privileges
- Check console output for specific errors

### Problem: "Face recognition not accurate"
**Solution:**
- Re-register with better lighting
- Capture more photos during registration
- Adjust `FACE_RECOGNITION_THRESHOLD` in `config.py` (lower = stricter)

---

## 📊 **Understanding the Console Output**

**During Registration:**
```
📝 Registration Summary:
   Student: John Doe
   ID: STU001
   Photos captured: 15
   Face encodings: 90  # 15 photos × 6 augmented versions
   ✓ Encodings saved to: data/faces/student_STU001/face_encodings.pkl
   ✓ Student registered in database
```

**During Monitoring:**
- Green status = Identity verified ✓
- Red status = Violation detected ✗
- Warnings are logged in real-time

---

## 🎨 **Tips for Best Results**

### For Registration:
1. **Good lighting** - Natural light works best
2. **Plain background** - Avoid clutter
3. **Face the camera directly**
4. **Remove accessories** that may change (hat, sunglasses)
5. **Neutral expression** initially
6. **Vary slightly** during capture (small head movements)

### For Monitoring:
1. **Same lighting conditions** as registration
2. **Same position** relative to camera
3. **Keep face visible** at all times
4. **Avoid obstructions** (hands, objects)

---

## 📁 **Project Structure**

```
face and assessment/
├── main.py                    # Main application
├── config.py                  # Settings and configuration
├── database_manager.py        # Database operations
├── facial_registration.py     # Student registration logic
├── exam_monitor.py            # Exam monitoring logic
├── simple_face_detection.py   # Face detection engine
├── test_camera_face.py        # Testing script
├── requirements.txt           # Dependencies
├── QUICK_START.md            # This file
├── data/
│   ├── faces/                 # Student face encodings
│   ├── logs/                  # System logs
│   └── students.db            # SQLite database
└── biometric_env/             # Virtual environment
```

---

## 🔧 **Advanced Configuration**

Edit `config.py` to customize:

```python
# Increase photos for better accuracy
PHOTOS_PER_REGISTRATION = 20  # Default: 15

# Adjust face recognition strictness
FACE_RECOGNITION_THRESHOLD = 0.3  # Lower = stricter (0.1-0.5)

# Change warning limit
MAX_WARNINGS = 3  # Default: 5

# Adjust camera settings
CAMERA_INDEX = 0  # Try 1 if camera 0 doesn't work
CAMERA_WIDTH = 1280  # Higher = better quality
CAMERA_HEIGHT = 720
```

---

## ✅ **System is Working If:**

- ✓ Test script shows "ALL TESTS PASSED"
- ✓ Camera feed shows green rectangles around faces
- ✓ Registration completes and shows success message
- ✓ Console shows "✓ Student registered in database"
- ✓ Face encoding files appear in `data/faces/`
- ✓ Monitoring window opens for registered students
- ✓ Identity verification shows "Identity Verified ✓"

---

## 📞 **Getting Help**

If issues persist:

1. **Check console output** for error messages
2. **Run test script** to isolate the problem
3. **Check data folder** for saved files
4. **Verify camera works** in other applications
5. **Review logs** in `data/logs/`

---

## 🎉 **You're All Set!**

Your biometric anti-cheating system is now ready to use. Start by registering yourself as a test student, then try monitoring to see how it works!

**Remember:** Always run `test_camera_face.py` first if you encounter issues.
