"""
Biometric Anti-Cheating and Assessment System
Main application file that coordinates all modules
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import os
from datetime import datetime

# Import custom modules
from facial_registration_v2 import FacialRegistration  # Using improved automatic version
from exam_monitor import ExamMonitor
from database_manager import DatabaseManager
from assessment_window import AssessmentWindow
from config import Config

class BiometricAssessmentSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Biometric Anti-Cheating Assessment System")
        self.root.geometry("800x750")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.facial_registration = FacialRegistration(self.db_manager)
        self.exam_monitor = ExamMonitor(self.db_manager)
        
        # Create main interface
        self.create_main_interface()
        
    def create_main_interface(self):
        """Create the main user interface"""
        # Title
        title_label = tk.Label(
            self.root, 
            text="Biometric Anti-Cheating Assessment System",
            font=("Arial", 18, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack(pady=20)
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(expand=True, fill='both', padx=50, pady=20)
        
        # Registration Section
        reg_frame = tk.LabelFrame(
            main_frame, 
            text="Student Registration", 
            font=("Arial", 14, "bold"),
            bg='#f0f0f0',
            fg='#34495e',
            padx=20,
            pady=20
        )
        reg_frame.pack(fill='x', pady=10)
        
        # Name input
        tk.Label(reg_frame, text="Student Name:", font=("Arial", 12), bg='#f0f0f0').grid(row=0, column=0, sticky='w', pady=5)
        self.name_entry = tk.Entry(reg_frame, font=("Arial", 12), width=30)
        self.name_entry.grid(row=0, column=1, pady=5, padx=10)
        
        # ID input
        tk.Label(reg_frame, text="Unique ID:", font=("Arial", 12), bg='#f0f0f0').grid(row=1, column=0, sticky='w', pady=5)
        self.id_entry = tk.Entry(reg_frame, font=("Arial", 12), width=30)
        self.id_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Register button
        register_btn = tk.Button(
            reg_frame,
            text="Register Student",
            command=self.register_student,
            font=("Arial", 12, "bold"),
            bg='#3498db',
            fg='white',
            padx=20,
            pady=10
        )
        register_btn.grid(row=2, column=0, columnspan=2, pady=15)
        
        # Assessment Section
        assessment_frame = tk.LabelFrame(
            main_frame, 
            text="Online Assessment (Proctored)", 
            font=("Arial", 14, "bold"),
            bg='#f0f0f0',
            fg='#34495e',
            padx=20,
            pady=20
        )
        assessment_frame.pack(fill='x', pady=10)
        
        # Student selection for assessment
        tk.Label(assessment_frame, text="Student Name:", font=("Arial", 12), bg='#f0f0f0').grid(row=0, column=0, sticky='w', pady=5)
        self.assessment_name_entry = tk.Entry(assessment_frame, font=("Arial", 12), width=30)
        self.assessment_name_entry.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(assessment_frame, text="Student ID:", font=("Arial", 12), bg='#f0f0f0').grid(row=1, column=0, sticky='w', pady=5)
        self.assessment_id_entry = tk.Entry(assessment_frame, font=("Arial", 12), width=30)
        self.assessment_id_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Question file path
        tk.Label(assessment_frame, text="Question File:", font=("Arial", 12), bg='#f0f0f0').grid(row=2, column=0, sticky='w', pady=5)
        
        file_frame = tk.Frame(assessment_frame, bg='#f0f0f0')
        file_frame.grid(row=2, column=1, pady=5, padx=10, sticky='ew')
        
        self.question_file_entry = tk.Entry(file_frame, font=("Arial", 10), width=25)
        self.question_file_entry.pack(side='left', fill='x', expand=True)
        self.question_file_entry.insert(0, "input/sample_mixed_assessment.json")
        
        browse_btn = tk.Button(
            file_frame,
            text="Browse...",
            command=self.browse_question_file,
            font=("Arial", 10),
            bg='#3498db',
            fg='white',
            padx=10,
            pady=5
        )
        browse_btn.pack(side='left', padx=(5, 0))
        
        # Help text for drag and drop
        help_label = tk.Label(
            assessment_frame,
            text="Tip: Paste file path or click Browse to select",
            font=("Arial", 9, "italic"),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        help_label.grid(row=3, column=1, sticky='w', padx=10)
        
        # Start assessment button
        start_assessment_btn = tk.Button(
            assessment_frame,
            text="Start Assessment",
            command=self.start_assessment,
            font=("Arial", 12, "bold"),
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=10
        )
        start_assessment_btn.grid(row=4, column=0, columnspan=2, pady=15)
        
        # Exam Monitoring Section (Legacy)
        exam_frame = tk.LabelFrame(
            main_frame, 
            text="Exam Monitoring (Video Only)", 
            font=("Arial", 14, "bold"),
            bg='#f0f0f0',
            fg='#34495e',
            padx=20,
            pady=20
        )
        exam_frame.pack(fill='x', pady=10)
        
        # Student selection for exam
        tk.Label(exam_frame, text="Student Name:", font=("Arial", 12), bg='#f0f0f0').grid(row=0, column=0, sticky='w', pady=5)
        self.exam_name_entry = tk.Entry(exam_frame, font=("Arial", 12), width=30)
        self.exam_name_entry.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(exam_frame, text="Student ID:", font=("Arial", 12), bg='#f0f0f0').grid(row=1, column=0, sticky='w', pady=5)
        self.exam_id_entry = tk.Entry(exam_frame, font=("Arial", 12), width=30)
        self.exam_id_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Start exam button
        start_exam_btn = tk.Button(
            exam_frame,
            text="Start Exam Monitoring",
            command=self.start_exam_monitoring,
            font=("Arial", 12, "bold"),
            bg='#e74c3c',
            fg='white',
            padx=20,
            pady=10
        )
        start_exam_btn.grid(row=2, column=0, columnspan=2, pady=15)
        
        # Status display
        self.status_label = tk.Label(
            main_frame,
            text="System Ready",
            font=("Arial", 12),
            bg='#f0f0f0',
            fg='#27ae60'
        )
        self.status_label.pack(pady=20)
        
    def register_student(self):
        """Handle student registration"""
        name = self.name_entry.get().strip()
        student_id = self.id_entry.get().strip()
        
        if not name or not student_id:
            messagebox.showerror("Error", "Please enter both name and ID")
            return
            
        self.status_label.config(text="Starting registration process...", fg='#f39c12')
        self.root.update()
        
        try:
            success = self.facial_registration.register_student(name, student_id)
            if success:
                messagebox.showinfo("Success", f"Student {name} registered successfully!")
                self.name_entry.delete(0, tk.END)
                self.id_entry.delete(0, tk.END)
                self.status_label.config(text="Registration completed successfully", fg='#27ae60')
            else:
                messagebox.showerror("Error", "Registration failed. Please try again.")
                self.status_label.config(text="Registration failed", fg='#e74c3c')
        except Exception as e:
            messagebox.showerror("Error", f"Registration error: {str(e)}")
            self.status_label.config(text="Registration error", fg='#e74c3c')
    
    def browse_question_file(self):
        """Open file browser to select question file"""
        initial_dir = os.path.join(Config.BASE_DIR, "input")
        
        file_path = filedialog.askopenfilename(
            title="Select Question File",
            initialdir=initial_dir if os.path.exists(initial_dir) else os.getcwd(),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            # Update the entry field with selected path
            self.question_file_entry.delete(0, tk.END)
            self.question_file_entry.insert(0, file_path)
    
    def start_assessment(self):
        """Start fullscreen proctored assessment for a student"""
        name = self.assessment_name_entry.get().strip()
        student_id = self.assessment_id_entry.get().strip()
        question_file = self.question_file_entry.get().strip()
        
        if not name or not student_id:
            messagebox.showerror("Error", "Please enter both name and ID")
            return
        
        if not question_file:
            messagebox.showerror("Error", "Please specify a question file path")
            return
        
        # Check if file exists
        if not os.path.isabs(question_file):
            # If relative path, make it absolute from base directory
            question_file = os.path.join(Config.BASE_DIR, question_file)
        
        if not os.path.exists(question_file):
            messagebox.showerror("Error", f"Question file not found:\n{question_file}")
            return
            
        # Check if student is registered
        if not self.db_manager.student_exists(name, student_id):
            messagebox.showerror("Error", "Student not found. Please register first.")
            return
        
        # Get student data
        student_data = self.db_manager.get_student_data(student_id)
        if not student_data:
            messagebox.showerror("Error", "Could not retrieve student data!")
            return
            
        self.status_label.config(text="Starting assessment...", fg='#f39c12')
        self.root.update()
        
        try:
            # Create and start assessment window
            assessment_window = AssessmentWindow(
                student_data=student_data,
                db_manager=self.db_manager,
                exam_monitor=self.exam_monitor
            )
            
            # Pass the question file path
            success = assessment_window.start_assessment(questions_file=question_file)
            
            if success:
                self.status_label.config(text="Assessment active", fg='#27ae60')
            else:
                self.status_label.config(text="Assessment start failed", fg='#e74c3c')
                
        except Exception as e:
            messagebox.showerror("Error", f"Assessment error: {str(e)}")
            self.status_label.config(text="Assessment error", fg='#e74c3c')
    
    def start_exam_monitoring(self):
        """Start exam monitoring for a student (legacy - video only)"""
        name = self.exam_name_entry.get().strip()
        student_id = self.exam_id_entry.get().strip()
        
        if not name or not student_id:
            messagebox.showerror("Error", "Please enter both name and ID")
            return
            
        # Check if student is registered
        if not self.db_manager.student_exists(name, student_id):
            messagebox.showerror("Error", "Student not found. Please register first.")
            return
            
        self.status_label.config(text="Starting exam monitoring...", fg='#f39c12')
        self.root.update()
        
        try:
            # Start monitoring in a new window
            self.exam_monitor.start_monitoring(name, student_id)
            self.status_label.config(text="Exam monitoring active", fg='#27ae60')
        except Exception as e:
            messagebox.showerror("Error", f"Monitoring error: {str(e)}")
            self.status_label.config(text="Monitoring error", fg='#e74c3c')
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data/faces", exist_ok=True)
    os.makedirs("data/logs", exist_ok=True)
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    # Start application
    app = BiometricAssessmentSystem()
    app.run()
