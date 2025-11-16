"""
Assessment Window Module
Handles fullscreen assessment interface with camera monitoring, questions, and answers
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from PIL import Image, ImageTk
import cv2
import json
import os
import time
import threading
import numpy as np
from datetime import datetime
from config import Config
from arcface_recognition import face_locations, face_encodings, compare_faces
import logging


class AssessmentWindow:
    def __init__(self, student_data, db_manager, exam_monitor):
        self.student_data = student_data
        self.db_manager = db_manager
        self.exam_monitor = exam_monitor
        self.logger = logging.getLogger(__name__)
        
        # Assessment state
        self.questions = []
        self.current_question_index = 0
        self.answers = {}
        self.is_active = False
        self.warnings_count = 0
        self.session_id = None
        self.session_start_time = None
        
        # Camera and monitoring
        self.cap = None
        self.known_face_encodings = []
        self._last_identity_check = 0.0
        self._last_object_check = 0.0
        self.last_warning_time = 0
        self.violation_log = []
        
        # Window focus monitoring
        self.window_focus = True
        self.focus_check_after_id = None
        
        # Create fullscreen window
        self.window = None
        
    def start_assessment(self, questions_file=None):
        """Start the assessment"""
        try:
            # Load questions
            if not questions_file:
                questions_file = filedialog.askopenfilename(
                    title="Select Question File",
                    initialdir=os.path.join(Config.BASE_DIR, "input"),
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
                )
            
            if not questions_file:
                messagebox.showerror("Error", "No question file selected!")
                return False
            
            # Load questions from JSON
            self.questions = self._load_questions(questions_file)
            if not self.questions:
                messagebox.showerror("Error", "No questions loaded!")
                return False
            
            # Load known face encodings
            self.known_face_encodings = self.db_manager.load_face_encodings(
                self.student_data['student_id']
            )
            if not self.known_face_encodings:
                messagebox.showerror("Error", "Could not load student's face data!")
                return False
            
            # Start exam session
            self.session_id = self.db_manager.start_exam_session(
                self.student_data['student_id']
            )
            if not self.session_id:
                messagebox.showerror("Error", "Could not start exam session!")
                return False
            
            # Initialize camera
            if not self._initialize_camera():
                messagebox.showerror("Error", "Could not access camera!")
                return False
            
            # Create fullscreen assessment window
            self._create_assessment_window()
            
            # Start monitoring
            self.is_active = True
            self.session_start_time = time.time()
            self.warnings_count = 0
            self.violation_log = []
            
            # Start monitoring threads
            self._start_monitoring()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting assessment: {str(e)}")
            messagebox.showerror("Error", f"Failed to start assessment: {str(e)}")
            return False
    
    def _show_dialog(self, dialog_func, *args, **kwargs):
        """Helper to show dialogs on top of fullscreen window"""
        if self.window:
            # Temporarily exit fullscreen and topmost for dialog
            try:
                was_fullscreen = self.window.attributes('-fullscreen')
                self.window.attributes('-fullscreen', False)
                self.window.attributes('-topmost', False)
                self.window.update()
            except:
                was_fullscreen = False
            
            # Show dialog with window as parent
            result = dialog_func(*args, parent=self.window, **kwargs)
            
            # Restore fullscreen if it was active
            if was_fullscreen:
                try:
                    self.window.attributes('-fullscreen', True)
                    self.window.attributes('-topmost', True)
                    self.window.lift()
                    self.window.focus_force()
                except:
                    pass
            
            return result
        else:
            return dialog_func(*args, **kwargs)
    
    def _load_questions(self, file_path):
        """Load questions from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            
            # Validate and normalize questions
            normalized = []
            for i, q in enumerate(questions):
                if 'question' not in q:
                    continue
                
                # Determine question type
                if 'options' in q and q.get('options'):
                    q_type = 'mcq'
                elif q.get('type') == 'programming' or 'program' in q.get('type', '').lower():
                    q_type = 'programming'
                else:
                    q_type = 'descriptive'
                
                normalized_q = {
                    'serial_no': i + 1,
                    'question': q['question'],
                    'type': q_type,
                    'options': q.get('options', []),
                    'correct_answer': q.get('correct_answer', q.get('answer', '')),
                    'explanation': q.get('explanation', '')
                }
                normalized.append(normalized_q)
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error loading questions: {str(e)}")
            return []
    
    def _initialize_camera(self):
        """Initialize camera for monitoring"""
        try:
            print(f"Initializing camera with index: {Config.CAMERA_INDEX}")
            self.cap = cv2.VideoCapture(Config.CAMERA_INDEX, cv2.CAP_DSHOW)  # DirectShow for Windows
            
            if not self.cap.isOpened():
                print("Failed to open camera, trying index 0 without DirectShow...")
                self.cap = cv2.VideoCapture(0)
            
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
                self.cap.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
                
                # Test read
                ret, test_frame = self.cap.read()
                if ret:
                    print(f"Camera initialized successfully! Frame shape: {test_frame.shape}")
                    return True
                else:
                    print("Camera opened but cannot read frames")
                    return False
            else:
                print("Could not open camera")
                return False
        except Exception as e:
            self.logger.error(f"Camera initialization error: {str(e)}")
            print(f"Camera initialization exception: {str(e)}")
            return False
    
    def _create_assessment_window(self):
        """Create fullscreen assessment window"""
        self.window = tk.Toplevel()
        self.window.title("Assessment - Active")
        
        # Make fullscreen without window controls
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-topmost', True)
        
        # Disable Alt+F4 and other close attempts
        self.window.protocol("WM_DELETE_WINDOW", self._prevent_close)
        
        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Main container
        main_container = tk.Frame(self.window, bg='#ffffff')
        main_container.pack(fill='both', expand=True)
        
        # Left side (70%) - Questions
        left_width = int(screen_width * 0.70)
        self.left_frame = tk.Frame(main_container, bg='#f5f5f5', width=left_width)
        self.left_frame.pack(side='left', fill='both', expand=True)
        self.left_frame.pack_propagate(False)
        
        # Right side (30%) - Camera and Warnings
        right_width = int(screen_width * 0.30)
        self.right_frame = tk.Frame(main_container, bg='#2c3e50', width=right_width)
        self.right_frame.pack(side='right', fill='both')
        self.right_frame.pack_propagate(False)
        
        # Setup left side (questions)
        self._setup_question_area()
        
        # Setup right side (camera and warnings)
        self._setup_monitoring_area()
        
        # Bind keyboard shortcuts (ESC disabled)
        self.window.bind('<Escape>', lambda e: 'break')
        
        # Start window focus monitoring
        self._start_focus_monitoring()
    
    def _setup_question_area(self):
        """Setup the question display area (left 70%)"""
        # Header
        header_frame = tk.Frame(self.left_frame, bg='#3498db', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Student info
        student_label = tk.Label(
            header_frame,
            text=f"Student: {self.student_data['name']} | ID: {self.student_data['student_id']}",
            font=("Arial", 14, "bold"),
            bg='#3498db',
            fg='white'
        )
        student_label.pack(side='left', padx=20, pady=15)
        
        # Timer
        self.timer_label = tk.Label(
            header_frame,
            text="Time: 00:00:00",
            font=("Arial", 14, "bold"),
            bg='#3498db',
            fg='white'
        )
        self.timer_label.pack(side='right', padx=20, pady=15)
        
        # Question number indicator with submission status
        indicator_frame = tk.Frame(self.left_frame, bg='#f5f5f5')
        indicator_frame.pack(pady=10)
        
        self.question_indicator = tk.Label(
            indicator_frame,
            text="",
            font=("Arial", 12, "bold"),
            bg='#f5f5f5',
            fg='#2c3e50'
        )
        self.question_indicator.pack(side='left')
        
        self.submission_indicator = tk.Label(
            indicator_frame,
            text="",
            font=("Arial", 14, "bold"),
            bg='#f5f5f5',
            fg='#27ae60'
        )
        self.submission_indicator.pack(side='left', padx=10)
        
        # Question display frame with scrolling
        question_container = tk.Frame(self.left_frame, bg='white')
        question_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.question_canvas = tk.Canvas(question_container, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(question_container, orient="vertical", command=self.question_canvas.yview)
        self.question_scrollable_frame = tk.Frame(self.question_canvas, bg='white')
        
        self.question_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.question_canvas.configure(scrollregion=self.question_canvas.bbox("all"))
        )
        
        self.question_canvas.create_window((0, 0), window=self.question_scrollable_frame, anchor="nw")
        self.question_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.question_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Question text
        self.question_text = tk.Label(
            self.question_scrollable_frame,
            text="",
            font=("Arial", 14),
            bg='white',
            fg='#2c3e50',
            wraplength=800,
            justify='left'
        )
        self.question_text.pack(anchor='w', padx=20, pady=20)
        
        # Answer area
        self.answer_frame = tk.Frame(self.question_scrollable_frame, bg='white')
        self.answer_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Navigation buttons
        nav_frame = tk.Frame(self.left_frame, bg='#f5f5f5', height=80)
        nav_frame.pack(fill='x', side='bottom')
        nav_frame.pack_propagate(False)
        
        button_container = tk.Frame(nav_frame, bg='#f5f5f5')
        button_container.pack(expand=True)
        
        self.prev_button = tk.Button(
            button_container,
            text="◄ Previous",
            command=self._previous_question,
            font=("Arial", 12, "bold"),
            bg='#95a5a6',
            fg='white',
            padx=20,
            pady=10
        )
        self.prev_button.pack(side='left', padx=10)
        
        self.next_button = tk.Button(
            button_container,
            text="Next ►",
            command=self._next_question,
            font=("Arial", 12, "bold"),
            bg='#3498db',
            fg='white',
            padx=20,
            pady=10
        )
        self.next_button.pack(side='left', padx=10)
        
        self.submit_button = tk.Button(
            button_container,
            text="Submit Answer",
            command=self._submit_current_answer,
            font=("Arial", 12, "bold"),
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=10
        )
        self.submit_button.pack(side='left', padx=10)
        
        self.finish_button = tk.Button(
            button_container,
            text="Finish Assessment",
            command=self._finish_assessment,
            font=("Arial", 12, "bold"),
            bg='#e74c3c',
            fg='white',
            padx=20,
            pady=10
        )
        self.finish_button.pack(side='left', padx=10)
        
        # Display first question
        self._display_question()
    
    def _setup_monitoring_area(self):
        """Setup camera and warnings area (right 30%)"""
        # Title
        monitoring_title = tk.Label(
            self.right_frame,
            text="PROCTORING",
            font=("Arial", 16, "bold"),
            bg='#2c3e50',
            fg='white'
        )
        monitoring_title.pack(pady=15)
        
        # Camera feed - larger size but not too large to hide warnings
        camera_container = tk.Frame(self.right_frame, bg='#2c3e50')
        camera_container.pack(pady=10, fill='x')
        
        tk.Label(
            camera_container,
            text="● LIVE CAMERA FEED",
            font=('Arial', 12, 'bold'),
            bg='#2c3e50',
            fg='#27ae60'
        ).pack(pady=5)
        
        # Create camera label with initial placeholder (16:9 aspect ratio)
        self.camera_label = tk.Label(
            camera_container,
            text="Initializing camera...",
            font=('Arial', 12),
            bg='black',
            fg='white',
            bd=3,
            relief='ridge'
        )
        self.camera_label.pack(padx=10, pady=5)
        
        # Warnings section
        warnings_frame = tk.LabelFrame(
            self.right_frame,
            text="Warnings",
            font=("Arial", 12, "bold"),
            bg='#34495e',
            fg='white',
            padx=10,
            pady=10
        )
        warnings_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Warning counter
        self.warning_counter = tk.Label(
            warnings_frame,
            text=f"0 / {Config.MAX_WARNINGS}",
            font=("Arial", 20, "bold"),
            bg='#34495e',
            fg='#27ae60'
        )
        self.warning_counter.pack(pady=10)
        
        # Warning status
        self.warning_status = tk.Label(
            warnings_frame,
            text="Identity: Verifying...",
            font=("Arial", 11),
            bg='#34495e',
            fg='#f39c12',
            wraplength=250
        )
        self.warning_status.pack(pady=5)
        
        # Violations log - smaller to give more space to camera
        log_label = tk.Label(
            warnings_frame,
            text="Violation Log:",
            font=("Arial", 9, "bold"),
            bg='#34495e',
            fg='white'
        )
        log_label.pack(anchor='w', padx=5, pady=(5, 2))
        
        self.violations_text = scrolledtext.ScrolledText(
            warnings_frame,
            height=6,
            font=("Courier", 8),
            bg='#2c3e50',
            fg='#ecf0f1',
            wrap='word'
        )
        self.violations_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Start camera feed (delayed to ensure window is ready)
        print("Setting up camera feed update...")
        self.window.after(100, self._update_camera_feed)
        
        # Start timer
        self._update_timer()
    
    def _display_question(self):
        """Display current question"""
        if not self.questions or self.current_question_index >= len(self.questions):
            return
        
        question = self.questions[self.current_question_index]
        
        # Update question indicator
        self.question_indicator.config(
            text=f"Question {self.current_question_index + 1} of {len(self.questions)}"
        )
        
        # Update submission status indicator
        if self.current_question_index in self.answers:
            self.submission_indicator.config(text="✓ Submitted", fg='#27ae60')
        else:
            self.submission_indicator.config(text="", fg='#e74c3c')
        
        # Update question text
        self.question_text.config(text=f"Q{question['serial_no']}: {question['question']}")
        
        # Clear previous answer widgets
        for widget in self.answer_frame.winfo_children():
            widget.destroy()
        
        # Create answer input based on question type
        if question['type'] == 'mcq':
            self._create_mcq_answer(question)
        elif question['type'] == 'programming':
            self._create_programming_answer(question)
        else:  # descriptive
            self._create_descriptive_answer(question)
        
        # Update navigation buttons
        self.prev_button.config(state='normal' if self.current_question_index > 0 else 'disabled')
        self.next_button.config(state='normal' if self.current_question_index < len(self.questions) - 1 else 'disabled')
        
        # Load existing answer if any
        self._load_existing_answer()
    
    def _create_mcq_answer(self, question):
        """Create MCQ answer widgets"""
        tk.Label(
            self.answer_frame,
            text="Select your answer:",
            font=("Arial", 12, "bold"),
            bg='white',
            fg='#2c3e50'
        ).pack(anchor='w', pady=(10, 5))
        
        self.mcq_var = tk.StringVar()
        
        options = question.get('options', [])
        option_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        
        for i, option in enumerate(options[:8]):
            option_frame = tk.Frame(self.answer_frame, bg='white')
            option_frame.pack(fill='x', pady=5)
            
            rb = tk.Radiobutton(
                option_frame,
                text=f"{option_labels[i]}. {option}",
                variable=self.mcq_var,
                value=option_labels[i],
                font=("Arial", 11),
                bg='white',
                fg='#2c3e50',
                selectcolor='#3498db',
                wraplength=700,
                justify='left'
            )
            rb.pack(anchor='w', padx=10)
    
    def _create_programming_answer(self, question):
        """Create programming answer widgets"""
        tk.Label(
            self.answer_frame,
            text="Write your code below:",
            font=("Arial", 12, "bold"),
            bg='white',
            fg='#2c3e50'
        ).pack(anchor='w', pady=(10, 5))
        
        code_frame = tk.Frame(self.answer_frame, bg='white')
        code_frame.pack(fill='both', expand=True, pady=5)
        
        self.programming_text = scrolledtext.ScrolledText(
            code_frame,
            height=20,
            width=80,
            font=("Consolas", 11),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white',
            wrap='none'
        )
        self.programming_text.pack(fill='both', expand=True)
    
    def _create_descriptive_answer(self, question):
        """Create descriptive answer widgets"""
        tk.Label(
            self.answer_frame,
            text="Write your answer below:",
            font=("Arial", 12, "bold"),
            bg='white',
            fg='#2c3e50'
        ).pack(anchor='w', pady=(10, 5))
        
        text_frame = tk.Frame(self.answer_frame, bg='white')
        text_frame.pack(fill='both', expand=True, pady=5)
        
        self.descriptive_text = scrolledtext.ScrolledText(
            text_frame,
            height=15,
            width=80,
            font=("Arial", 11),
            bg='#ffffff',
            fg='#2c3e50',
            wrap='word'
        )
        self.descriptive_text.pack(fill='both', expand=True)
    
    def _show_submission_tick(self):
        """Show tick mark when answer is submitted"""
        self.submission_indicator.config(text="✓ Submitted", fg='#27ae60')
        # Flash effect
        self.submission_indicator.config(font=("Arial", 16, "bold"))
        self.window.after(200, lambda: self.submission_indicator.config(font=("Arial", 14, "bold")))
    
    def _load_existing_answer(self):
        """Load previously saved answer for current question"""
        q_id = self.current_question_index
        if q_id in self.answers:
            answer = self.answers[q_id]
            question = self.questions[self.current_question_index]
            
            if question['type'] == 'mcq' and hasattr(self, 'mcq_var'):
                self.mcq_var.set(answer)
            elif question['type'] == 'programming' and hasattr(self, 'programming_text'):
                self.programming_text.delete('1.0', 'end')
                self.programming_text.insert('1.0', answer)
            elif question['type'] == 'descriptive' and hasattr(self, 'descriptive_text'):
                self.descriptive_text.delete('1.0', 'end')
                self.descriptive_text.insert('1.0', answer)
    
    def _submit_current_answer(self):
        """Submit/save current answer"""
        question = self.questions[self.current_question_index]
        answer = ""
        
        if question['type'] == 'mcq' and hasattr(self, 'mcq_var'):
            answer = self.mcq_var.get()
        elif question['type'] == 'programming' and hasattr(self, 'programming_text'):
            answer = self.programming_text.get('1.0', 'end-1c')
        elif question['type'] == 'descriptive' and hasattr(self, 'descriptive_text'):
            answer = self.descriptive_text.get('1.0', 'end-1c')
        
        if not answer.strip():
            self._show_dialog(messagebox.showwarning, "Warning", "Please provide an answer before submitting.")
            return
        
        # Save answer and show tick mark
        self.answers[self.current_question_index] = answer
        self._show_submission_tick()
    
    def _previous_question(self):
        """Navigate to previous question"""
        if self.current_question_index > 0:
            self.current_question_index -= 1
            self._display_question()
    
    def _next_question(self):
        """Navigate to next question"""
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self._display_question()
    
    def _finish_assessment(self):
        """Finish and submit assessment"""
        unanswered = []
        for i in range(len(self.questions)):
            if i not in self.answers or not self.answers[i].strip():
                unanswered.append(i + 1)
        
        if unanswered:
            response = self._show_dialog(
                messagebox.askyesno,
                "Unanswered Questions",
                f"You have {len(unanswered)} unanswered question(s): {', '.join(map(str, unanswered))}.\n\n"
                "Do you want to finish anyway?"
            )
            if not response:
                return
        
        response = self._show_dialog(
            messagebox.askyesno,
            "Finish Assessment",
            "Are you sure you want to finish the assessment?\n"
            "You will not be able to return to the questions."
        )
        
        if response:
            self._save_answers_to_file()
            self._end_assessment()
    
    def _save_answers_to_file(self):
        """Save answers to JSON file in output folder"""
        try:
            output_dir = os.path.join(Config.BASE_DIR, "output")
            os.makedirs(output_dir, exist_ok=True)
            
            output_data = []
            for i, question in enumerate(self.questions):
                answer_data = {
                    "serial_no": question['serial_no'],
                    "question": question['question'],
                    "type": question['type'],
                    "student_answer": self.answers.get(i, ""),
                    "correct_answer": question['correct_answer']
                }
                
                if question['type'] == 'mcq':
                    answer_data['options'] = question.get('options', [])
                
                output_data.append(answer_data)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"assessment_{self.student_data['student_id']}_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    "student_name": self.student_data['name'],
                    "student_id": self.student_data['student_id'],
                    "timestamp": timestamp,
                    "total_questions": len(self.questions),
                    "answered_questions": len(self.answers),
                    "warnings_count": self.warnings_count,
                    "answers": output_data
                }, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Answers saved to: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving answers: {str(e)}")
            self._show_dialog(messagebox.showerror, "Error", f"Failed to save answers: {str(e)}")
    
    def _prevent_close(self):
        """Prevent accidental window closing"""
        self._show_dialog(
            messagebox.showwarning,
            "Warning",
            "You cannot close this window.\nClick 'Finish Assessment' to end the exam."
        )
    
    def _start_monitoring(self):
        """Start monitoring threads"""
        threading.Thread(target=self._monitoring_loop, daemon=True).start()
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_active and self.warnings_count < Config.MAX_WARNINGS:
            try:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        frame = cv2.flip(frame, 1)
                        
                        now = time.time()
                        if now - self._last_identity_check >= Config.IDENTITY_CHECK_INTERVAL:
                            self._check_identity(frame)
                            self._last_identity_check = now
                        
                        if self.exam_monitor.net and Config.ENABLE_YOLO:
                            if now - self._last_object_check >= Config.OBJECT_CHECK_INTERVAL:
                                self._check_prohibited_objects(frame)
                                self._last_object_check = now
                
                time.sleep(Config.MONITORING_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {str(e)}")
                time.sleep(1)
        
        if self.warnings_count >= Config.MAX_WARNINGS:
            self._handle_max_warnings()
    
    def _check_identity(self, frame):
        """Check student identity"""
        try:
            detected_faces = face_locations(frame)
            detected_encodings = face_encodings(frame, detected_faces)
            
            if len(detected_faces) == 0:
                self._update_warning_status("Please look at camera", Config.WARNING_COLOR)
            elif len(detected_faces) > 1:
                self._update_warning_status(f"🚨 {len(detected_faces)} FACES DETECTED!", Config.ERROR_COLOR)
                self._add_warning("multiple_faces", f"{len(detected_faces)} faces detected - CHEATING!")
            else:
                if len(detected_encodings) > 0:
                    face_encoding = detected_encodings[0]
                    matches = compare_faces(
                        self.known_face_encodings,
                        face_encoding,
                        tolerance=Config.ARC_FACE_SIM_THRESHOLD
                    )
                    
                    match_percentage = sum(matches) / len(matches) * 100 if matches else 0
                    
                    if match_percentage >= 50:
                        self._update_warning_status("✓ Identity Verified", Config.SUCCESS_COLOR)
                    else:
                        self._update_warning_status("⚠️ UNKNOWN PERSON!", Config.ERROR_COLOR)
                        self._add_warning("identity_mismatch", "Unknown person detected")
                else:
                    self._update_warning_status("Verifying...", Config.WARNING_COLOR)
                    
        except Exception as e:
            self.logger.error(f"Identity check error: {str(e)}")
    
    def _check_prohibited_objects(self, frame):
        """Check for prohibited objects using YOLO"""
        try:
            height, width, channels = frame.shape
            
            inp = int(getattr(Config, 'YOLO_INPUT_SIZE', 320))
            blob = cv2.dnn.blobFromImage(frame, 1/255.0, (inp, inp), (0, 0, 0), swapRB=True, crop=False)
            self.exam_monitor.net.setInput(blob)
            outputs = self.exam_monitor.net.forward(self.exam_monitor.output_layers)
            
            boxes = []
            confidences = []
            class_ids = []
            
            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    
                    if confidence > Config.PHONE_DETECTION_CONFIDENCE:
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)
                        boxes.append([x, y, w, h])
                        confidences.append(float(confidence))
                        class_ids.append(int(class_id))
            
            idxs = cv2.dnn.NMSBoxes(boxes, confidences, Config.PHONE_DETECTION_CONFIDENCE, 0.4)
            if isinstance(idxs, (list, tuple)):
                nms_idx = list(idxs)
            elif hasattr(idxs, 'flatten'):
                nms_idx = idxs.flatten().tolist()
            else:
                nms_idx = []
            
            phone_hits = []
            for i in nms_idx:
                try:
                    i0 = int(i)
                    if class_ids[i0] in self.exam_monitor.phone_class_ids:
                        phone_hits.append(i0)
                except Exception:
                    continue
            
            if len(phone_hits) > 0:
                self._add_warning("prohibited_object", "Mobile phone detected")
        
        except Exception as e:
            self.logger.error(f"Object detection error: {str(e)}")
    
    def _add_warning(self, warning_type, message):
        """Add a warning to the system"""
        current_time = time.time()
        
        if current_time - self.last_warning_time < Config.WARNING_COOLDOWN:
            return
        
        self.warnings_count += 1
        self.last_warning_time = current_time
        
        if self.session_id:
            self.db_manager.add_warning(self.session_id, warning_type, message)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] WARNING {self.warnings_count}: {message}\n"
        self.violation_log.append(log_entry)
        
        self._update_warnings_display()
        self._update_violations_log()
        
        if self.warnings_count >= Config.MAX_WARNINGS:
            self._handle_max_warnings()
    
    def _update_warning_status(self, status, color):
        """Update warning status display"""
        if self.window and self.warning_status:
            self.warning_status.configure(text=f"Identity: {status}", fg=color)
    
    def _update_warnings_display(self):
        """Update warnings counter display"""
        if self.window and self.warning_counter:
            color = Config.SUCCESS_COLOR
            if self.warnings_count >= Config.MAX_WARNINGS * 0.8:
                color = Config.ERROR_COLOR
            elif self.warnings_count >= Config.MAX_WARNINGS * 0.6:
                color = Config.WARNING_COLOR
            
            self.warning_counter.configure(
                text=f"{self.warnings_count} / {Config.MAX_WARNINGS}",
                fg=color
            )
    
    def _update_violations_log(self):
        """Update violations log display"""
        if self.window and self.violations_text:
            self.violations_text.delete('1.0', 'end')
            for entry in self.violation_log:
                self.violations_text.insert('end', entry)
            self.violations_text.see('end')
    
    def _update_camera_feed(self):
        """Update camera feed display"""
        try:
            if not self.is_active:
                return
                
            if self.cap and self.cap.isOpened() and self.window:
                ret, frame = self.cap.read()
                
                if ret and frame is not None:
                    # Print first frame info for debugging
                    if not hasattr(self, '_first_frame_shown'):
                        print(f"First frame captured! Shape: {frame.shape}")
                        self._first_frame_shown = True
                    
                    # Flip frame horizontally (mirror effect)
                    frame = cv2.flip(frame, 1)
                    
                    # Update main camera feed (right panel) - 16:9 aspect ratio
                    display_width = 480  # Fixed width for 16:9 ratio
                    display_height = 270  # 16:9 aspect ratio (480/270 = 1.778)
                    # Note: Original frame is 4:3, so we'll crop or fit it to 16:9
                    
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Create PIL image and resize
                    pil_image = Image.fromarray(frame_rgb)
                    pil_image_resized = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                    
                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(pil_image_resized)
                    
                    # Update label (clear text and show image)
                    try:
                        self.camera_label.configure(image=photo, text="", bg='black')
                        self.camera_label.image = photo  # Keep reference
                    except Exception as label_error:
                        print(f"Error updating camera label: {label_error}")
                else:
                    # Show error message on camera label if frame read fails
                    if not hasattr(self, '_error_shown'):
                        print("Failed to read frame from camera")
                        self._error_shown = True
                        self.camera_label.configure(text="Camera Error: Cannot read frames", fg='red')
            else:
                if not hasattr(self, '_cap_error_shown'):
                    print(f"Camera check failed - cap: {self.cap is not None}, opened: {self.cap.isOpened() if self.cap else 'N/A'}, window: {self.window is not None}")
                    self._cap_error_shown = True
                    if self.window and self.camera_label:
                        self.camera_label.configure(text="Camera not available", fg='red')
            
            # Schedule next update
            if self.window and self.is_active:
                self.window.after(int(Config.PREVIEW_FPS_MS), self._update_camera_feed)
                
        except Exception as e:
            print(f"Camera feed update error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.logger.error(f"Camera feed error: {str(e)}")
            if self.window and self.is_active:
                self.window.after(int(Config.PREVIEW_FPS_MS), self._update_camera_feed)
    
    def _update_timer(self):
        """Update session timer"""
        if self.window and self.is_active:
            elapsed = int(time.time() - self.session_start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            
            time_str = f"Time: {hours:02d}:{minutes:02d}:{seconds:02d}"
            self.timer_label.configure(text=time_str)
            
            self.window.after(1000, self._update_timer)
    
    def _start_focus_monitoring(self):
        """Start monitoring window focus"""
        self._check_window_focus()
    
    def _check_window_focus(self):
        """Check if window has focus"""
        if self.window and self.is_active:
            try:
                current_focus = self.window.focus_displayof() is not None
                
                if not current_focus and self.window_focus:
                    # Lost focus - add warning
                    self._add_warning("window_focus_lost", "Student switched windows - CHEATING ATTEMPT!")
                    self.window_focus = False
                elif current_focus and not self.window_focus:
                    # Regained focus
                    self.window_focus = True
                
            except Exception as e:
                self.logger.error(f"Focus check error: {str(e)}")
            
            # Schedule next check
            self.focus_check_after_id = self.window.after(1000, self._check_window_focus)
    
    def _handle_max_warnings(self):
        """Handle when maximum warnings are reached"""
        self.is_active = False
        
        if self.window:
            # Exit fullscreen before showing message
            try:
                self.window.attributes('-fullscreen', False)
                self.window.attributes('-topmost', False)
            except:
                pass
            
            # No need to use _show_dialog here as we're already exiting fullscreen
            messagebox.showerror(
                "Assessment Terminated",
                f"Maximum warnings ({Config.MAX_WARNINGS}) reached.\nAssessment has been terminated.",
                parent=self.window
            )
        
        self._save_answers_to_file()
        self._end_assessment()
    
    def _end_assessment(self):
        """End the assessment session"""
        self.is_active = False
        
        if self.session_id:
            self.db_manager.end_exam_session(self.session_id, self.violation_log)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        if self.focus_check_after_id:
            try:
                self.window.after_cancel(self.focus_check_after_id)
            except:
                pass
        
        if self.window:
            # Exit fullscreen and topmost before destroying window
            try:
                self.window.attributes('-fullscreen', False)
                self.window.attributes('-topmost', False)
            except:
                pass
            
            self.window.destroy()
            self.window = None
        
        self._show_assessment_summary()
    
    def _show_assessment_summary(self):
        """Show assessment summary"""
        try:
            answered = len(self.answers)
            total = len(self.questions)
            
            summary_message = f"""
Assessment Summary:
Student: {self.student_data['name']}
ID: {self.student_data['student_id']}

Questions Answered: {answered}/{total}
Total Warnings: {self.warnings_count}/{Config.MAX_WARNINGS}
Status: {'TERMINATED' if self.warnings_count >= Config.MAX_WARNINGS else 'COMPLETED'}

Your answers have been saved to the output folder.
            """
            
            # Window is already destroyed, so don't use it as parent
            messagebox.showinfo("Assessment Summary", summary_message)
            
        except Exception as e:
            self.logger.error(f"Error showing summary: {str(e)}")
