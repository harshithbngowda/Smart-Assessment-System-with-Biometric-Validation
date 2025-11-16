# Proctored Assessment System - User Guide

## Overview
This fullscreen proctored assessment system provides a secure environment for conducting online examinations with real-time monitoring and cheating detection.

## Key Features

### 1. **Fullscreen Mode**
- Assessment window goes fullscreen automatically
- No minimize, maximize, or close buttons
- Window can only be closed by finishing the assessment or reaching the warning limit
- ESC key is disabled

### 2. **Layout**
- **Left Side (70%)**: Question display and answer input area
- **Right Side (30%)**: Camera feed and warning display
  - Live camera monitoring
  - Warning counter
  - Identity verification status
  - Violation log

### 3. **Question Types Supported**

#### Multiple Choice Questions (MCQ)
- Radio buttons for options (A, B, C, D, etc.)
- Only one answer can be selected
- Options are displayed with clear labeling

#### Descriptive Questions
- Large text area for essay-type answers
- Word wrap enabled
- Scroll support for long answers

#### Programming Questions
- Code editor with monospace font
- Dark theme optimized for code
- Support for multi-line code
- No word wrap (preserves code formatting)

### 4. **Monitoring Features**

#### Face Recognition
- Continuous identity verification
- Detects if the registered student is present
- Warns if unknown person is detected
- Warns if multiple faces are detected (cheating attempt)

#### Window Focus Monitoring
- Detects when student switches to another window
- Issues warning for each window switch
- Counts as a cheating attempt

#### Object Detection (Optional)
- Detects mobile phones using YOLO
- Warns when prohibited objects are detected

### 5. **Warning System**
- Maximum 10 warnings allowed (configurable)
- Each violation adds a warning
- Color-coded warning counter:
  - Green: 0-5 warnings
  - Orange: 6-7 warnings
  - Red: 8+ warnings
- Assessment automatically terminates at max warnings
- All warnings logged with timestamps

## How to Use

### For Teachers/Administrators

#### 1. Prepare Question File
Create a JSON file with questions in the `input/` folder. Format:

```json
[
  {
    "question": "Question text here",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "A",
    "type": "mcq"
  },
  {
    "question": "Descriptive question text",
    "correct_answer": "Expected answer",
    "type": "descriptive"
  },
  {
    "question": "Programming question text",
    "answer": "Sample solution code",
    "type": "programming"
  }
]
```

**Sample files provided:**
- `sample_mcq_questions.json` - Multiple choice questions
- `sample_descriptive_questions.json` - Essay questions
- `sample_programming_questions.json` - Coding questions
- `sample_mixed_assessment.json` - Mix of all types

### For Students

#### 1. Register First
- Enter your name and unique student ID
- Click "Register Student"
- Look at the camera for face registration
- Wait for confirmation

#### 2. Start Assessment
- Enter the same name and student ID in "Online Assessment" section
- Click "Start Assessment"
- Select question file when prompted (or teacher provides file path)

#### 3. During Assessment
- **Answer questions**: Read and answer one question at a time
- **Navigation**: Use Previous/Next buttons to move between questions
- **Save answers**: Click "Submit Answer" after answering each question
- **Stay focused**: 
  - Look at camera regularly
  - Don't switch windows
  - Don't have others in frame
  - No mobile phones
- **Monitor warnings**: Check warning counter on right side

#### 4. Finishing Assessment
- Review all answers using Previous/Next buttons
- Click "Finish Assessment" when done
- Confirm completion
- Answers are automatically saved to `output/` folder

### Answer Storage Format

Answers are saved as JSON in the `output/` folder with filename:
```
assessment_<student_id>_<timestamp>.json
```

**File contains:**
- Student information
- All questions with:
  - Serial number
  - Question text
  - Question type
  - Student's answer
  - Correct answer
- Total warnings received
- Timestamp

**Example output:**
```json
{
  "student_name": "John Doe",
  "student_id": "12345",
  "timestamp": "20241014_155430",
  "total_questions": 5,
  "answered_questions": 5,
  "warnings_count": 2,
  "answers": [
    {
      "serial_no": 1,
      "question": "What does HTML stand for?",
      "type": "mcq",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "student_answer": "A",
      "correct_answer": "A"
    }
  ]
}
```

## Warning Triggers

### Will Issue Warning:
- Multiple faces detected
- Unknown person detected (not the registered student)
- Switching to another window or application
- Mobile phone detected (if YOLO is enabled)

### Will NOT Issue Warning:
- Looking down briefly (e.g., at paper or keyboard)
- Momentarily leaving camera frame
- Normal eye movements

## Important Notes

1. **Camera Required**: Working webcam is mandatory
2. **Good Lighting**: Ensure proper lighting for face recognition
3. **Stable Internet**: Keep connection stable (for future online features)
4. **Close Other Apps**: Avoid background notifications
5. **Privacy**: Only registered student should be visible
6. **Save Often**: Use "Submit Answer" button frequently
7. **Time Management**: Timer shown at top right

## Troubleshooting

### "Could not access camera"
- Check if camera is connected
- Close other apps using camera
- Restart application

### "Student not found"
- Complete registration first
- Use exact same name and ID

### Face not recognized
- Improve lighting
- Face camera directly
- Remove obstacles (glasses, mask if possible)
- Re-register if persistent

### Window stuck in fullscreen
- Complete assessment normally
- Use "Finish Assessment" button
- Don't force close

## Configuration

Edit `config.py` to adjust:
- `MAX_WARNINGS`: Maximum warnings allowed (default: 10)
- `WARNING_COOLDOWN`: Seconds between warnings (default: 3)
- `IDENTITY_CHECK_INTERVAL`: Face check frequency (default: 0.8s)
- `ENABLE_YOLO`: Enable/disable object detection

## Technical Requirements

- Python 3.8+
- Working webcam
- Screen resolution: 1280x720 or higher
- RAM: 4GB minimum (8GB recommended)
- Processor: Intel i3 or equivalent

## Support

For issues or questions:
1. Check console logs for error messages
2. Review violation log in assessment window
3. Check `data/logs/` folder for detailed logs
4. Ensure all dependencies are installed

---

**Note**: This system is designed to promote academic integrity. Students should focus on demonstrating their knowledge honestly, and the monitoring features ensure a fair assessment environment for all.
