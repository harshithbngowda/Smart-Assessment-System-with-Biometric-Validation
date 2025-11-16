"""
Helper methods for assessment window - Part 2
This file contains additional methods that will be added to assessment_window.py
"""

# PART 2 - Question Display and Navigation Methods

def _display_question(self):
    """Display current question"""
    if not self.questions or self.current_question_index >= len(self.questions):
        return
    
    question = self.questions[self.current_question_index]
    
    # Update question indicator
    self.question_indicator.config(
        text=f"Question {self.current_question_index + 1} of {len(self.questions)}"
    )
    
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
    import tkinter as tk
    
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
    import tkinter as tk
    from tkinter import scrolledtext
    
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
    import tkinter as tk
    from tkinter import scrolledtext
    
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
    from tkinter import messagebox
    
    question = self.questions[self.current_question_index]
    answer = ""
    
    if question['type'] == 'mcq' and hasattr(self, 'mcq_var'):
        answer = self.mcq_var.get()
    elif question['type'] == 'programming' and hasattr(self, 'programming_text'):
        answer = self.programming_text.get('1.0', 'end-1c')
    elif question['type'] == 'descriptive' and hasattr(self, 'descriptive_text'):
        answer = self.descriptive_text.get('1.0', 'end-1c')
    
    if not answer.strip():
        messagebox.showwarning("Warning", "Please provide an answer before submitting.")
        return
    
    self.answers[self.current_question_index] = answer
    messagebox.showinfo("Success", "Answer saved successfully!")

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
    from tkinter import messagebox
    
    unanswered = []
    for i in range(len(self.questions)):
        if i not in self.answers or not self.answers[i].strip():
            unanswered.append(i + 1)
    
    if unanswered:
        response = messagebox.askyesno(
            "Unanswered Questions",
            f"You have {len(unanswered)} unanswered question(s): {', '.join(map(str, unanswered))}.\n\n"
            "Do you want to finish anyway?"
        )
        if not response:
            return
    
    response = messagebox.askyesno(
        "Finish Assessment",
        "Are you sure you want to finish the assessment?\n"
        "You will not be able to return to the questions."
    )
    
    if response:
        self._save_answers_to_file()
        self._end_assessment()

def _save_answers_to_file(self):
    """Save answers to JSON file in output folder"""
    import os
    import json
    from datetime import datetime
    from tkinter import messagebox
    from config import Config
    
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
        messagebox.showerror("Error", f"Failed to save answers: {str(e)}")
