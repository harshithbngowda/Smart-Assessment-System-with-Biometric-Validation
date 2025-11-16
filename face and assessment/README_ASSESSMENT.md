# Proctored Assessment System - Quick Start

## What's New

This update adds a **fullscreen proctored assessment system** with:
- ✅ Fullscreen mode with no window controls
- ✅ 70/30 split layout (questions left, monitoring right)
- ✅ Support for 3 question types: MCQ, Descriptive, Programming
- ✅ Real-time camera monitoring
- ✅ Window focus detection
- ✅ Automatic answer saving to JSON
- ✅ Warning system with automatic termination

## Quick Start

### 1. Start the Application
```bash
python main.py
```

### 2. Register a Student
- Enter name and student ID in "Student Registration" section
- Click "Register Student"
- Look at camera for face capture (system captures 20 photos automatically)
- Wait for "Registration completed successfully"

### 3. Start Assessment
- Enter the same name and ID in "Online Assessment (Proctored)" section
- Click "Start Assessment"
- Select a question file from `input/` folder (or use provided samples)
- Assessment window goes fullscreen automatically

### 4. Take Assessment
- Answer questions using provided input methods:
  - **MCQ**: Select radio button
  - **Descriptive**: Type in text area
  - **Programming**: Write code in code editor
- Click "Submit Answer" to save each answer
- Use Previous/Next to navigate questions
- Click "Finish Assessment" when done

### 5. Results
- Answers saved automatically to `output/` folder
- File format: `assessment_<student_id>_<timestamp>.json`
- Contains all questions, answers, and warnings

## Sample Question Files

Located in `input/` folder:
- `sample_mcq_questions.json` - 5 multiple choice questions
- `sample_descriptive_questions.json` - 5 essay questions
- `sample_programming_questions.json` - 5 coding questions
- `sample_mixed_assessment.json` - 10 mixed questions

## Question File Format

### MCQ Question
```json
{
  "question": "What does CPU stand for?",
  "options": [
    "Central Processing Unit",
    "Computer Personal Unit",
    "Central Program Utility",
    "Central Processor Universal"
  ],
  "correct_answer": "A",
  "type": "mcq"
}
```

### Descriptive Question
```json
{
  "question": "Explain the concept of OOP and its four main principles.",
  "correct_answer": "Sample expected answer here",
  "type": "descriptive"
}
```

### Programming Question
```json
{
  "question": "Write a function to check if a number is prime.",
  "answer": "def is_prime(n):\n    # code here",
  "type": "programming"
}
```

## Assessment Features

### Left Side (70% - Questions)
- Question counter (e.g., "Question 1 of 10")
- Question text with scrolling
- Answer input (changes based on question type)
- Navigation buttons (Previous, Next, Submit Answer, Finish Assessment)
- Timer display

### Right Side (30% - Monitoring)
- Live camera feed
- Warning counter (color-coded)
- Identity verification status
- Violation log with timestamps

## Monitoring & Warnings

### Warning Triggers
1. **Multiple faces detected** - Someone else in frame
2. **Unknown person** - Face doesn't match registered student
3. **Window focus lost** - Student switched windows
4. **Mobile phone detected** - Prohibited object (if YOLO enabled)

### Warning Limits
- Default: 10 warnings maximum
- Assessment auto-terminates at limit
- All warnings logged with timestamps
- Configurable in `config.py`

## Window Behavior

### Fullscreen Mode
- Automatically goes fullscreen on start
- No minimize/maximize/close buttons
- ESC key disabled
- Cannot resize or move

### Exit Methods
1. Click "Finish Assessment" button (normal completion)
2. Reach maximum warnings (forced termination)

**Note**: Attempting to close the window shows a warning message.

## File Structure

```
face and assessment/
├── main.py                      # Main application (updated)
├── assessment_window.py         # New fullscreen assessment module
├── exam_monitor.py             # Existing monitoring module
├── database_manager.py         # Student data management
├── config.py                   # Configuration settings
├── input/                      # Question files
│   ├── sample_mcq_questions.json
│   ├── sample_descriptive_questions.json
│   ├── sample_programming_questions.json
│   └── sample_mixed_assessment.json
├── output/                     # Answer submissions (auto-created)
│   └── assessment_<id>_<timestamp>.json
└── data/
    ├── faces/                  # Student face data
    ├── logs/                   # System logs
    └── students.db            # Student database
```

## Troubleshooting

### Camera not working
```bash
# Check camera index in config.py
CAMERA_INDEX = 0  # Try 1, 2, etc. if 0 doesn't work
```

### Student not recognized
- Ensure good lighting during registration
- Face camera directly
- Remove glasses if causing issues
- Re-register student if needed

### Assessment won't start
- Verify student is registered first
- Check question file format is valid JSON
- Ensure camera is available

### Window focus warnings
- Don't click outside assessment window
- Close notifications/popups before starting
- Focus only on assessment window

## Configuration Options

Edit `config.py`:

```python
# Warning system
MAX_WARNINGS = 10                    # Maximum warnings before termination
WARNING_COOLDOWN = 3                 # Seconds between warnings

# Monitoring intervals
IDENTITY_CHECK_INTERVAL = 0.8        # Face recognition frequency (seconds)
OBJECT_CHECK_INTERVAL = 1.0          # Object detection frequency

# Camera settings
CAMERA_WIDTH = 960
CAMERA_HEIGHT = 540
CAMERA_FPS = 30

# Face recognition
ARC_FACE_SIM_THRESHOLD = 0.40        # Face match threshold (0.3-0.6)

# Object detection
ENABLE_YOLO = True                   # Enable/disable phone detection
PHONE_DETECTION_CONFIDENCE = 0.10    # Detection sensitivity
```

## Output Format

Example answer file (`output/assessment_12345_20241014_155430.json`):

```json
{
  "student_name": "John Doe",
  "student_id": "12345",
  "timestamp": "20241014_155430",
  "total_questions": 10,
  "answered_questions": 9,
  "warnings_count": 2,
  "answers": [
    {
      "serial_no": 1,
      "question": "What does CPU stand for?",
      "type": "mcq",
      "options": [...],
      "student_answer": "A",
      "correct_answer": "A"
    },
    {
      "serial_no": 2,
      "question": "Explain OOP principles",
      "type": "descriptive",
      "student_answer": "Student's essay answer here...",
      "correct_answer": "Expected answer..."
    },
    {
      "serial_no": 3,
      "question": "Write a prime number checker",
      "type": "programming",
      "student_answer": "def is_prime(n):\n    ...",
      "correct_answer": "def is_prime(n):\n    ..."
    }
  ]
}
```

## Best Practices

### For Students
1. Find a quiet, well-lit location
2. Ensure stable internet connection
3. Close unnecessary applications
4. Test camera before starting
5. Read instructions carefully
6. Save answers frequently
7. Don't leave assessment window

### For Administrators
1. Test with sample questions first
2. Brief students on rules and monitoring
3. Verify camera requirements
4. Set appropriate warning limits
5. Review output files promptly
6. Keep question files backed up

## Legacy Features

The old "Exam Monitoring (Video Only)" section is still available for:
- Simple video monitoring without questions
- Testing face recognition
- Camera setup verification

## Support & Logs

### View Logs
```bash
# Check system logs
cat data/logs/main.log

# Check Python console output for real-time info
```

### Common Issues

**Issue**: "No question file selected"
**Solution**: Select a valid JSON file from `input/` folder

**Issue**: "Could not load student's face data"
**Solution**: Register student first using registration section

**Issue**: Too many warnings
**Solution**: Ensure student:
- Faces camera
- Stays in frame
- Doesn't switch windows
- Is alone in frame

## Updates Made

### New Files
- ✅ `assessment_window.py` - Complete fullscreen assessment module
- ✅ `assessment_helpers.py` - Helper functions (reference)
- ✅ `ASSESSMENT_GUIDE.md` - Detailed user guide
- ✅ Sample question JSON files (4 files)

### Modified Files
- ✅ `main.py` - Added assessment integration
- ✅ Created `input/` and `output/` directories

### Features Implemented
- ✅ Fullscreen mode with no controls
- ✅ 70/30 split layout
- ✅ MCQ with radio buttons
- ✅ Descriptive with text area
- ✅ Programming with code editor
- ✅ Question navigation (Previous/Next)
- ✅ Answer submission and storage
- ✅ Camera monitoring (right side)
- ✅ Warning counter display
- ✅ Identity verification
- ✅ Window focus monitoring
- ✅ Automatic termination on max warnings
- ✅ JSON output with all data

## Next Steps

1. Run the application: `python main.py`
2. Register a test student
3. Start an assessment with sample questions
4. Test all question types
5. Verify output files are created
6. Review monitoring features

---

**For detailed instructions, see `ASSESSMENT_GUIDE.md`**
