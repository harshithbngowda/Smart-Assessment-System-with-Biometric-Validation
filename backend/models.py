"""
Database Models for AI Assessment Platform
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import secrets
import string

db = SQLAlchemy()

def generate_code(length=8):
    """Generate unique assessment code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

class User(db.Model):
    """User model for students, teachers, and admins"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'teacher', 'admin'
    
    # Additional fields
    department = db.Column(db.String(100))
    student_id = db.Column(db.String(50))
    year = db.Column(db.String(20))
    
    # Facial recognition data
    face_encoding = db.Column(db.LargeBinary)  # Store face encoding as binary
    face_registered_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assessments = db.relationship('Assessment', backref='teacher', lazy=True, foreign_keys='Assessment.teacher_id', cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'

class Assessment(db.Model):
    """Assessment/Exam model"""
    __tablename__ = 'assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Teacher who created it
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Assessment details
    duration_minutes = db.Column(db.Integer, default=60)
    total_marks = db.Column(db.Float, default=0)
    
    # Settings
    enable_anti_cheating = db.Column(db.Boolean, default=True)
    enable_fullscreen = db.Column(db.Boolean, default=True)
    enable_webcam = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='assessment', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='assessment', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Assessment, self).__init__(**kwargs)
        if not self.code:
            self.code = generate_code()
    
    def __repr__(self):
        return f'<Assessment {self.title}>'

class Question(db.Model):
    """Question model"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    
    question_number = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # 'mcq', 'descriptive', 'programming'
    
    # Answer and options
    correct_answer = db.Column(db.Text)
    options = db.Column(db.Text)  # JSON string for MCQ options
    
    # Marks
    marks = db.Column(db.Float, default=1)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Question {self.question_number} of Assessment {self.assessment_id}>'

class Submission(db.Model):
    """Student submission model"""
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Submission details
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_marks = db.Column(db.Float, default=0)
    
    # Evaluation
    evaluated = db.Column(db.Boolean, default=False)
    evaluated_at = db.Column(db.DateTime)
    
    # Teacher feedback
    teacher_comments = db.Column(db.Text)
    
    # Anti-cheating logs
    face_verification_passed = db.Column(db.Boolean, default=True)
    cheating_attempts = db.Column(db.Integer, default=0)
    
    # Relationships
    answers = db.relationship('AnswerSubmission', backref='submission', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Submission {self.id} by Student {self.student_id}>'

class AnswerSubmission(db.Model):
    """Individual answer submission model"""
    __tablename__ = 'answer_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
    question_number = db.Column(db.Integer, nullable=False)
    student_answer = db.Column(db.Text)
    
    # Evaluation
    marks_obtained = db.Column(db.Float, default=0)
    ai_feedback = db.Column(db.Text)
    teacher_feedback = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    question = db.relationship('Question', backref='answer_submissions')
    
    def __repr__(self):
        return f'<AnswerSubmission {self.id} for Question {self.question_id}>'
