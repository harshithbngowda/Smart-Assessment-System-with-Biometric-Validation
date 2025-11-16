"""
Database Manager for Biometric Assessment System
Handles all database operations for student data
"""

import sqlite3
import os
import json
import pickle
from datetime import datetime
import logging
from config import Config

class DatabaseManager:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.init_database()
        self.logger = logging.getLogger(__name__)
        
    def init_database(self):
        """Initialize the database with required tables"""
        Config.create_directories()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                student_id TEXT UNIQUE NOT NULL,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                face_encodings_path TEXT,
                photo_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Exam sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_end TIMESTAMP,
                warnings_count INTEGER DEFAULT 0,
                violations TEXT,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (student_id) REFERENCES students (student_id)
            )
        ''')
        
        # Warnings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                warning_type TEXT NOT NULL,
                warning_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES exam_sessions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_student(self, name, student_id, face_encodings_path, photo_count):
        """Register a new student in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO students (name, student_id, face_encodings_path, photo_count)
                VALUES (?, ?, ?, ?)
            ''', (name, student_id, face_encodings_path, photo_count))
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.IntegrityError:
            self.logger.error(f"Student ID {student_id} already exists")
            return False
        except Exception as e:
            self.logger.error(f"Error registering student: {str(e)}")
            return False
    
    def student_exists(self, name, student_id):
        """Check if a student exists in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM students 
                WHERE name = ? AND student_id = ? AND is_active = 1
            ''', (name, student_id))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            self.logger.error(f"Error checking student existence: {str(e)}")
            return False
    
    def get_student_data(self, student_id):
        """Get student data including face encodings path"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, student_id, face_encodings_path, photo_count
                FROM students 
                WHERE student_id = ? AND is_active = 1
            ''', (student_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'name': result[0],
                    'student_id': result[1],
                    'face_encodings_path': result[2],
                    'photo_count': result[3]
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting student data: {str(e)}")
            return None
    
    def start_exam_session(self, student_id):
        """Start a new exam session for a student"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO exam_sessions (student_id)
                VALUES (?)
            ''', (student_id,))
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"Error starting exam session: {str(e)}")
            return None
    
    def end_exam_session(self, session_id, violations=None):
        """End an exam session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            violations_json = json.dumps(violations) if violations else None
            
            cursor.execute('''
                UPDATE exam_sessions 
                SET session_end = CURRENT_TIMESTAMP, 
                    violations = ?,
                    status = 'completed'
                WHERE id = ?
            ''', (violations_json, session_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error ending exam session: {str(e)}")
            return False
    
    def add_warning(self, session_id, warning_type, warning_message):
        """Add a warning to the current exam session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Add warning record
            cursor.execute('''
                INSERT INTO warnings (session_id, warning_type, warning_message)
                VALUES (?, ?, ?)
            ''', (session_id, warning_type, warning_message))
            
            # Update warnings count in exam session
            cursor.execute('''
                UPDATE exam_sessions 
                SET warnings_count = warnings_count + 1
                WHERE id = ?
            ''', (session_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding warning: {str(e)}")
            return False
    
    def get_session_warnings_count(self, session_id):
        """Get the current number of warnings for a session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT warnings_count FROM exam_sessions WHERE id = ?
            ''', (session_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0
            
        except Exception as e:
            self.logger.error(f"Error getting warnings count: {str(e)}")
            return 0
    
    def get_all_students(self):
        """Get all registered students"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, student_id, registration_date, photo_count
                FROM students 
                WHERE is_active = 1
                ORDER BY registration_date DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'name': row[0],
                    'student_id': row[1],
                    'registration_date': row[2],
                    'photo_count': row[3]
                }
                for row in results
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting all students: {str(e)}")
            return []
    
    def save_face_encodings(self, student_id, face_encodings):
        """Save face encodings to file"""
        try:
            student_dir = Config.get_student_face_dir(student_id)
            os.makedirs(student_dir, exist_ok=True)
            
            encodings_path = os.path.join(student_dir, "face_encodings.pkl")
            
            with open(encodings_path, 'wb') as f:
                pickle.dump(face_encodings, f)
            
            return encodings_path
            
        except Exception as e:
            self.logger.error(f"Error saving face encodings: {str(e)}")
            return None
    
    def load_face_encodings(self, student_id):
        """Load face encodings from file"""
        try:
            student_data = self.get_student_data(student_id)
            if not student_data or not student_data['face_encodings_path']:
                return None
            
            encodings_path = student_data['face_encodings_path']
            
            if not os.path.exists(encodings_path):
                return None
            
            with open(encodings_path, 'rb') as f:
                face_encodings = pickle.load(f)
            
            return face_encodings
            
        except Exception as e:
            self.logger.error(f"Error loading face encodings: {str(e)}")
            return None
