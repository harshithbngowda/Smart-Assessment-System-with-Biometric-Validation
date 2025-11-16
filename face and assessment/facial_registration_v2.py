"""
Improved Facial Registration Module - Automatic & User-Friendly
Handles student registration with automatic photo capture
"""

import cv2
import numpy as np
# Use high-accuracy ArcFace backend for registration encodings
from arcface_recognition import face_locations, face_encodings
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
        
    # ---------- Utility: Safe UI Updates ----------
    def _safe_label_config(self, label, **kwargs):
        try:
            if self.registration_window and label:
                label.configure(**kwargs)
        except Exception:
            # Window may have been closed; ignore
            pass

    def _safe_window_update(self):
        try:
            if self.registration_window:
                self.registration_window.update()
        except Exception:
            pass

    def register_student(self, name, student_id):
        """Main registration function"""
        try:
            # Check if student already exists
            if self.db_manager.student_exists(name, student_id):
                messagebox.showerror("Error", "Student already registered!")
                return False
            
            print(f"\n{'='*60}")
            print(f"Starting registration for: {name} (ID: {student_id})")
            print(f"{'='*60}")
            
            # Start the registration process
            success = self._start_registration_process(name, student_id)
            return success
            
        except Exception as e:
            self.logger.error(f"Registration error: {str(e)}")
            print(f"❌ Registration error: {str(e)}")
            messagebox.showerror("Error", f"Registration failed: {str(e)}")
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
        
        return True
    
    def _create_registration_window(self, name, student_id):
        """Create the registration interface window"""
        self.registration_window = tk.Toplevel()
        self.registration_window.title("Student Registration - Automatic Photo Capture")
        self.registration_window.geometry("900x750")
        self.registration_window.configure(bg=Config.BACKGROUND_COLOR)
        
        # Make window modal
        self.registration_window.transient()
        self.registration_window.grab_set()
        
        # Title
        title_label = tk.Label(
            self.registration_window,
            text=f"Registering: {name} (ID: {student_id})",
            font=("Arial", 18, "bold"),
            bg=Config.BACKGROUND_COLOR,
            fg=Config.TEXT_COLOR
        )
        title_label.pack(pady=15)
        
        # Instructions - BIG and CLEAR
        instructions_frame = tk.Frame(self.registration_window, bg='#ffffcc', relief='raised', bd=2)
        instructions_frame.pack(pady=10, padx=20, fill='x')
        
        instructions = tk.Label(
            instructions_frame,
            text="📸 AUTOMATIC CAPTURE WILL START IN 5 SECONDS\n\n"
                 "✓ Look directly at the camera\n"
                 "✓ Keep your face in the green box\n"
                 "✓ System will capture 15 photos automatically\n"
                 "✓ Move your head slightly between captures",
            font=("Arial", 13, "bold"),
            bg='#ffffcc',
            fg='#333333',
            justify=tk.LEFT,
            padx=20,
            pady=15
        )
        instructions.pack()
        
        # Camera frame with border
        camera_container = tk.Frame(self.registration_window, bg='black', relief='solid', bd=3)
        camera_container.pack(pady=15)
        
        self.camera_frame = tk.Label(
            camera_container,
            bg='black',
            width=800,
            height=600
        )
        self.camera_frame.pack()
        
        # Progress section
        progress_frame = tk.Frame(self.registration_window, bg=Config.BACKGROUND_COLOR)
        progress_frame.pack(pady=10, padx=20, fill='x')
        
        # Progress bar - LARGER
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=Config.PHOTOS_PER_REGISTRATION,
            length=600,
            mode='determinate'
        )
        self.progress_bar.pack(pady=10)
        
        # Status label - LARGER
        self.status_label = tk.Label(
            progress_frame,
            text="⏳ Initializing camera...",
            font=("Arial", 14, "bold"),
            bg=Config.BACKGROUND_COLOR,
            fg=Config.WARNING_COLOR,
            height=2
        )
        self.status_label.pack(pady=10)
        
        # Photo counter - LARGER
        self.counter_label = tk.Label(
            progress_frame,
            text="Photos: 0/15",
            font=("Arial", 16, "bold"),
            bg=Config.BACKGROUND_COLOR,
            fg=Config.PRIMARY_COLOR
        )
        self.counter_label.pack(pady=5)
        
        # Control buttons
        button_frame = tk.Frame(self.registration_window, bg=Config.BACKGROUND_COLOR)
        button_frame.pack(pady=15)
        
        self.cancel_button = tk.Button(
            button_frame,
            text="❌ Cancel",
            command=self._cancel_registration,
            font=("Arial", 12, "bold"),
            bg=Config.ERROR_COLOR,
            fg='white',
            padx=30,
            pady=12,
            width=15
        )
        self.cancel_button.pack()
        
        # Store student info
        self.current_name = name
        self.current_student_id = student_id
        
        # Handle window close
        self.registration_window.protocol("WM_DELETE_WINDOW", self._cancel_registration)
    
    def _initialize_camera(self):
        """Initialize the camera"""
        try:
            print("🎥 Initializing camera...")
            self.cap = cv2.VideoCapture(Config.CAMERA_INDEX)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
            
            if not self.cap.isOpened():
                print("❌ Failed to open camera")
                return False
            
            print("✓ Camera initialized successfully")
            
            # Start video feed
            self._update_camera_feed()
            
            # AUTO-START capture after 5 seconds
            self.registration_window.after(5000, self._auto_start_capture)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Camera initialization error: {str(e)}")
            print(f"❌ Camera error: {str(e)}")
            return False
    
    def _auto_start_capture(self):
        """Automatically start capture - no button needed"""
        if self.registration_window and self.cap and self.cap.isOpened():
            print("\n🚀 AUTO-STARTING CAPTURE...")
            self.is_capturing = True
            self._safe_label_config(self.status_label, text="🎬 Starting capture in 3 seconds...", fg=Config.WARNING_COLOR)
            threading.Thread(target=self._capture_photos, daemon=True).start()
    
    def _update_camera_feed(self):
        """Update the camera feed in the GUI"""
        if self.cap and self.cap.isOpened() and self.registration_window:
            ret, frame = self.cap.read()
            if ret:
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Detect faces and draw rectangles
                detected_faces = face_locations(frame)
                
                for (top, right, bottom, left) in detected_faces:
                    # Draw thick green rectangle
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 3)
                    # Add text
                    cv2.putText(frame, "FACE DETECTED", (left, top-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Add face count
                face_text = f"Faces: {len(detected_faces)}"
                cv2.putText(frame, face_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Convert to RGB and then to PIL Image
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                
                # Resize to fit the label
                pil_image = pil_image.resize((800, 600), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(pil_image)
                
                # Update the label
                self.camera_frame.configure(image=photo)
                self.camera_frame.image = photo
            
            # Schedule next update
            if self.registration_window:
                self.registration_window.after(30, self._update_camera_feed)
    
    def _capture_photos(self):
        """Capture multiple photos for registration"""
        try:
            # Countdown
            for i in range(3, 0, -1):
                if not self.is_capturing:
                    return
                self._safe_label_config(self.status_label, text=f"⏳ Starting in {i}...")
                self._safe_window_update()
                time.sleep(1)
            
            photos_captured = 0
            attempts = 0
            max_attempts = Config.PHOTOS_PER_REGISTRATION * 5  # Give multiple chances
            
            print(f"\n📸 Starting photo capture (target: {Config.PHOTOS_PER_REGISTRATION} photos)...")
            
            while photos_captured < Config.PHOTOS_PER_REGISTRATION and self.is_capturing and attempts < max_attempts:
                attempts += 1
                ret, frame = self.cap.read()
                if not ret:
                    continue
                
                # Flip frame
                frame = cv2.flip(frame, 1)
                
                # Detect faces
                detected_faces = face_locations(frame)
                
                if len(detected_faces) == 1:  # Exactly one face detected
                    # Capture the photo
                    self.captured_photos.append(frame.copy())
                    photos_captured += 1
                    
                    print(f"✓ Captured photo {photos_captured}/{Config.PHOTOS_PER_REGISTRATION}")
                    
                    # Update progress
                    self.progress_var.set(photos_captured)
                    self._safe_label_config(self.counter_label, text=f"Photos: {photos_captured}/{Config.PHOTOS_PER_REGISTRATION}")
                    self._safe_label_config(
                        self.status_label,
                        text=f"✓ Captured {photos_captured}/{Config.PHOTOS_PER_REGISTRATION} photos - Great!",
                        fg=Config.SUCCESS_COLOR
                    )
                    self._safe_window_update()
                    
                    # Wait between captures
                    time.sleep(1.2)
                    
                elif len(detected_faces) == 0:
                    self._safe_label_config(
                        self.status_label,
                        text="⚠️ No face detected. Please look at the camera.",
                        fg=Config.ERROR_COLOR
                    )
                    self._safe_window_update()
                    time.sleep(0.3)
                    
                else:
                    self._safe_label_config(
                        self.status_label,
                        text="⚠️ Multiple faces detected. Please ensure only you are visible.",
                        fg=Config.ERROR_COLOR
                    )
                    self._safe_window_update()
                    time.sleep(0.3)
            
            if photos_captured == Config.PHOTOS_PER_REGISTRATION:
                print(f"\n✓ Successfully captured all {photos_captured} photos!")
                self._process_captured_photos()
            else:
                print(f"\n⚠️ Only captured {photos_captured} photos out of {Config.PHOTOS_PER_REGISTRATION}")
                if photos_captured >= 5:  # If we got at least 5 photos, proceed anyway
                    print("Proceeding with available photos...")
                    self._process_captured_photos()
                else:
                    messagebox.showerror("Error", f"Could not capture enough photos. Only got {photos_captured}. Please try again in better lighting.")
                    self._cancel_registration()
            
        except Exception as e:
            self.logger.error(f"Photo capture error: {str(e)}")
            print(f"❌ Capture error: {str(e)}")
            self._safe_label_config(self.status_label, text="❌ Capture failed!", fg=Config.ERROR_COLOR)
            try:
                messagebox.showerror("Error", f"Capture failed: {str(e)}")
            except Exception:
                pass
    
    def _process_captured_photos(self):
        """Process captured photos and create face encodings"""
        try:
            self._safe_label_config(self.status_label, text="⚙️ Processing photos...", fg=Config.WARNING_COLOR)
            self._safe_window_update()
            
            print(f"\n⚙️ Processing {len(self.captured_photos)} photos...")
            
            all_encodings = []
            processed_count = 0
            
            # Process original photos
            for i, photo in enumerate(self.captured_photos):
                encodings = self._extract_face_encodings(photo)
                if encodings:
                    all_encodings.extend(encodings)
                    processed_count += 1
                    print(f"  ✓ Processed photo {i+1}/{len(self.captured_photos)}")
            
            # Augmentation phase (optional + time-capped)
            if Config.AUGMENTATION_ENABLED and not Config.FAST_MODE_DEFAULT:
                print(f"\n🔄 Creating augmented versions for better accuracy (time cap: {Config.AUGMENTATION_MAX_SECONDS}s)...")
                self._safe_label_config(self.status_label, text="🔄 Creating variations for better accuracy...", fg=Config.WARNING_COLOR)
                self._safe_window_update()
                aug_start = time.time()
                total_aug = 0
                for i, photo in enumerate(self.captured_photos):
                    if time.time() - aug_start > Config.AUGMENTATION_MAX_SECONDS:
                        print("⏱️ Augmentation time cap reached. Proceeding with current encodings.")
                        break
                    augmented_photos = self._augment_photo(photo)
                    for j, aug_photo in enumerate(augmented_photos):
                        if time.time() - aug_start > Config.AUGMENTATION_MAX_SECONDS:
                            print("⏱️ Augmentation time cap reached inside loop. Breaking.")
                            break
                        encodings = self._extract_face_encodings(aug_photo)
                        if encodings:
                            all_encodings.extend(encodings)
                            total_aug += 1
                    if i % 2 == 0:
                        print(f"  • Augmented sets processed: {i+1}/{len(self.captured_photos)} | Encodings so far: {len(all_encodings)}")
                print(f"✓ Augmentation complete. Added ~{total_aug} augmented encodings. Total encodings: {len(all_encodings)}")
            else:
                print("⏩ Fast mode enabled: skipping augmentation to speed up registration.")
                self._safe_label_config(self.status_label, text="⏩ Fast mode: skipping augmentation", fg=Config.SUCCESS_COLOR)
                self._safe_window_update()
            
            print(f"✓ Created {len(all_encodings)} total face encodings")
            
            if len(all_encodings) > 0:
                self.face_encodings = all_encodings
                self._save_registration_data()
            else:
                print("❌ Could not extract any face features")
                messagebox.showerror("Error", "Could not extract face features. Please try again.")
                self._cancel_registration()
                
        except Exception as e:
            self.logger.error(f"Photo processing error: {str(e)}")
            print(f"❌ Processing error: {str(e)}")
            messagebox.showerror("Error", f"Photo processing failed: {str(e)}")
            self._cancel_registration()
    
    def _extract_face_encodings(self, image):
        """Extract face encodings from an image"""
        try:
            detected_faces = face_locations(image)
            
            if len(detected_faces) >= 1:  # Accept even if multiple faces, take first
                encodings = face_encodings(image, [detected_faces[0]])
                return encodings
            
            return []
            
        except Exception as e:
            self.logger.error(f"Face encoding extraction error: {str(e)}")
            return []
    
    def _augment_photo(self, image):
        """Create augmented versions of a photo for maximum robustness"""
        augmented_photos = []
        
        try:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Brightness variations (MORE variations)
            for brightness_factor in [0.75, 0.85, 0.95, 1.05, 1.15, 1.25]:
                enhancer = ImageEnhance.Brightness(pil_image)
                bright_image = enhancer.enhance(brightness_factor)
                augmented_photos.append(cv2.cvtColor(np.array(bright_image), cv2.COLOR_RGB2BGR))
            
            # Contrast variations
            for contrast_factor in [0.85, 0.95, 1.05, 1.15]:
                enhancer = ImageEnhance.Contrast(pil_image)
                contrast_image = enhancer.enhance(contrast_factor)
                augmented_photos.append(cv2.cvtColor(np.array(contrast_image), cv2.COLOR_RGB2BGR))
            
            # Sharpness variations
            for sharpness_factor in [0.8, 1.2]:
                enhancer = ImageEnhance.Sharpness(pil_image)
                sharp_image = enhancer.enhance(sharpness_factor)
                augmented_photos.append(cv2.cvtColor(np.array(sharp_image), cv2.COLOR_RGB2BGR))
            
            # Blur variations
            for blur_radius in [0.3, 0.7]:
                blurred = pil_image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                augmented_photos.append(cv2.cvtColor(np.array(blurred), cv2.COLOR_RGB2BGR))
            
            return augmented_photos[:Config.AUGMENTATION_COUNT]
            
        except Exception as e:
            self.logger.error(f"Photo augmentation error: {str(e)}")
            return []
    
    def _save_registration_data(self):
        """Save the registration data to database"""
        try:
            self._safe_label_config(self.status_label, text="💾 Saving registration data...", fg=Config.WARNING_COLOR)
            self._safe_window_update()
            
            print(f"\n{'='*60}")
            print(f"📝 Registration Summary:")
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
                    print(f"{'='*60}\n")
                    
                    self._safe_label_config(self.status_label, text="✅ Registration completed successfully!", fg=Config.SUCCESS_COLOR)
                    self._safe_window_update()
                    time.sleep(1)
                    
                    success_msg = (f"✅ Student {self.current_name} registered successfully!\n\n"
                                 f"📸 Photos captured: {len(self.captured_photos)}\n"
                                 f"🔐 Face encodings created: {len(self.face_encodings)}\n"
                                 f"💾 Data saved at:\n{encodings_path}\n\n"
                                 f"You can now use this student for exam monitoring!")
                    messagebox.showinfo("Success", success_msg)
                    self._close_registration_window()
                else:
                    print(f"   ❌ Failed to save to database")
                    messagebox.showerror("Error", "Failed to save student data to database!")
                    self._cancel_registration()
            else:
                print(f"   ❌ Failed to save face encodings")
                messagebox.showerror("Error", "Failed to save face encodings to file!")
                self._cancel_registration()
                
        except Exception as e:
            self.logger.error(f"Registration save error: {str(e)}")
            print(f"❌ Save error: {str(e)}")
            messagebox.showerror("Error", f"Failed to save registration data: {str(e)}")
            self._cancel_registration()
    
    def _cancel_registration(self):
        """Cancel the registration process"""
        print("\n⚠️ Registration cancelled")
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
