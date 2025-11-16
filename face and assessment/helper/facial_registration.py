"""
Facial Registration Module
Handles student registration with facial data capture and processing
"""

import cv2
import numpy as np
# Use simple OpenCV-based face recognition
from simple_face_detection import face_locations, face_encodings
import os
import time
import logging
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import threading
from config import Config

class FacialRegistration:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.cap = None
        self.registration_window = None
        self.is_capturing = False
        self.captured_photos = []
        self.face_encodings = []
        
    def register_student(self, name, student_id):
        """Main registration function"""
        try:
            # Check if student already exists
            if self.db_manager.student_exists(name, student_id):
                messagebox.showerror("Error", "Student already registered!")
                return False
            
            # Start the registration process
            success = self._start_registration_process(name, student_id)
            return success
            
        except Exception as e:
            self.logger.error(f"Registration error: {str(e)}")
            return False
    
    def _start_registration_process(self, name, student_id):
        """Start the photo capture and registration process"""
        self.captured_photos = []
        self.face_encodings = []
        
        # Create registration window
        self._create_registration_window(name, student_id)
        
        # Start camera
        if not self._initialize_camera():
            messagebox.showerror("Error", "Could not access camera!")
            return False
        
        # Start capture process
        self._start_photo_capture()
        
        return True
    
    def _create_registration_window(self, name, student_id):
        """Create the registration interface window"""
        self.registration_window = tk.Toplevel()
        self.registration_window.title("Student Registration - Photo Capture")
        self.registration_window.geometry("800x700")
        self.registration_window.configure(bg=Config.BACKGROUND_COLOR)
        
        # Make window modal
        self.registration_window.transient()
        self.registration_window.grab_set()
        
        # Title
        title_label = tk.Label(
            self.registration_window,
            text=f"Registering: {name} (ID: {student_id})",
            font=("Arial", 16, "bold"),
            bg=Config.BACKGROUND_COLOR,
            fg=Config.TEXT_COLOR
        )
        title_label.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(
            self.registration_window,
            text="Look directly at the camera. Multiple photos will be taken automatically.\nMove your head slightly between captures for better accuracy.",
            font=("Arial", 12),
            bg=Config.BACKGROUND_COLOR,
            fg=Config.TEXT_COLOR,
            justify=tk.CENTER
        )
        instructions.pack(pady=10)
        
        # Camera frame
        self.camera_frame = tk.Label(
            self.registration_window,
            bg='black',
            width=640,
            height=480
        )
        self.camera_frame.pack(pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.registration_window,
            variable=self.progress_var,
            maximum=Config.PHOTOS_PER_REGISTRATION,
            length=400
        )
        self.progress_bar.pack(pady=10)
        
        # Status label
        self.status_label = tk.Label(
            self.registration_window,
            text="Initializing camera...",
            font=("Arial", 12),
            bg=Config.BACKGROUND_COLOR,
            fg=Config.WARNING_COLOR
        )
        self.status_label.pack(pady=5)
        
        # Control buttons
        button_frame = tk.Frame(self.registration_window, bg=Config.BACKGROUND_COLOR)
        button_frame.pack(pady=20)
        
        self.start_button = tk.Button(
            button_frame,
            text="Start Capture",
            command=self._start_capture,
            font=("Arial", 12, "bold"),
            bg=Config.SUCCESS_COLOR,
            fg='white',
            padx=20,
            pady=10
        )
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        self.cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel_registration,
            font=("Arial", 12, "bold"),
            bg=Config.ERROR_COLOR,
            fg='white',
            padx=20,
            pady=10
        )
        self.cancel_button.pack(side=tk.LEFT, padx=10)
        
        # Store student info
        self.current_name = name
        self.current_student_id = student_id
        
        # Handle window close
        self.registration_window.protocol("WM_DELETE_WINDOW", self._cancel_registration)
    
    def _initialize_camera(self):
        """Initialize the camera"""
        try:
            self.cap = cv2.VideoCapture(Config.CAMERA_INDEX)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
            
            if not self.cap.isOpened():
                return False
            
            # Start video feed
            self._update_camera_feed()
            return True
            
        except Exception as e:
            self.logger.error(f"Camera initialization error: {str(e)}")
            return False
    
    def _update_camera_feed(self):
        """Update the camera feed in the GUI"""
        if self.cap and self.cap.isOpened() and self.registration_window:
            ret, frame = self.cap.read()
            if ret:
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Detect faces and draw rectangles using imported function
                detected_faces = face_locations(frame)
                for (top, right, bottom, left) in detected_faces:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                # Convert to RGB and then to PIL Image
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                
                # Resize to fit the label
                pil_image = pil_image.resize((640, 480), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(pil_image)
                
                # Update the label
                self.camera_frame.configure(image=photo)
                self.camera_frame.image = photo
            
            # Schedule next update
            if self.registration_window:
                self.registration_window.after(30, self._update_camera_feed)
    
    def _start_capture(self):
        """Start the photo capture process"""
        self.is_capturing = True
        self.start_button.configure(state='disabled')
        self.status_label.configure(text="Starting capture in 3 seconds...", fg=Config.WARNING_COLOR)
        
        # Start capture in a separate thread
        threading.Thread(target=self._capture_photos, daemon=True).start()
    
    def _capture_photos(self):
        """Capture multiple photos for registration"""
        try:
            # Countdown
            for i in range(3, 0, -1):
                if not self.is_capturing:
                    return
                self.status_label.configure(text=f"Starting in {i}...")
                time.sleep(1)
            
            photos_captured = 0
            
            while photos_captured < Config.PHOTOS_PER_REGISTRATION and self.is_capturing:
                ret, frame = self.cap.read()
                if not ret:
                    continue
                
                # Flip frame
                frame = cv2.flip(frame, 1)
                
                # Detect faces using imported function
                detected_faces = face_locations(frame)
                
                if len(detected_faces) == 1:  # Exactly one face detected
                    # Capture the photo
                    self.captured_photos.append(frame.copy())
                    photos_captured += 1
                    
                    # Update progress
                    self.progress_var.set(photos_captured)
                    self.status_label.configure(
                        text=f"Captured {photos_captured}/{Config.PHOTOS_PER_REGISTRATION} photos",
                        fg=Config.SUCCESS_COLOR
                    )
                    
                    # Wait between captures
                    time.sleep(1.5)
                    
                elif len(detected_faces) == 0:
                    self.status_label.configure(text="No face detected. Please look at the camera.", fg=Config.ERROR_COLOR)
                    time.sleep(0.5)
                    
                else:
                    self.status_label.configure(text="Multiple faces detected. Please ensure only you are visible.", fg=Config.ERROR_COLOR)
                    time.sleep(0.5)
            
            if photos_captured == Config.PHOTOS_PER_REGISTRATION:
                self._process_captured_photos()
            
        except Exception as e:
            self.logger.error(f"Photo capture error: {str(e)}")
            self.status_label.configure(text="Capture failed!", fg=Config.ERROR_COLOR)
    
    def _process_captured_photos(self):
        """Process captured photos and create face encodings"""
        try:
            self.status_label.configure(text="Processing photos and creating face encodings...", fg=Config.WARNING_COLOR)
            
            all_encodings = []
            processed_count = 0
            
            # Process original photos
            for photo in self.captured_photos:
                encodings = self._extract_face_encodings(photo)
                if encodings:
                    all_encodings.extend(encodings)
                    processed_count += 1
            
            # Create augmented versions
            self.status_label.configure(text="Creating augmented versions for better accuracy...", fg=Config.WARNING_COLOR)
            
            for photo in self.captured_photos:
                augmented_photos = self._augment_photo(photo)
                for aug_photo in augmented_photos:
                    encodings = self._extract_face_encodings(aug_photo)
                    if encodings:
                        all_encodings.extend(encodings)
            
            if len(all_encodings) > 0:
                self.face_encodings = all_encodings
                self._save_registration_data()
            else:
                messagebox.showerror("Error", "Could not extract face features. Please try again.")
                self._cancel_registration()
                
        except Exception as e:
            self.logger.error(f"Photo processing error: {str(e)}")
            messagebox.showerror("Error", "Photo processing failed!")
            self._cancel_registration()
    
    def _extract_face_encodings(self, image):
        """Extract face encodings from an image"""
        try:
            # Find face locations using imported function
            detected_faces = face_locations(image)
            
            if len(detected_faces) == 1:
                # Extract face encodings using imported function
                encodings = face_encodings(image, detected_faces)
                return encodings
            
            return []
            
        except Exception as e:
            self.logger.error(f"Face encoding extraction error: {str(e)}")
            return []
    
    def _augment_photo(self, image):
        """Create augmented versions of a photo for better training"""
        augmented_photos = []
        
        try:
            # Convert to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Brightness variations
            for brightness_factor in [0.8, 1.2]:
                enhancer = ImageEnhance.Brightness(pil_image)
                bright_image = enhancer.enhance(brightness_factor)
                augmented_photos.append(cv2.cvtColor(np.array(bright_image), cv2.COLOR_RGB2BGR))
            
            # Contrast variations
            for contrast_factor in [0.9, 1.1]:
                enhancer = ImageEnhance.Contrast(pil_image)
                contrast_image = enhancer.enhance(contrast_factor)
                augmented_photos.append(cv2.cvtColor(np.array(contrast_image), cv2.COLOR_RGB2BGR))
            
            # Slight blur
            blurred = pil_image.filter(ImageFilter.GaussianBlur(radius=0.5))
            augmented_photos.append(cv2.cvtColor(np.array(blurred), cv2.COLOR_RGB2BGR))
            
            return augmented_photos[:Config.AUGMENTATION_COUNT]
            
        except Exception as e:
            self.logger.error(f"Photo augmentation error: {str(e)}")
            return []
    
    def _save_registration_data(self):
        """Save the registration data to database"""
        try:
            self.status_label.configure(text="Saving registration data...", fg=Config.WARNING_COLOR)
            
            # Log details
            self.logger.info(f"Saving {len(self.face_encodings)} face encodings for student {self.current_student_id}")
            print(f"\n📝 Registration Summary:")
            print(f"   Student: {self.current_name}")
            print(f"   ID: {self.current_student_id}")
            print(f"   Photos captured: {len(self.captured_photos)}")
            print(f"   Face encodings: {len(self.face_encodings)}")
            
            # Save face encodings to file
            encodings_path = self.db_manager.save_face_encodings(
                self.current_student_id, 
                self.face_encodings
            )
            
            if encodings_path:
                print(f"   ✓ Encodings saved to: {encodings_path}")
                
                # Save student to database
                success = self.db_manager.register_student(
                    self.current_name,
                    self.current_student_id,
                    encodings_path,
                    len(self.captured_photos)
                )
                
                if success:
                    print(f"   ✓ Student registered in database")
                    self.status_label.configure(text="Registration completed successfully!", fg=Config.SUCCESS_COLOR)
                    
                    success_msg = (f"Student {self.current_name} registered successfully!\n\n"
                                 f"Photos captured: {len(self.captured_photos)}\n"
                                 f"Face encodings created: {len(self.face_encodings)}\n"
                                 f"Data saved at: {encodings_path}")
                    messagebox.showinfo("Success", success_msg)
                    self._close_registration_window()
                else:
                    print(f"   ✗ Failed to save to database")
                    messagebox.showerror("Error", "Failed to save student data to database!")
                    self._cancel_registration()
            else:
                print(f"   ✗ Failed to save face encodings")
                messagebox.showerror("Error", "Failed to save face encodings to file!")
                self._cancel_registration()
                
        except Exception as e:
            self.logger.error(f"Registration save error: {str(e)}")
            messagebox.showerror("Error", "Failed to save registration data!")
            self._cancel_registration()
    
    def _cancel_registration(self):
        """Cancel the registration process"""
        self.is_capturing = False
        self._close_registration_window()
    
    def _close_registration_window(self):
        """Close the registration window and cleanup"""
        if self.cap:
            self.cap.release()
            self.cap = None
        
        if self.registration_window:
            self.registration_window.destroy()
            self.registration_window = None
