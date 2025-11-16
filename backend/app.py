"""
Main Flask Application for AI Assessment Platform
Integrates all features: Q&A Generation, Facial Recognition, Evaluation
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import json
import base64
import cv2
import numpy as np

from models import db, User, Assessment, Question, Submission, AnswerSubmission
from qa_generator import generate_questions_from_file, generate_questions_from_text
from evaluator import evaluate_submission
# Try to import advanced face recognition, fallback to simple version
try:
    from face_processor_advanced import verify_face, save_face_encoding, monitor_cheating_attempts
    print("Using advanced face recognition with multi-photo capture and augmentation")
except ImportError:
    print("Advanced face recognition not available, using simple version")
    from face_processor_simple import verify_face, save_face_encoding
    def monitor_cheating_attempts(image, user):
        return {
            'face_verified': False,
            'face_confidence': 0.0,
            'multiple_faces': False,
            'face_count': 0,
            'phone_detected': False,
            'phone_count': 0,
            'overall_status': 'safe'
        }

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

# Use absolute path for database to avoid issues with different working directories
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "assessment_platform.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
print(f"[DB] Database path: {db_path}")
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# API Keys (hardcoded as requested)
app.config['GEMINI_API_KEY'] = 'AIzaSyDpB0FK_XtWKJZdfNq4bnaErhvROmpMLms'
app.config['HANDWRITING_API_KEY'] = 'AIzaSyDJbnjXOLDPm8iIgxYEU8_2MUMGBQnwFfU'

# Set environment variables for handwriting converter and evaluation only
os.environ['GEMINI_API_KEY'] = app.config['GEMINI_API_KEY']
os.environ['HANDWRITING_API_KEY'] = app.config['HANDWRITING_API_KEY']
# os.environ['USE_GEMINI_QG'] = '1'  # DISABLED - Use Pakka for question generation

# Initialize extensions
CORS(app, resources={r"/*": {"origins": "*"}})
jwt = JWTManager(app)
db.init_app(app)

# Create upload folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'faces'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'handwriting'), exist_ok=True)

# ==================== Health Check ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Server is running'}), 200

# ==================== Authentication Routes ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user (student/teacher)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'name', 'role']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Validate role
        if data['role'] not in ['student', 'teacher']:
            return jsonify({'error': 'Invalid role'}), 400
        
        # Create new user
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            email=data['email'],
            password=hashed_password,
            name=data['name'],
            role=data['role'],
            department=data.get('department', ''),
            student_id=data.get('student_id', ''),
            year=data.get('year', '')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create access token: identity must be a string in JWT v4
        access_token = create_access_token(
            identity=str(new_user.id),
            additional_claims={'email': new_user.email, 'role': new_user.role}
        )
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'name': new_user.name,
                'role': new_user.role,
                'department': new_user.department,
                'year': new_user.year,
                'student_id': new_user.student_id,
                'has_face_data': new_user.face_encoding is not None
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create access token: identity as string, role/email as additional claims
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'email': user.email, 'role': user.role}
        )
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'role': user.role,
                'department': user.department,
                'year': user.year,
                'has_face_data': user.face_encoding is not None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/admin/login', methods=['POST'])
def admin_login():
    """Admin login with predefined credentials"""
    try:
        data = request.get_json()
        
        # Hardcoded admin credentials (change in production)
        if data.get('username') == 'admin' and data.get('password') == 'admin123':
            access_token = create_access_token(
                identity=str(0),
                additional_claims={'email': 'admin@system.com', 'role': 'admin'}
            )
            
            return jsonify({
                'access_token': access_token,
                'user': {
                    'id': 0,
                    'email': 'admin@system.com',
                    'name': 'Administrator',
                    'role': 'admin'
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid admin credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Face Registration Routes ====================

@app.route('/api/face/register', methods=['POST'])
@jwt_required()
def register_face():
    """Register student's facial features"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        if claims.get('role') != 'student':
            return jsonify({'error': 'Only students can register faces'}), 403
        
        data = request.get_json()
        print(f"[DEBUG] Received face registration request. Data keys: {list(data.keys()) if data else 'None'}")
        
        # Accept either a single image string under 'image' or a list under 'images'
        images_payload = None
        if data and data.get('images') and isinstance(data.get('images'), list) and len(data['images']) > 0:
            print(f"[DEBUG] Found {len(data['images'])} images in payload")
            images_payload = data['images']
        elif data and data.get('image'):
            print(f"[DEBUG] Found single image in payload")
            images_payload = data['image']
        else:
            print(f"[DEBUG] No valid images found. data={data}")
            return jsonify({'error': 'Image data required'}), 400
        
        # Save face encoding (advanced function handles single string, ndarray, or list)
        user = User.query.get(user_id)
        success, message = save_face_encoding(user, images_payload)
        
        if success:
            db.session.commit()
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/face/verify', methods=['POST'])
@jwt_required()
def verify_face_api():
    """Verify student's face before exam"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        print(f"[VERIFY API] User {user_id} requesting face verification")
        
        if claims.get('role') != 'student':
            return jsonify({'error': 'Only students can verify faces'}), 403
        
        data = request.get_json()
        
        if not data.get('image'):
            print("[VERIFY API] No image data in request")
            return jsonify({'error': 'Image data required'}), 400
        
        # Decode base64 image
        image_base64 = data['image']
        
        if not image_base64 or len(image_base64) < 100:
            print(f"[VERIFY API] Image data too short: {len(image_base64) if image_base64 else 0} bytes")
            return jsonify({'error': 'Invalid or empty image data'}), 400
        
        # Remove data URL prefix if present
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        print(f"[VERIFY API] Base64 length: {len(image_base64)} bytes")
        
        try:
            image_bytes = base64.b64decode(image_base64)
            print(f"[VERIFY API] Decoded to {len(image_bytes)} bytes")
        except Exception as e:
            print(f"[VERIFY API] Base64 decode error: {e}")
            return jsonify({'error': 'Failed to decode base64 image'}), 400
        
        if len(image_bytes) == 0:
            print("[VERIFY API] Decoded bytes are empty")
            return jsonify({'error': 'Decoded image is empty'}), 400
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            print(f"[VERIFY API] cv2.imdecode failed, buffer size: {len(image_bytes)}")
            return jsonify({'error': 'Invalid image format'}), 400
        
        print(f"[VERIFY API] Image decoded, shape: {image.shape}")
        
        # Verify face
        user = User.query.get(user_id)
        if not user:
            print(f"[VERIFY API] User {user_id} not found")
            return jsonify({'error': 'User not found'}), 404
        
        if not user.face_encoding:
            print(f"[VERIFY API] User {user_id} has no registered face")
            return jsonify({'error': 'No face registered. Please register your face first.'}), 400
        
        print(f"[VERIFY API] Calling verify_face for user {user.email}")
        success, confidence = verify_face(user, image)
        
        print(f"[VERIFY API] Verification result: {success}, confidence: {confidence}")
        
        # Convert numpy types to native Python types for JSON serialization
        return jsonify({
            'verified': bool(success),
            'confidence': float(confidence * 100)  # Convert to percentage
        }), 200
        
    except Exception as e:
        print(f"[VERIFY API] ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== Assessment Routes (Teacher) ====================

@app.route('/api/assessments', methods=['POST'])
@jwt_required()
def create_assessment():
    """Create new assessment (teacher only)"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        if claims.get('role') != 'teacher':
            return jsonify({'error': 'Only teachers can create assessments'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Assessment title required'}), 400
        
        # Create assessment
        assessment = Assessment(
            title=data['title'],
            description=data.get('description', ''),
            teacher_id=user_id,
            duration_minutes=data.get('duration_minutes', 60),
            total_marks=0  # Will be calculated from questions
        )
        
        db.session.add(assessment)
        db.session.flush()  # Get assessment ID
        
        # Add questions
        questions_data = data.get('questions', [])
        total_marks = 0
        
        for idx, q_data in enumerate(questions_data):
            question = Question(
                assessment_id=assessment.id,
                question_number=idx + 1,
                question_text=q_data['question_text'],
                question_type=q_data['question_type'],
                correct_answer=q_data.get('correct_answer', ''),
                marks=q_data.get('marks', 1 if q_data['question_type'] == 'mcq' else 10),
                options=json.dumps(q_data.get('options', [])) if q_data.get('options') else None
            )
            total_marks += question.marks
            db.session.add(question)
        
        assessment.total_marks = total_marks
        db.session.commit()
        
        return jsonify({
            'message': 'Assessment created successfully',
            'assessment': {
                'id': assessment.id,
                'code': assessment.code,
                'title': assessment.title
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/assessments/generate', methods=['POST'])
@jwt_required()
def generate_assessment_questions():
    """Generate questions from uploaded file or text"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        if claims.get('role') != 'teacher':
            return jsonify({'error': 'Only teachers can generate questions'}), 403
        
        # Check if file upload or text
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Save file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'documents', filename)
            file.save(filepath)
            
            print(f"✅ File saved: {filepath}")
            
            # Generate questions from file
            num_questions = int(request.form.get('num_questions', 10))
            mode = request.form.get('mode', 'auto')
            print(f"Generating {num_questions} questions from file (mode: {mode})...")
            questions = generate_questions_from_file(filepath, num_questions, mode)
            print(f"✅ Generated {len(questions)} questions")
            
        elif request.get_json() and request.get_json().get('text'):
            data = request.get_json()
            text = data['text']
            num_questions = data.get('num_questions', 10)
            mode = data.get('mode', 'auto')
            
            print(f"Generating {num_questions} questions from text (mode: {mode})...")
            # Generate questions from text
            questions = generate_questions_from_text(text, num_questions, mode)
            print(f"✅ Generated {len(questions)} questions")
            
        else:
            return jsonify({'error': 'No file or text provided'}), 400
        
        return jsonify({
            'questions': questions
        }), 200
        
    except Exception as e:
        print(f"❌ Error generating questions: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/assessments/teacher', methods=['GET'])
@jwt_required()
def get_teacher_assessments():
    """Get all assessments created by teacher"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        if claims.get('role') != 'teacher':
            return jsonify({'error': 'Only teachers can access this'}), 403
        
        assessments = Assessment.query.filter_by(teacher_id=user_id).all()
        
        return jsonify({
            'assessments': [{
                'id': a.id,
                'code': a.code,
                'title': a.title,
                'description': a.description,
                'duration_minutes': a.duration_minutes,
                'total_marks': a.total_marks,
                'created_at': a.created_at.isoformat(),
                'submissions_count': len(a.submissions)
            } for a in assessments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assessments/<int:assessment_id>', methods=['GET'])
@jwt_required()
def get_assessment_details(assessment_id):
    """Get assessment details with questions"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        role = claims.get('role')
        
        assessment = Assessment.query.get_or_404(assessment_id)
        
        # Check permissions
        if role == 'teacher' and assessment.teacher_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        questions = Question.query.filter_by(assessment_id=assessment_id).order_by(Question.question_number).all()
        
        return jsonify({
            'id': assessment.id,
            'code': assessment.code,
            'title': assessment.title,
            'description': assessment.description,
            'duration_minutes': assessment.duration_minutes,
            'total_marks': assessment.total_marks,
            'created_at': assessment.created_at.isoformat(),
            'questions': [{
                'id': q.id,
                'question_number': q.question_number,
                'question_text': q.question_text,
                'question_type': q.question_type,
                'marks': q.marks,
                'options': json.loads(q.options) if q.options else None,
                'correct_answer': q.correct_answer if role in ['teacher', 'admin'] else None
            } for q in questions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assessments/<int:assessment_id>/submissions', methods=['GET'])
@jwt_required()
def get_assessment_submissions(assessment_id):
    """Get all submissions for an assessment (teacher only)"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        if claims.get('role') != 'teacher':
            return jsonify({'error': 'Only teachers can view submissions'}), 403
        
        assessment = Assessment.query.get_or_404(assessment_id)
        
        if assessment.teacher_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        submissions = Submission.query.filter_by(assessment_id=assessment_id).all()
        
        return jsonify({
            'submissions': [{
                'id': s.id,
                'student': {
                    'id': s.student.id,
                    'name': s.student.name,
                    'email': s.student.email
                },
                'submitted_at': s.submitted_at.isoformat(),
                'total_marks': s.total_marks,
                'max_marks': assessment.total_marks,
                'percentage': (s.total_marks / assessment.total_marks * 100) if assessment.total_marks > 0 else 0,
                'evaluated': s.evaluated,
                'teacher_comments': s.teacher_comments
            } for s in submissions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/submissions/<int:submission_id>', methods=['GET'])
@jwt_required()
def get_submission_details(submission_id):
    """Get detailed submission with answers"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        role = claims.get('role')
        
        submission = Submission.query.get_or_404(submission_id)
        
        # Check permissions
        if role == 'student' and submission.student_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if role == 'teacher' and submission.assessment.teacher_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        answers = AnswerSubmission.query.filter_by(submission_id=submission_id).order_by(AnswerSubmission.question_number).all()
        
        return jsonify({
            'id': submission.id,
            'assessment': {
                'id': submission.assessment.id,
                'title': submission.assessment.title
            },
            'student': {
                'id': submission.student.id,
                'name': submission.student.name,
                'email': submission.student.email
            },
            'submitted_at': submission.submitted_at.isoformat(),
            'total_marks': submission.total_marks,
            'max_marks': submission.assessment.total_marks,
            'evaluated': submission.evaluated,
            'teacher_comments': submission.teacher_comments,
            'answers': [{
                'id': a.id,  # Add the actual database ID
                'question_number': a.question_number,
                'question_text': a.question.question_text,
                'question_type': a.question.question_type,
                'student_answer': a.student_answer,
                'correct_answer': a.question.correct_answer,
                'marks_obtained': a.marks_obtained,
                'max_marks': a.question.marks,
                'ai_feedback': a.ai_feedback,
                'teacher_feedback': a.teacher_feedback
            } for a in answers]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/submissions/<int:submission_id>/update', methods=['PUT'])
@jwt_required()
def update_submission_marks(submission_id):
    """Update marks and add teacher comments"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        if claims.get('role') != 'teacher':
            return jsonify({'error': 'Only teachers can update marks'}), 403
        
        submission = Submission.query.get_or_404(submission_id)
        
        if submission.assessment.teacher_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Update teacher comments
        if 'teacher_comments' in data:
            submission.teacher_comments = data['teacher_comments']
        
        # Update individual answer marks and feedback
        if 'answers' in data:
            total_marks = 0
            for answer_data in data['answers']:
                answer = AnswerSubmission.query.get(answer_data['id'])
                if answer and answer.submission_id == submission_id:
                    if 'marks_obtained' in answer_data:
                        answer.marks_obtained = answer_data['marks_obtained']
                    if 'teacher_feedback' in answer_data:
                        answer.teacher_feedback = answer_data['teacher_feedback']
                    total_marks += answer.marks_obtained
            
            submission.total_marks = total_marks
        
        db.session.commit()
        
        return jsonify({'message': 'Submission updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/submissions/<int:submission_id>', methods=['DELETE'])
@jwt_required()
def delete_submission(submission_id):
    """Delete a submission (for retaking assessment)"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        role = claims.get('role')
        
        submission = Submission.query.get_or_404(submission_id)
        
        # Only the student who submitted or teacher can delete
        if role == 'student' and submission.student_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if role == 'teacher' and submission.assessment.teacher_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Delete all related answer submissions first
        AnswerSubmission.query.filter_by(submission_id=submission_id).delete()
        
        # Delete the submission
        db.session.delete(submission)
        db.session.commit()
        
        print(f"[DELETE] Submission {submission_id} deleted by user {user_id}")
        
        return jsonify({'message': 'Submission deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== Student Routes ====================

@app.route('/api/assessments/access/<string:code>', methods=['GET'])
@jwt_required()
def access_assessment_by_code(code):
    """Access assessment using unique code"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        # Normalize: trim spaces and uppercase so pasted codes work reliably
        code = code.strip().upper()
        
        if claims.get('role') != 'student':
            return jsonify({'error': 'Only students can access assessments'}), 403
        
        assessment = Assessment.query.filter_by(code=code).first()
        if not assessment:
            return jsonify({'error': 'Invalid assessment code'}), 404
        
        # Check if student has already submitted
        existing_submission = Submission.query.filter_by(
            assessment_id=assessment.id,
            student_id=user_id
        ).first()
        
        if existing_submission:
            return jsonify({'error': 'You have already submitted this assessment'}), 400
        
        questions = Question.query.filter_by(assessment_id=assessment.id).order_by(Question.question_number).all()
        
        return jsonify({
            'id': assessment.id,
            'title': assessment.title,
            'description': assessment.description,
            'duration_minutes': assessment.duration_minutes,
            'total_marks': assessment.total_marks,
            'questions': [{
                'id': q.id,
                'question_number': q.question_number,
                'question_text': q.question_text,
                'question_type': q.question_type,
                'marks': q.marks,
                'options': json.loads(q.options) if q.options else None
            } for q in questions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/submissions', methods=['POST'])
@jwt_required()
def submit_assessment():
    """Submit assessment answers"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        print(f"[SUBMIT] User {user_id} attempting to submit assessment")
        
        if claims.get('role') != 'student':
            return jsonify({'error': 'Only students can submit assessments'}), 403
        
        data = request.get_json()
        print(f"[SUBMIT] Data received: assessment_id={data.get('assessment_id')}, answers count={len(data.get('answers', []))}")
        
        # Validate required fields
        if not data.get('assessment_id') or not data.get('answers'):
            return jsonify({'error': 'Assessment ID and answers required'}), 400
        
        # Check if already submitted
        existing_submission = Submission.query.filter_by(
            assessment_id=data['assessment_id'],
            student_id=user_id
        ).first()
        
        if existing_submission:
            print(f"[SUBMIT] Duplicate submission detected for assessment {data['assessment_id']}")
            return jsonify({'error': 'Assessment already submitted'}), 400
        
        print(f"[SUBMIT] No existing submission found, creating new one")
        
        # Create submission
        submission = Submission(
            assessment_id=data['assessment_id'],
            student_id=user_id
        )
        
        db.session.add(submission)
        db.session.flush()
        print(f"[SUBMIT] Submission created with ID: {submission.id}")
        
        # Save answers
        for answer_data in data['answers']:
            answer = AnswerSubmission(
                submission_id=submission.id,
                question_id=answer_data['question_id'],
                question_number=answer_data['question_number'],
                student_answer=answer_data['student_answer']
            )
            db.session.add(answer)
        
        print(f"[SUBMIT] Added {len(data['answers'])} answers, committing to database...")
        db.session.commit()
        print(f"[SUBMIT] Database commit successful for submission {submission.id}")
        
        # Verify the submission was actually saved
        db.session.expire_all()
        verify_sub = db.session.get(Submission, submission.id)
        if verify_sub:
            print(f"[SUBMIT] Verified: Submission {submission.id} exists in database")
        else:
            print(f"[SUBMIT] WARNING: Submission {submission.id} NOT found after commit!")
        
        # Store submission_id before starting async evaluation
        submission_id = submission.id
        
        # Evaluate submission asynchronously (with slight delay to ensure DB commit completes)
        import time
        time.sleep(0.1)  # Small delay to ensure transaction is committed
        print(f"[SUBMIT] Starting async evaluation for submission {submission_id}")
        # Pass the current app instance to avoid creating a new one
        from flask import current_app
        evaluate_submission(submission_id, current_app._get_current_object(), app.config['GEMINI_API_KEY'])
        
        print(f"[SUBMIT] ✅ Submission {submission_id} created successfully, evaluation started")
        return jsonify({
            'message': 'Assessment submitted successfully',
            'submission_id': submission.id
        }), 201
        
    except Exception as e:
        print(f"[SUBMIT] ❌ Error during submission: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/submissions/student', methods=['GET'])
@jwt_required()
def get_student_submissions():
    """Get all submissions by current student"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        if claims.get('role') != 'student':
            return jsonify({'error': 'Only students can access this'}), 403
        
        submissions = Submission.query.filter_by(student_id=user_id).all()
        
        return jsonify({
            'submissions': [{
                'id': s.id,
                'assessment': {
                    'id': s.assessment.id,
                    'title': s.assessment.title,
                    'code': s.assessment.code
                },
                'submitted_at': s.submitted_at.isoformat(),
                'total_marks': s.total_marks,
                'max_marks': s.assessment.total_marks,
                'percentage': (s.total_marks / s.assessment.total_marks * 100) if s.assessment.total_marks > 0 else 0,
                'evaluated': s.evaluated,
                'teacher_comments': s.teacher_comments
            } for s in submissions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Admin Routes ====================

@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def get_admin_stats():
    """Get system statistics (admin only)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access only'}), 403
        
        total_students = User.query.filter_by(role='student').count()
        total_teachers = User.query.filter_by(role='teacher').count()
        total_assessments = Assessment.query.count()
        total_submissions = Submission.query.count()
        
        # Calculate verification rate
        students_with_faces = User.query.filter_by(role='student').filter(User.face_encoding.isnot(None)).count()
        verification_rate = (students_with_faces / total_students * 100) if total_students > 0 else 0
        
        return jsonify({
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_assessments': total_assessments,
            'total_submissions': total_submissions,
            'verification_rate': round(verification_rate, 1)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Get all users (admin only)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access only'}), 403
        
        users = User.query.all()
        
        return jsonify({
            'users': [{
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'role': u.role,
                'department': u.department,
                'created_at': u.created_at.isoformat(),
                'has_face_data': u.face_encoding is not None
            } for u in users]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users', methods=['POST'])
@jwt_required()
def admin_create_user():
    """Create a user (admin only)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access only'}), 403

        data = request.get_json() or {}
        required = ['email', 'password', 'name', 'role']
        if not all(k in data and data[k] for k in required):
            return jsonify({'error': 'email, password, name, role are required'}), 400

        if data['role'] not in ['student', 'teacher', 'admin']:
            return jsonify({'error': 'Invalid role'}), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400

        hashed = generate_password_hash(data['password'])
        user = User(
            email=data['email'],
            password=hashed,
            name=data['name'],
            role=data['role'],
            department=data.get('department', ''),
            student_id=data.get('student_id', ''),
            year=data.get('year', '')
        )
        db.session.add(user)
        db.session.commit()

        return jsonify({'message': 'User created', 'id': user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def admin_update_user(user_id):
    """Update a user (admin only)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access only'}), 403

        user = User.query.get_or_404(user_id)
        data = request.get_json() or {}

        # Unique email check
        if 'email' in data and data['email'] and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already exists'}), 400
            user.email = data['email']

        if 'name' in data and data['name']:
            user.name = data['name']
        if 'role' in data and data['role'] in ['student', 'teacher', 'admin']:
            user.role = data['role']
        if 'department' in data:
            user.department = data['department'] or ''
        if 'student_id' in data:
            user.student_id = data['student_id'] or ''
        if 'year' in data:
            user.year = data['year'] or ''
        if 'password' in data and data['password']:
            user.password = generate_password_hash(data['password'])

        db.session.commit()
        return jsonify({'message': 'User updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_user(user_id):
    """Delete a user (admin only)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access only'}), 403

        user = User.query.get_or_404(user_id)
        # Prevent deleting built-in admin identity 0 (JWT-only)
        if user.id == 0:
            return jsonify({'error': 'Cannot delete built-in admin'}), 400

        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/clear-face', methods=['POST'])
@jwt_required()
def admin_clear_face(user_id):
    """Clear stored face data for a user (admin only)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access only'}), 403

        user = User.query.get_or_404(user_id)
        user.face_encoding = None
        user.face_registered_at = None
        db.session.commit()
        return jsonify({'message': 'Face data cleared'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/register-face', methods=['POST'])
@jwt_required()
def admin_register_face(user_id):
    """Register or re-register face data for any user (admin only)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access only'}), 403

        user = User.query.get_or_404(user_id)
        data = request.get_json()
        print(f"[ADMIN FACE] Registering face for user {user_id} ({user.email})")

        # Accept either a single image string under 'image' or a list under 'images'
        images_payload = None
        if data and data.get('images') and isinstance(data.get('images'), list) and len(data['images']) > 0:
            print(f"[ADMIN FACE] Found {len(data['images'])} images in payload")
            images_payload = data['images']
        elif data and data.get('image'):
            print(f"[ADMIN FACE] Found single image in payload")
            images_payload = data['image']
        else:
            print(f"[ADMIN FACE] No valid images found")
            return jsonify({'error': 'Image data required'}), 400

        # Save face encoding
        success, message = save_face_encoding(user, images_payload)

        if success:
            db.session.commit()
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/assessments', methods=['GET'])
@jwt_required()
def get_all_assessments():
    """Get all assessments (admin only)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access only'}), 403
        
        assessments = Assessment.query.all()
        
        return jsonify({
            'assessments': [{
                'id': a.id,
                'code': a.code,
                'title': a.title,
                'teacher': {
                    'id': a.teacher.id,
                    'name': a.teacher.name
                },
                'created_at': a.created_at.isoformat(),
                'submissions_count': len(a.submissions)
            } for a in assessments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Handwriting to Text ====================

@app.route('/api/handwriting/convert', methods=['POST'])
@jwt_required()
def convert_handwriting():
    """Convert handwriting image to text using Google Vision API"""
    filepath = None
    try:
        print("="*70)
        print("📝 Handwriting conversion request received")
        print("="*70)
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        print(f"📄 File: {file.filename}")
        print(f"📄 Type: {file.content_type}")
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'handwriting', filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        file.save(filepath)
        print(f"💾 Saved to: {filepath}")
        print(f"💾 File size: {os.path.getsize(filepath)} bytes")
        
        # Convert handwriting to text
        from handwriting_converter import convert_image_to_text
        print(f"🔄 Starting conversion...")
        text = convert_image_to_text(filepath, app.config['HANDWRITING_API_KEY'])
        print(f"✅ Conversion complete")
        
        # Check if conversion failed (error message returned)
        if not text or text.startswith("Error") or text.startswith("PDF processing not available"):
            print(f"❌ Handwriting conversion failed: {text}")
            return jsonify({'error': 'Could not extract text from file. Please ensure the file is a clear image or PDF with readable handwriting.'}), 400
        
        if len(text.strip()) < 10:
            print(f"⚠️ Warning: Extracted text is very short ({len(text)} chars)")
            return jsonify({'error': 'Could not extract meaningful text from image. Please ensure the image is clear and contains readable text.'}), 400
        
        print(f"✅ Extracted {len(text)} characters from handwriting")
        print(f"📝 Text preview: {text[:100]}...")
        
        return jsonify({'text': text}), 200
        
    except Exception as e:
        print(f"❌ Error in handwriting conversion: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Handwriting conversion failed: {str(e)}'}), 500

# ==================== Cheating Monitoring ====================

@app.route('/api/monitor-cheating', methods=['POST'])
@jwt_required()
def monitor_cheating():
    """Monitor for cheating attempts during assessment"""
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Get current user
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Decode base64 image
        image_data_clean = image_data.split(',')[1] if ',' in image_data else image_data
        image_bytes = base64.b64decode(image_data_clean)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'error': 'Failed to decode image'}), 400
        
        print(f"[MONITOR] Monitoring cheating for user {user.email}, image shape: {image.shape}")
        
        # Monitor cheating attempts
        results = monitor_cheating_attempts(image, user)
        
        print(f"[MONITOR] Results: {results}")
        
        return jsonify(results), 200
        
    except Exception as e:
        print(f"[MONITOR] ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== Handwritten Assessment Evaluator ====================

@app.route('/api/handwritten-evaluation', methods=['POST'])
@jwt_required()
def evaluate_handwritten_assessment():
    """Evaluate handwritten answers against subject content"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        print(f"[HANDWRITTEN] User {user.email} starting evaluation")
        
        # Get uploaded files
        if 'subject_file' not in request.files or 'handwritten_file' not in request.files:
            return jsonify({'error': 'Both subject file and handwritten file required'}), 400
        
        subject_file = request.files['subject_file']
        handwritten_file = request.files['handwritten_file']
        marks_per_question = float(request.form.get('marks_per_question', 10.0))
        
        if subject_file.filename == '' or handwritten_file.filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        # Save files temporarily
        import tempfile
        from werkzeug.utils import secure_filename
        
        # Save subject file
        subject_ext = subject_file.filename.rsplit('.', 1)[1].lower()
        if subject_ext not in ['pdf', 'docx', 'txt']:
            return jsonify({'error': 'Subject file must be PDF, DOCX, or TXT'}), 400
        
        subject_temp = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{subject_ext}')
        subject_file.save(subject_temp.name)
        subject_temp.close()
        
        # Save handwritten file
        handwritten_ext = handwritten_file.filename.rsplit('.', 1)[1].lower()
        if handwritten_ext not in ['jpg', 'jpeg', 'png', 'pdf']:
            return jsonify({'error': 'Handwritten file must be JPG, PNG, or PDF'}), 400
        
        handwritten_temp = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{handwritten_ext}')
        handwritten_file.save(handwritten_temp.name)
        handwritten_temp.close()
        
        print(f"[HANDWRITTEN] Files saved: {subject_temp.name}, {handwritten_temp.name}")
        
        # Import and use evaluator
        from handwritten_evaluator import HandwrittenEvaluator
        
        evaluator = HandwrittenEvaluator(api_key=app.config['GEMINI_API_KEY'])
        results = evaluator.evaluate_handwritten_assessment(
            subject_temp.name,
            subject_ext,
            handwritten_temp.name,
            marks_per_question
        )
        
        # Clean up temp files
        import os
        os.unlink(subject_temp.name)
        os.unlink(handwritten_temp.name)
        
        if results['success']:
            print(f"[HANDWRITTEN] ✅ Evaluation complete: {results['total_marks']}/{results['max_marks']}")
            return jsonify(results), 200
        else:
            print(f"[HANDWRITTEN] ❌ Evaluation failed: {results.get('error')}")
            return jsonify(results), 400
        
    except Exception as e:
        print(f"[HANDWRITTEN] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== Initialize Database ====================

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()

# ==================== Main ====================

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, host='0.0.0.0', port=5000)
