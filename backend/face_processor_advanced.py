"""
Advanced Face Processing Module
Integrates the facial registration system from face and assessment/main.py
with ArcFace recognition and image augmentation
"""

import cv2
import numpy as np
import pickle
import os
import sys
import logging
from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path

# Try to import the advanced face recognition modules
try:
    # Add the face and assessment directory to the path
    current_dir = Path(__file__).parent
    face_assessment_dir = current_dir.parent / "face and assessment"
    sys.path.append(str(face_assessment_dir))

    # Import Config for YOLO paths and thresholds
    from config import Config

    from arcface_recognition import face_locations, face_encodings, compare_faces, face_distance
    ADVANCED_FACE_RECOGNITION = True
    print("Using advanced face recognition (ArcFace) with multi-photo capture and augmentation")
except (ImportError, RuntimeError) as e:
    print(f"Advanced face recognition not available: {e}")
    ADVANCED_FACE_RECOGNITION = False
    Config = None
    # Fallback to simple face detection
    from face_processor_simple import verify_face as simple_verify_face, save_face_encoding as simple_save_face_encoding

# ==================== YOLO (Phone Detection) ====================
# Lazy-loaded global state
YOLO_NET = None
YOLO_OUTPUT_LAYERS = None
YOLO_CLASSES = []
PHONE_CLASS_IDS = set()

def _init_yolo_if_needed():
    """Initialize YOLOv4-tiny for phone detection if available.
    Uses paths from face and assessment/config.py (Config), with graceful fallback."""
    global YOLO_NET, YOLO_OUTPUT_LAYERS, YOLO_CLASSES, PHONE_CLASS_IDS
    if YOLO_NET is not None:
        return
    try:
        if Config is None:
            # Config not available; cannot locate model files
            return

        import os
        # Resolve paths
        yolo_cfg = getattr(Config, 'YOLO_CONFIG_PATH', '')
        yolo_weights = getattr(Config, 'YOLO_WEIGHTS_PATH', '')
        yolo_classes = getattr(Config, 'YOLO_CLASSES_PATH', '')

        if not (os.path.exists(yolo_cfg) and os.path.exists(yolo_weights) and os.path.exists(yolo_classes)):
            # Try to auto-resolve inside models/yolo directory
            base_dir = os.path.dirname(yolo_cfg) if yolo_cfg else ''
            try:
                cand = os.listdir(base_dir) if base_dir and os.path.isdir(base_dir) else []
            except Exception:
                cand = []
            cfg = next((os.path.join(base_dir, f) for f in cand if f.lower().endswith('.cfg') and 'yolov4-tiny' in f.lower()), None)
            if not cfg:
                cfg = next((os.path.join(base_dir, f) for f in cand if f.lower().endswith('.cfg')), None)
            weights = next((os.path.join(base_dir, f) for f in cand if f.lower().endswith('.weights') and 'yolov4-tiny' in f.lower()), None)
            if not weights:
                weights = next((os.path.join(base_dir, f) for f in cand if f.lower().endswith('.weights')), None)
            classes_path = yolo_classes if os.path.exists(yolo_classes) else next((os.path.join(base_dir, f) for f in cand if f.lower().endswith('.names') or f.lower().endswith('coco.names')), None)
            yolo_cfg = cfg or yolo_cfg
            yolo_weights = weights or yolo_weights
            yolo_classes = classes_path or yolo_classes

        if not (yolo_cfg and yolo_weights and yolo_classes and os.path.exists(yolo_cfg) and os.path.exists(yolo_weights) and os.path.exists(yolo_classes)):
            print("[YOLO] Model files not found. Phone detection disabled.")
            return

        # Load network
        YOLO_NET = cv2.dnn.readNet(yolo_weights, yolo_cfg)
        layer_names = YOLO_NET.getLayerNames()
        uol = YOLO_NET.getUnconnectedOutLayers()
        try:
            YOLO_OUTPUT_LAYERS = [layer_names[int(i[0]) - 1] for i in uol]
        except Exception:
            YOLO_OUTPUT_LAYERS = [layer_names[int(i) - 1] for i in uol]

        # Load classes
        with open(yolo_classes, 'r') as f:
            YOLO_CLASSES = [line.strip() for line in f.readlines()]

        # Resolve phone class IDs dynamically
        phone_names = {"cell phone", "cellphone", "mobile phone", "phone"}
        dyn_ids = [i for i, n in enumerate(YOLO_CLASSES) if n.lower() in phone_names]
        if dyn_ids:
            PHONE_CLASS_IDS = set(dyn_ids)
        else:
            PHONE_CLASS_IDS = set(getattr(Config, 'PHONE_CLASS_IDS', [67]))

        print(f"[YOLO] Loaded. Phone classes: {[YOLO_CLASSES[i] for i in PHONE_CLASS_IDS]} at ids {sorted(PHONE_CLASS_IDS)}")
    except Exception as e:
        print(f"[YOLO] Initialization error: {e}")
        YOLO_NET = None
        YOLO_OUTPUT_LAYERS = None
        YOLO_CLASSES = []
        PHONE_CLASS_IDS = set()

def create_augmented_photos(base_image, num_photos=15):
    """Create augmented versions of the base image for better recognition"""
    try:
        augmented_photos = []
        
        # Validate input
        if base_image is None or not isinstance(base_image, np.ndarray):
            logging.error("create_augmented_photos: base_image is None or not ndarray")
            return []
        if base_image.ndim < 2:
            logging.error("create_augmented_photos: base_image has invalid shape")
            return []
        
        # Convert to PIL for easier manipulation (guarded)
        try:
            rgb_image = cv2.cvtColor(base_image, cv2.COLOR_BGR2RGB)
        except Exception as e:
            logging.warning(f"create_augmented_photos: cvtColor failed: {e}")
            rgb_image = base_image
        try:
            pil_image = Image.fromarray(rgb_image)
        except Exception as e:
            logging.error(f"create_augmented_photos: PIL conversion failed: {e}")
            return []
        
        # Original photo
        augmented_photos.append(base_image)
        
        # Brightness variations
        for brightness_factor in [0.7, 0.8, 0.9, 1.1, 1.2, 1.3]:
            try:
                enhancer = ImageEnhance.Brightness(pil_image)
                bright_image = enhancer.enhance(brightness_factor)
                arr = np.array(bright_image)
                if arr is not None and arr.size > 0:
                    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                    augmented_photos.append(bgr)
            except:
                pass
        
        # Contrast variations
        for contrast_factor in [0.8, 0.9, 1.1, 1.2]:
            try:
                enhancer = ImageEnhance.Contrast(pil_image)
                contrast_image = enhancer.enhance(contrast_factor)
                arr = np.array(contrast_image)
                if arr is not None and arr.size > 0:
                    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                    augmented_photos.append(bgr)
            except:
                pass
        
        # Sharpness variations
        for sharpness_factor in [0.7, 1.3]:
            try:
                enhancer = ImageEnhance.Sharpness(pil_image)
                sharp_image = enhancer.enhance(sharpness_factor)
                arr = np.array(sharp_image)
                if arr is not None and arr.size > 0:
                    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                    augmented_photos.append(bgr)
            except:
                pass
        
        # Blur variations (subtle)
        for blur_radius in [0.2, 0.5]:
            try:
                blurred = pil_image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                arr = np.array(blurred)
                if arr is not None and arr.size > 0:
                    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                    augmented_photos.append(bgr)
            except:
                pass
        
        # Return up to the requested number
        return augmented_photos[:num_photos]
        
    except Exception as e:
        logging.error(f"Error creating augmented photos: {e}")
        return [base_image]  # Return at least original

def save_face_encoding(user, image_data):
    """Save face encoding for a user using advanced multi-photo capture and augmentation.
    Accepts a single base64 string/ndarray OR a list of base64 strings/ndarrays.
    """
    print(f"[FACE] save_face_encoding called. image_data type: {type(image_data)}, is list: {isinstance(image_data, list)}")
    try:
        # Always use advanced processing (works with both single images and lists)
        print("[FACE] Using advanced face recognition")
        # if not ADVANCED_FACE_RECOGNITION:
        #     print("[FACE] Using simple face recognition fallback")
        #     return simple_save_face_encoding(user, image_data)
        # Convert image data to OpenCV format
        import base64
        from io import BytesIO
        
        images_to_process = []
        skip_augmentation = False  # If we have raw frames, skip PIL augmentation
        
        if isinstance(image_data, list):
            # List of frames that can be base64 strings OR numpy arrays
            print(f"[FACE] Processing list of {len(image_data)} items")
            for idx, item in enumerate(image_data):
                try:
                    if isinstance(item, np.ndarray):
                        skip_augmentation = True  # Raw frames; use directly
                        if item is not None:
                            images_to_process.append(item)
                        print(f"[FACE] Frame {idx}: Added numpy array")
                        continue
                    # else assume base64 string
                    if not isinstance(item, str):
                        print(f"[FACE] Frame {idx}: Not a string or ndarray, skipping. Type: {type(item)}")
                        continue
                    img_clean = item.split(',')[1] if ',' in item else item
                    image_bytes = base64.b64decode(img_clean)
                    nparr = np.frombuffer(image_bytes, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is not None:
                        images_to_process.append(img)
                        print(f"[FACE] Frame {idx}: Decoded OK, shape: {img.shape}")
                    else:
                        print(f"[FACE] Frame {idx}: cv2.imdecode returned None")
                except Exception as e:
                    print(f"[FACE] Frame {idx}: Exception: {e}")
                    continue
            # Always skip augmentation when client provides multiple frames for speed
            skip_augmentation = True
        elif isinstance(image_data, str):
            # Single base64 string
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                images_to_process.append(img)
        elif isinstance(image_data, np.ndarray):
            skip_augmentation = True
            images_to_process.append(image_data)
        else:
            return False, "Invalid image format"

        if not images_to_process:
            return False, "No valid images provided"

        # If we have raw frames, use them directly; otherwise augment
        if skip_augmentation:
            augmented_images = images_to_process  # Use raw frames as-is
        else:
            augmented_images = []
            for base_img in images_to_process:
                augmented_images.extend(create_augmented_photos(base_img, num_photos=15))
        
        if not augmented_images:
            return False, "Could not create photo variations"
        
        all_encodings = []
        processed_count = 0
        print(f"[FACE] Processing {len(augmented_images)} images for face detection/encoding")
        
        # Cap total processed images to avoid long CPU loops
        max_process = min(len(augmented_images), 60)
        for idx, aug_image in enumerate(augmented_images[:max_process]):
            try:
                if ADVANCED_FACE_RECOGNITION:
                    # Prefer ArcFace embeddings for robustness to pose/lighting
                    locs = face_locations(aug_image)
                    if not locs:
                        continue
                    # Use the largest face if multiple
                    if len(locs) > 1:
                        # face_locations typically returns (top, right, bottom, left)
                        def area(box):
                            t, r, b, l = box
                            return max(0, b - t) * max(0, r - l)
                        locs = sorted(locs, key=area, reverse=True)
                        locs = [locs[0]]
                    encs = face_encodings(aug_image, locs)
                    if not encs:
                        continue
                    enc = encs[0]
                    # Normalize embedding for cosine
                    norm = np.linalg.norm(enc)
                    if norm == 0 or np.isnan(norm):
                        continue
                    enc = enc / norm
                    all_encodings.append(enc.astype(np.float32))
                    processed_count += 1
                else:
                    # Fallback: Haar + grayscale template (less robust)
                    rgb_image = cv2.cvtColor(aug_image, cv2.COLOR_BGR2RGB)
                    gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30))
                    if len(faces) == 0:
                        continue
                    if len(faces) > 1:
                        faces = sorted(faces, key=lambda face: face[2] * face[3], reverse=True)
                    (x, y, w, h) = faces[0]
                    face_region = gray[y:y+h, x:x+w]
                    face_region = cv2.resize(face_region, (100, 100))
                    encoding = face_region.flatten().astype(np.float32)
                    # Normalize grayscale vector to reduce brightness impact
                    m, s = float(np.mean(encoding)), float(np.std(encoding))
                    if s < 1e-6:
                        continue
                    encoding = (encoding - m) / s
                    all_encodings.append(encoding)
                    processed_count += 1
            except Exception as e:
                print(f"[FACE] Error processing image {idx}: {e}")
                continue
        
        print(f"[FACE] Processed {processed_count} images successfully, {len(all_encodings)} encodings extracted")
        
        if len(all_encodings) == 0:
            return False, "Could not extract face features. Please ensure your face is clearly visible."
        
        if processed_count < 8:
            return False, f"Only {processed_count} valid photos captured. Please try again with better lighting and ensure multiple angles."
        
        # Save face encodings
        user.face_encoding = pickle.dumps(all_encodings)
        user.face_registered_at = datetime.utcnow()
        print(f"[FACE] Face registration successful! Saved {len(all_encodings)} encodings")
        
        return True, f"Face registered successfully with {len(all_encodings)} encodings from {processed_count} photos"
        
    except Exception as e:
        logging.error(f"Error in advanced face encoding: {e}")
        return False, f"Error processing face: {str(e)}"

def verify_face(user, image, tolerance=0.80):
    """Verify if the face matches the registered user using OpenCV Haar Cascade"""
    try:
        print(f"[FACE VERIFY] Starting verification for user {user.id}")
        
        # Always use OpenCV approach (consistent with registration)
        if not user.face_encoding:
            print(f"[FACE VERIFY] User has no face encoding")
            return False, 0.0
        
        # Convert image data if needed
        import base64
        from io import BytesIO
        
        if isinstance(image, str):
            print(f"[FACE VERIFY] Image is string, decoding...")
            if ',' in image:
                image = image.split(',')[1]
            image_bytes = base64.b64decode(image)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            print(f"[FACE VERIFY] Image is None after decoding")
            return False, 0.0
        
        print(f"[FACE VERIFY] Image shape: {image.shape}")
        
        # Extract embedding
        current_encoding = None
        if ADVANCED_FACE_RECOGNITION:
            locs = face_locations(image)
            print(f"[FACE VERIFY] Detected {len(locs)} faces (ArcFace)")
            if not locs:
                print(f"[FACE VERIFY] No faces detected")
                return False, 0.0
            if len(locs) > 1:
                def area(box):
                    t, r, b, l = box
                    return max(0, b - t) * max(0, r - l)
                locs = sorted(locs, key=area, reverse=True)
                locs = [locs[0]]
            encs = face_encodings(image, locs)
            if not encs:
                print(f"[FACE VERIFY] No embeddings produced")
                return False, 0.0
            current_encoding = encs[0]
            norm = np.linalg.norm(current_encoding)
            if norm == 0 or np.isnan(norm):
                print(f"[FACE VERIFY] Invalid embedding norm")
                return False, 0.0
            current_encoding = (current_encoding / norm).astype(np.float32)
        else:
            # Fallback Haar template
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30))
            print(f"[FACE VERIFY] Detected {len(faces)} faces")
            if len(faces) == 0:
                print(f"[FACE VERIFY] No faces detected")
                return False, 0.0
            if len(faces) > 1:
                faces = sorted(faces, key=lambda face: face[2] * face[3], reverse=True)
                print(f"[FACE VERIFY] Using largest face out of {len(faces)}")
            (x, y, w, h) = faces[0]
            face_region = gray[y:y+h, x:x+w]
            face_region = cv2.resize(face_region, (100, 100))
            current_encoding = face_region.flatten().astype(np.float32)
            m, s = float(np.mean(current_encoding)), float(np.std(current_encoding))
            if s < 1e-6:
                return False, 0.0
            current_encoding = (current_encoding - m) / s
        
        print(f"[FACE VERIFY] Extracted face encoding, length: {len(current_encoding)}")
        
        # Load stored face encodings
        stored_encodings = pickle.loads(user.face_encoding)
        print(f"[FACE VERIFY] Loaded {len(stored_encodings)} stored encodings")
        # Filter to only those matching current embedding dimensionality (after flatten)
        try:
            target_size = int(np.asarray(current_encoding).size)
            filtered_encs = []
            for se in stored_encodings:
                try:
                    arr = np.asarray(se)
                    if arr is None:
                        continue
                    arr = arr.astype(np.float32, copy=False)
                    arr = arr.reshape(-1)
                    if int(arr.size) == target_size:
                        filtered_encs.append(arr)
                except Exception:
                    continue
            if not filtered_encs:
                print("[FACE VERIFY] No stored encodings match current dimensionality; returning NO MATCH")
                return False, 0.0
            stored_encodings = filtered_encs
        except Exception:
            pass
        
        # Compare using cosine similarity if embeddings, else correlation
        similarities = []
        # Cap comparisons for speed
        compare_list = stored_encodings[:200]
        for idx, stored_encoding in enumerate(compare_list):
            try:
                a = np.asarray(stored_encoding, dtype=np.float32).reshape(-1)
                b = np.asarray(current_encoding, dtype=np.float32).reshape(-1)
                if a.size == b.size and a.ndim == 1 and a.size >= 128:
                    # Assume embeddings: use cosine
                    denom = (np.linalg.norm(a) * np.linalg.norm(b))
                    if denom == 0 or np.isnan(denom):
                        continue
                    sim = float(np.dot(a, b) / denom)
                    similarities.append(sim)
                else:
                    # Fallback: correlation
                    sim = float(np.corrcoef(a, b)[0, 1])
                    if not np.isnan(sim):
                        similarities.append(sim)
            except Exception:
                continue
        
        print(f"[FACE VERIFY] Computed {len(similarities)} valid similarities")
        
        if not similarities:
            print(f"[FACE VERIFY] No valid similarities computed")
            return False, 0.0
        
        # Robust aggregation to avoid spurious spikes
        similarities.sort(reverse=True)
        top_k = similarities[:7]
        if len(top_k) >= 3:
            agg = float(np.median(top_k))
        else:
            agg = float(np.mean(top_k))
        # Convert to 0-1 scale from [-1,1]
        confidence = (agg + 1.0) / 2.0
        
        print(f"[FACE VERIFY] Best confidence: {confidence:.4f}, tolerance: {tolerance}")
        
        # Check if it matches based on tolerance
        matches = confidence > tolerance
        print(f"[FACE VERIFY] Result: {'MATCH' if matches else 'NO MATCH'}")
        return matches, float(confidence)
            
    except Exception as e:
        print(f"[FACE VERIFY] Exception: {e}")
        import traceback
        traceback.print_exc()
        logging.error(f"Error in face verification: {e}")
        return False, 0.0

def detect_multiple_faces(image):
    """Detect if multiple faces are present in the image"""
    try:
        if not ADVANCED_FACE_RECOGNITION:
            # Fallback to simple detection
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            return len(faces) > 1, len(faces)
        
        # Use ArcFace detection
        face_locs = face_locations(image)
        return len(face_locs) > 1, len(face_locs)
        
    except Exception as e:
        logging.error(f"Error detecting multiple faces: {e}")
        return False, 0

def detect_phone_usage(image):
    """Detect if a phone is being used. Prefer YOLOv4-tiny via OpenCV DNN; fall back to simple heuristic."""
    try:
        _init_yolo_if_needed()

        if YOLO_NET is not None and YOLO_OUTPUT_LAYERS is not None and (PHONE_CLASS_IDS or True):
            # YOLO-based detection
            try:
                h, w = image.shape[:2]
                cfg_inp = int(getattr(Config, 'YOLO_INPUT_SIZE', 416)) if Config else 416
                # Use 416 by default for better accuracy; allow 320–608 via Config
                inp = max(320, min(608, cfg_inp))
                blob = cv2.dnn.blobFromImage(image, 1/255.0, (inp, inp), (0, 0, 0), swapRB=True, crop=False)
                YOLO_NET.setInput(blob)
                outputs = YOLO_NET.forward(YOLO_OUTPUT_LAYERS)

                boxes, confidences, class_ids = [], [], []
                thresh = float(getattr(Config, 'PHONE_DETECTION_CONFIDENCE', 0.4)) if Config else 0.4

                for output in outputs:
                    for detection in output:
                        scores = detection[5:]
                        class_id = int(np.argmax(scores))
                        confidence = float(scores[class_id])
                        if confidence > thresh:
                            cx, cy, bw, bh = detection[0:4]
                            center_x = int(cx * w)
                            center_y = int(cy * h)
                            width = int(bw * w)
                            height = int(bh * h)
                            x = int(center_x - width / 2)
                            y = int(center_y - height / 2)
                            boxes.append([x, y, width, height])
                            confidences.append(confidence)
                            class_ids.append(class_id)

                # NMS
                idxs = cv2.dnn.NMSBoxes(boxes, confidences, thresh, 0.4)
                if isinstance(idxs, (list, tuple)):
                    keep = list(idxs)
                elif hasattr(idxs, 'flatten'):
                    keep = idxs.flatten().tolist()
                else:
                    keep = []

                # Filter phone classes
                hits = []
                phone_ids = PHONE_CLASS_IDS if PHONE_CLASS_IDS else set([67])
                for i in keep:
                    try:
                        i0 = int(i)
                        if class_ids[i0] in phone_ids:
                            hits.append(i0)
                    except Exception:
                        continue

                return (len(hits) > 0), len(hits)
            except Exception as e:
                logging.warning(f"YOLO detection failed, falling back. Error: {e}")

        # Disable heuristic fallback to avoid false positives in exams
        return False, 0

    except Exception as e:
        logging.error(f"Error detecting phone usage: {e}")
        return False, 0

def monitor_cheating_attempts(image, user):
    """Monitor for various cheating attempts"""
    results = {
        'face_verified': False,
        'face_confidence': 0.0,
        'multiple_faces': False,
        'face_count': 0,
        'phone_detected': False,
        'phone_count': 0,
        'overall_status': 'safe'
    }
    
    try:
        print(f"[MONITOR CHEATING] Starting monitoring for user {user.id}")
        
        # Face verification with aligned tolerance
        face_verified, confidence = verify_face(user, image, tolerance=0.80)
        results['face_verified'] = bool(face_verified)
        results['face_confidence'] = float(confidence * 100)  # Convert to percentage
        
        print(f"[MONITOR CHEATING] Face verified: {face_verified}, confidence: {confidence}")
        
        # Multiple face detection
        multiple_faces, face_count = detect_multiple_faces(image)
        results['multiple_faces'] = bool(multiple_faces)
        results['face_count'] = int(face_count)
        
        print(f"[MONITOR CHEATING] Multiple faces: {multiple_faces}, count: {face_count}")
        
        # Phone detection
        phone_detected, phone_count = detect_phone_usage(image)
        results['phone_detected'] = bool(phone_detected)
        results['phone_count'] = int(phone_count)
        
        print(f"[MONITOR CHEATING] Phone detected: {phone_detected}, count: {phone_count}")
        
        # Determine overall status
        # Treat as mismatch only if both failed AND confidence is low
        if (not face_verified) and (confidence < 0.80):
            results['overall_status'] = 'face_mismatch'
        elif multiple_faces:
            results['overall_status'] = 'multiple_faces'
        elif phone_detected:
            results['overall_status'] = 'phone_detected'
        else:
            results['overall_status'] = 'safe'
        
        print(f"[MONITOR CHEATING] Overall status: {results['overall_status']}")
        
        return results
        
    except Exception as e:
        print(f"[MONITOR CHEATING] Exception: {e}")
        import traceback
        traceback.print_exc()
        logging.error(f"Error monitoring cheating attempts: {e}")
        results['overall_status'] = 'error'
        results['error_message'] = str(e)
        return results
