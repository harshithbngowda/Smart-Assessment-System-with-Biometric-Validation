"""
Exam Monitoring Module
Handles real-time monitoring during exams for identity verification and cheating detection
"""

import cv2
import numpy as np
# Use high-accuracy ArcFace-based face recognition
from arcface_recognition import face_locations, face_encodings, compare_faces
import time
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
from datetime import datetime
import os
from config import Config

class ExamMonitor:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.cap = None
        self.monitor_window = None
        self.is_monitoring = False
        self.session_id = None
        self.student_data = None
        self.known_face_encodings = []
        self.warnings_count = 0
        self.last_warning_time = 0
        self.violation_log = []
        self._last_identity_check = 0.0
        self._last_object_check = 0.0
        
        # Load YOLO for object detection
        self.net = None
        self.output_layers = None
        self.classes = []
        self.phone_class_ids = None
        self._load_yolo_model()
    
    def _load_yolo_model(self):
        """Load YOLO model for object detection"""
        try:
            # Check if YOLO files exist
            need_paths = [
                ("CFG", Config.YOLO_CONFIG_PATH),
                ("WEIGHTS", Config.YOLO_WEIGHTS_PATH),
                ("CLASSES", Config.YOLO_CLASSES_PATH),
            ]
            for label, p in need_paths:
                self.logger.info(f"YOLO {label} path: {p} | exists={os.path.exists(p)}")
            # Try to auto-resolve if any missing
            if not all(os.path.exists(p) for _, p in need_paths):
                base_dir = os.path.dirname(Config.YOLO_CONFIG_PATH)
                try:
                    cand = os.listdir(base_dir)
                except Exception:
                    cand = []
                cfg = next((os.path.join(base_dir, f) for f in cand if f.lower().endswith('.cfg') and 'yolov4-tiny' in f.lower()), None)
                if not cfg:
                    cfg = next((os.path.join(base_dir, f) for f in cand if f.lower().endswith('.cfg')), None)
                weights = next((os.path.join(base_dir, f) for f in cand if f.lower().endswith('.weights') and 'yolov4-tiny' in f.lower()), None)
                if not weights:
                    weights = next((os.path.join(base_dir, f) for f in cand if f.lower().endswith('.weights')), None)
                classes = Config.YOLO_CLASSES_PATH if os.path.exists(Config.YOLO_CLASSES_PATH) else next((os.path.join(base_dir, f) for f in cand if f.lower().endswith('.names') or f.lower().endswith('coco.names')), None)

                self._yolo_cfg_path = cfg or Config.YOLO_CONFIG_PATH
                self._yolo_weights_path = weights or Config.YOLO_WEIGHTS_PATH
                self._yolo_classes_path = classes or Config.YOLO_CLASSES_PATH

                self.logger.warning("Auto-resolved YOLO paths:")
                self.logger.warning(f"  CFG: {self._yolo_cfg_path} exists={os.path.exists(self._yolo_cfg_path)}")
                self.logger.warning(f"  WEIGHTS: {self._yolo_weights_path} exists={os.path.exists(self._yolo_weights_path)}")
                self.logger.warning(f"  CLASSES: {self._yolo_classes_path} exists={os.path.exists(self._yolo_classes_path)}")

                if not (os.path.exists(self._yolo_cfg_path) and os.path.exists(self._yolo_weights_path) and os.path.exists(self._yolo_classes_path)):
                    self.logger.error("YOLO model files not found after auto-resolve. Object detection will be disabled.")
                    return
            else:
                self._yolo_cfg_path = Config.YOLO_CONFIG_PATH
                self._yolo_weights_path = Config.YOLO_WEIGHTS_PATH
                self._yolo_classes_path = Config.YOLO_CLASSES_PATH
            
            # Load YOLO
            # Load YOLO with resolved paths
            self.net = cv2.dnn.readNet(self._yolo_weights_path, self._yolo_cfg_path)
            layer_names = self.net.getLayerNames()
            uol = self.net.getUnconnectedOutLayers()
            # Handle both shapes: [[200], [267], [400]] or [200, 267, 400]
            try:
                self.output_layers = [layer_names[int(i[0]) - 1] for i in uol]
            except Exception:
                self.output_layers = [layer_names[int(i) - 1] for i in uol]
            
            # Load class names
            with open(self._yolo_classes_path, 'r') as f:
                self.classes = [line.strip() for line in f.readlines()]
            
            # Dynamically resolve phone-related class ids if available
            phone_names = {"cell phone", "cellphone", "mobile phone", "phone"}
            dyn_ids = [i for i, n in enumerate(self.classes) if n.lower() in phone_names]
            if dyn_ids:
                self.phone_class_ids = set(dyn_ids)
            else:
                # Fallback to config
                self.phone_class_ids = set(getattr(Config, 'PHONE_CLASS_IDS', [67]))
            self.logger.info(f"Phone classes: {[self.classes[i] for i in self.phone_class_ids]} at ids {sorted(self.phone_class_ids)}")
            
            self.logger.info("YOLO model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading YOLO model: {str(e)}")
            self.net = None
    
    def start_monitoring(self, name, student_id):
        """Start exam monitoring for a student"""
        try:
            # Get student data
            self.student_data = self.db_manager.get_student_data(student_id)
            if not self.student_data:
                messagebox.showerror("Error", "Student data not found!")
                return False
            
            # Load known face encodings
            self.known_face_encodings = self.db_manager.load_face_encodings(student_id)
            if not self.known_face_encodings:
                messagebox.showerror("Error", "Could not load student's face data!")
                return False
            
            # Start exam session in database
            self.session_id = self.db_manager.start_exam_session(student_id)
            if not self.session_id:
                messagebox.showerror("Error", "Could not start exam session!")
                return False
            
            # Reset monitoring variables
            self.warnings_count = 0
            self.violation_log = []
            self.last_warning_time = 0
            
            # Create monitoring window
            self._create_monitor_window()
            
            # Initialize camera
            if not self._initialize_camera():
                messagebox.showerror("Error", "Could not access camera!")
                return False
            
            # Start monitoring
            self.is_monitoring = True
            self._start_monitoring_loop()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting monitoring: {str(e)}")
            return False
    
    def _create_monitor_window(self):
        """Create the exam monitoring window"""
        self.monitor_window = tk.Toplevel()
        self.monitor_window.title("Exam Monitoring - Active")
        self.monitor_window.geometry(Config.MONITOR_WINDOW_SIZE)
        self.monitor_window.configure(bg=Config.BACKGROUND_COLOR)
        
        # Make window stay on top
        self.monitor_window.attributes('-topmost', True)
        
        # Student info frame
        info_frame = tk.Frame(self.monitor_window, bg=Config.BACKGROUND_COLOR)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        student_info = tk.Label(
            info_frame,
            text=f"Student: {self.student_data['name']} | ID: {self.student_data['student_id']}",
            font=("Arial", 14, "bold"),
            bg=Config.BACKGROUND_COLOR,
            fg=Config.TEXT_COLOR
        )
        student_info.pack(side=tk.LEFT)
        
        # Session time
        self.session_time_label = tk.Label(
            info_frame,
            text="Session Time: 00:00:00",
            font=("Arial", 12),
            bg=Config.BACKGROUND_COLOR,
            fg=Config.TEXT_COLOR
        )
        self.session_time_label.pack(side=tk.RIGHT)
        
        # Camera frame
        self.camera_frame = tk.Label(
            self.monitor_window,
            bg='black',
            width=800,
            height=600
        )
        self.camera_frame.pack(pady=10)
        
        # ALERT FRAME for multiple faces - BIG and VISIBLE
        self.alert_frame = tk.Frame(self.monitor_window, bg='red', relief='raised', bd=5)
        self.alert_label = tk.Label(
            self.alert_frame,
            text="",
            font=("Arial", 20, "bold"),
            bg='red',
            fg='white',
            padx=20,
            pady=15
        )
        self.alert_label.pack()
        # Hidden by default
        self.alert_frame.pack_forget()
        
        # Status frame
        status_frame = tk.Frame(self.monitor_window, bg=Config.BACKGROUND_COLOR)
        status_frame.pack(fill='x', padx=20, pady=10)
        
        # Identity status
        self.identity_status = tk.Label(
            status_frame,
            text="Identity: Verifying...",
            font=("Arial", 12, "bold"),
            bg=Config.BACKGROUND_COLOR,
            fg=Config.WARNING_COLOR
        )
        self.identity_status.pack(side=tk.LEFT)
        
        # Warnings counter
        self.warnings_label = tk.Label(
            status_frame,
            text=f"Warnings: {self.warnings_count}/{Config.MAX_WARNINGS}",
            font=("Arial", 12, "bold"),
            bg=Config.BACKGROUND_COLOR,
            fg=Config.SUCCESS_COLOR
        )
        self.warnings_label.pack(side=tk.RIGHT)
        
        # Violations log
        log_frame = tk.LabelFrame(
            self.monitor_window,
            text="Violations Log",
            font=("Arial", 12, "bold"),
            bg=Config.BACKGROUND_COLOR,
            fg=Config.TEXT_COLOR
        )
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Create scrollable text widget for log
        self.log_text = tk.Text(
            log_frame,
            height=8,
            font=("Courier", 10),
            bg='white',
            fg='black'
        )
        
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Control buttons
        button_frame = tk.Frame(self.monitor_window, bg=Config.BACKGROUND_COLOR)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        self.end_exam_button = tk.Button(
            button_frame,
            text="End Exam",
            command=self._end_exam,
            font=("Arial", 12, "bold"),
            bg=Config.ERROR_COLOR,
            fg='white',
            padx=20,
            pady=10
        )
        self.end_exam_button.pack(side=tk.RIGHT)
        
        # Handle window close
        self.monitor_window.protocol("WM_DELETE_WINDOW", self._end_exam)
        
        # Start session timer
        self.session_start_time = time.time()
        self._update_session_timer()
    
    def _initialize_camera(self):
        """Initialize the camera for monitoring"""
        try:
            self.cap = cv2.VideoCapture(Config.CAMERA_INDEX)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
            
            return self.cap.isOpened()
            
        except Exception as e:
            self.logger.error(f"Camera initialization error: {str(e)}")
            return False
    
    def _start_monitoring_loop(self):
        """Start the main monitoring loop"""
        threading.Thread(target=self._monitoring_loop, daemon=True).start()
        self._update_camera_feed()
    
    def _monitoring_loop(self):
        """Main monitoring loop that runs in a separate thread"""
        while self.is_monitoring and self.warnings_count < Config.MAX_WARNINGS:
            try:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        # Flip frame for mirror effect
                        frame = cv2.flip(frame, 1)
                        
                        # Check identity at intervals
                        now = time.time()
                        if now - self._last_identity_check >= Config.IDENTITY_CHECK_INTERVAL:
                            self._check_identity(frame)
                            self._last_identity_check = now
                        
                        # Check for prohibited objects at intervals
                        if self.net and Config.ENABLE_YOLO:
                            if now - self._last_object_check >= Config.OBJECT_CHECK_INTERVAL:
                                self._check_prohibited_objects(frame)
                                self._last_object_check = now
                
                time.sleep(Config.MONITORING_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {str(e)}")
                time.sleep(1)
        
        # If max warnings reached, end exam
        if self.warnings_count >= Config.MAX_WARNINGS:
            self._handle_max_warnings_reached()
    
    def _check_identity(self, frame):
        """Check if the person in frame matches the registered student"""
        try:
            # Find faces in the frame using imported functions
            detected_faces = face_locations(frame)
            detected_encodings = face_encodings(frame, detected_faces)
            
            if len(detected_faces) == 0:
                # No face detected - DON'T warn, just update status
                self._update_identity_status("Please look at camera", Config.WARNING_COLOR)
                # NO WARNING - student may just be looking down at paper/screen
                
            elif len(detected_faces) > 1:
                # Multiple faces detected - WARN (someone else in frame)
                # Make warning VERY VISIBLE
                num_faces = len(detected_faces)
                self._update_identity_status(f"🚨 {num_faces} FACES DETECTED - CHEATING! 🚨", Config.ERROR_COLOR)
                self._add_warning("multiple_faces", f"{num_faces} faces detected - CHEATING ATTEMPT!")
                # Flash warning - keep status for longer
                print(f"\n🚨🚨🚨 ALERT: {num_faces} FACES DETECTED - POSSIBLE CHEATING! 🚨🚨🚨")
                # Show BIG RED ALERT BOX
                if self.monitor_window and hasattr(self, 'alert_frame'):
                    self.alert_label.configure(text=f"⚠️⚠️ {num_faces} FACES DETECTED - CHEATING! ⚠️⚠️")
                    self.alert_frame.pack(fill='x', padx=20, pady=10, before=self.camera_frame.master.winfo_children()[3])
                    self.monitor_window.update()
                
            else:
                # One face detected - Hide alert box
                if self.monitor_window and hasattr(self, 'alert_frame'):
                    self.alert_frame.pack_forget()
                
                # Check if it matches
                if len(detected_encodings) > 0:
                    face_encoding = detected_encodings[0]
                    
                    # Compare with known encodings using ArcFace cosine-sim threshold
                    matches = compare_faces(
                        self.known_face_encodings,
                        face_encoding,
                        tolerance=Config.ARC_FACE_SIM_THRESHOLD
                    )
                    
                    # Count how many matches (need at least 50% to verify - strict)
                    match_percentage = sum(matches) / len(matches) * 100 if matches else 0
                    
                    if match_percentage >= 50:  # Strict - need solid majority to verify
                        # Identity verified
                        self._update_identity_status("✓ Identity Verified", Config.SUCCESS_COLOR)
                    else:
                        # Unknown person - WARN (this is actual cheating)
                        self._update_identity_status("⚠️ UNKNOWN PERSON!", Config.ERROR_COLOR)
                        self._add_warning("identity_mismatch", "Unknown person detected - not registered student")
                else:
                    # Could not extract encoding, don't warn
                    self._update_identity_status("Verifying...", Config.WARNING_COLOR)
                    
        except Exception as e:
            self.logger.error(f"Identity check error: {str(e)}")
    
    def _check_prohibited_objects(self, frame):
        """Check for prohibited objects like phones using YOLO"""
        try:
            height, width, channels = frame.shape
            
            # Prepare image for YOLO
            inp = int(getattr(Config, 'YOLO_INPUT_SIZE', 320))
            blob = cv2.dnn.blobFromImage(frame, 1/255.0, (inp, inp), (0, 0, 0), swapRB=True, crop=False)
            self.net.setInput(blob)
            outputs = self.net.forward(self.output_layers)
            
            # Process detections
            boxes = []
            confidences = []
            class_ids = []
            
            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    # Debug: log top detections occasionally
                    if confidence > 0.2:
                        try:
                            cname = self.classes[class_id]
                        except Exception:
                            cname = str(class_id)
                        self.logger.debug(f"Det: class={cname}({class_id}) conf={float(confidence):.2f}")
                    
                    if confidence > Config.PHONE_DETECTION_CONFIDENCE:
                        # Object candidate detected
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)
                        boxes.append([x, y, w, h])
                        confidences.append(float(confidence))
                        class_ids.append(int(class_id))
            
            # Apply non-maximum suppression
            idxs = cv2.dnn.NMSBoxes(boxes, confidences, Config.PHONE_DETECTION_CONFIDENCE, 0.4)
            if isinstance(idxs, (list, tuple)):
                nms_idx = list(idxs)
            elif hasattr(idxs, 'flatten'):
                nms_idx = idxs.flatten().tolist()
            else:
                nms_idx = []

            # Filter to only phone classes
            phone_hits = []
            for i in nms_idx:
                try:
                    i0 = int(i)
                    if class_ids[i0] in (self.phone_class_ids or set(getattr(Config, 'PHONE_CLASS_IDS', [67]))):
                        phone_hits.append(i0)
                except Exception:
                    continue

            if len(phone_hits) > 0:
                for i0 in phone_hits:
                    try:
                        cname = self.classes[class_ids[i0]]
                    except Exception:
                        cname = 'phone'
                self.logger.info(f"Phone detected: {len(phone_hits)} boxes, confs {[confidences[i] for i in phone_hits]}")
                self._add_warning("prohibited_object", "Mobile phone detected")
        
        except Exception as e:
            self.logger.error(f"Object detection error: {str(e)}")
    
    def _add_warning(self, warning_type, message):
        """Add a warning to the system"""
        current_time = time.time()
        
        # Check cooldown period
        if current_time - self.last_warning_time < Config.WARNING_COOLDOWN:
            return
        
        self.warnings_count += 1
        self.last_warning_time = current_time
        
        # Log warning to database
        self.db_manager.add_warning(self.session_id, warning_type, message)
        
        # Add to violation log
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] WARNING {self.warnings_count}: {message}\n"
        self.violation_log.append(log_entry)
        
        # Update UI
        self._update_warnings_display()
        self._update_violations_log()
        
        # Check if max warnings reached
        if self.warnings_count >= Config.MAX_WARNINGS:
            self._handle_max_warnings_reached()
    
    def _update_identity_status(self, status, color):
        """Update the identity status display"""
        if self.monitor_window:
            self.identity_status.configure(text=f"Identity: {status}", fg=color)
    
    def _update_warnings_display(self):
        """Update the warnings counter display"""
        if self.monitor_window:
            color = Config.SUCCESS_COLOR
            if self.warnings_count >= Config.MAX_WARNINGS * 0.8:
                color = Config.ERROR_COLOR
            elif self.warnings_count >= Config.MAX_WARNINGS * 0.6:
                color = Config.WARNING_COLOR
            
            self.warnings_label.configure(
                text=f"Warnings: {self.warnings_count}/{Config.MAX_WARNINGS}",
                fg=color
            )
    
    def _update_violations_log(self):
        """Update the violations log display"""
        if self.monitor_window and self.log_text:
            self.log_text.delete(1.0, tk.END)
            for entry in self.violation_log:
                self.log_text.insert(tk.END, entry)
            self.log_text.see(tk.END)
    
    def _update_session_timer(self):
        """Update the session timer display"""
        if self.monitor_window and self.is_monitoring:
            elapsed = int(time.time() - self.session_start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            
            time_str = f"Session Time: {hours:02d}:{minutes:02d}:{seconds:02d}"
            self.session_time_label.configure(text=time_str)
            
            # Schedule next update
            self.monitor_window.after(1000, self._update_session_timer)
    
    def _update_camera_feed(self):
        """Update the camera feed display"""
        if self.cap and self.cap.isOpened() and self.monitor_window and self.is_monitoring:
            ret, frame = self.cap.read()
            if ret:
                # Flip frame horizontally
                frame = cv2.flip(frame, 1)
                
                if getattr(Config, 'DRAW_BOXES_IN_PREVIEW', True):
                    # Draw face detection rectangles using imported functions
                    detected_faces = face_locations(frame)
                    for (top, right, bottom, left) in detected_faces:
                        # Determine color based on identity verification
                        color = (0, 255, 0)  # Green for verified
                        if len(detected_faces) > 1:
                            color = (255, 0, 0)  # Red for multiple faces
                        elif len(detected_faces) == 1:
                            # Check if face matches
                            detected_encodings = face_encodings(frame, [(top, right, bottom, left)])
                            if detected_encodings:
                                matches = compare_faces(
                                    self.known_face_encodings, 
                                    detected_encodings[0], 
                                    tolerance=Config.ARC_FACE_SIM_THRESHOLD
                                )
                                if not any(matches):
                                    color = (255, 0, 0)  # Red for unknown person
                        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Convert to PIL Image and display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                pil_image = pil_image.resize((800, 600), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(pil_image)
                
                self.camera_frame.configure(image=photo)
                self.camera_frame.image = photo
            
            # Schedule next update
            if self.monitor_window:
                self.monitor_window.after(int(Config.PREVIEW_FPS_MS), self._update_camera_feed)
    
    def _handle_max_warnings_reached(self):
        """Handle when maximum warnings are reached"""
        self.is_monitoring = False
        
        if self.monitor_window:
            messagebox.showerror(
                "Exam Terminated", 
                f"Maximum warnings ({Config.MAX_WARNINGS}) reached. Exam has been terminated."
            )
        
        self._end_exam()
    
    def _end_exam(self):
        """End the exam monitoring session"""
        self.is_monitoring = False
        
        # End session in database
        if self.session_id:
            self.db_manager.end_exam_session(self.session_id, self.violation_log)
        
        # Cleanup
        if self.cap:
            self.cap.release()
            self.cap = None
        
        if self.monitor_window:
            self.monitor_window.destroy()
            self.monitor_window = None
        
        # Show summary
        self._show_exam_summary()
    
    def _show_exam_summary(self):
        """Show exam session summary"""
        try:
            if self.session_id:
                warnings_count = self.db_manager.get_session_warnings_count(self.session_id)
                
                summary_message = f"""
Exam Session Summary:
Student: {self.student_data['name']}
ID: {self.student_data['student_id']}
Total Warnings: {warnings_count}
Session Status: {'TERMINATED' if warnings_count >= Config.MAX_WARNINGS else 'COMPLETED'}

The exam session has been recorded in the system.
                """
                
                messagebox.showinfo("Exam Summary", summary_message)
                
        except Exception as e:
            self.logger.error(f"Error showing exam summary: {str(e)}")
