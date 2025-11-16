"""
Handwriting to Text Converter
Integrates with handwriting_to_text module
"""

import os
import sys
from pathlib import Path

# Add the handwriting_to_text directory to the path
current_dir = Path(__file__).parent
handwriting_dir = current_dir.parent / "handwriting_to_text"
sys.path.append(str(handwriting_dir))

try:
    # Set UTF-8 encoding for Windows
    import sys
    import os
    if sys.platform == "win32":
        os.environ["PYTHONIOENCODING"] = "utf-8"
    
    from recognize_gemini import convert_image_to_text_gemini
    print("✅ Handwriting recognition loaded successfully")
except Exception as e:
    print(f"⚠️ Warning: Handwriting recognition not available ({type(e).__name__}). Using fallback converter.")
    convert_image_to_text_gemini = None

def convert_image_to_text(image_path, api_key):
    """Convert handwriting image or PDF to text"""
    try:
        # Check if it's a PDF
        if image_path.lower().endswith('.pdf'):
            return convert_pdf_to_text(image_path, api_key)
        
        # Handle regular images
        if convert_image_to_text_gemini and api_key:
            # Use Gemini-based converter
            return convert_image_to_text_gemini(image_path, api_key)
        else:
            # Fallback to basic OCR or return placeholder
            return convert_image_fallback(image_path)
            
    except Exception as e:
        print(f"Error converting handwriting: {e}")
        return convert_image_fallback(image_path)

def convert_pdf_to_text(pdf_path, api_key):
    """Convert PDF with handwritten content to text"""
    print(f"🔍 Starting PDF conversion: {pdf_path}")
    print(f"🔑 API key available: {bool(api_key)}")
    
    try:
        import fitz  # PyMuPDF
        print("✅ PyMuPDF (fitz) imported successfully")
    except ImportError as e:
        print(f"❌ PyMuPDF not installed: {e}")
        print("💡 Install with: pip install PyMuPDF")
        return "PDF processing not available - PyMuPDF not installed"
    
    try:
        import tempfile
        import time
        from PIL import Image
        
        print(f"📄 Opening PDF: {pdf_path}")
        doc = fitz.open(pdf_path)
        print(f"📄 PDF has {len(doc)} pages")
        all_text = []
        temp_files = []  # Track temp files for cleanup
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            print(f"   Processing page {page_num + 1}/{len(doc)}...")
            
            # Convert page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
                pix.save(tmp_path)
                temp_files.append(tmp_path)
            
            # Important: Free the pixmap memory
            pix = None
            
            try:
                # Convert image to text using Gemini
                if convert_image_to_text_gemini and api_key:
                    print(f"   🤖 Using Gemini to extract text from page {page_num + 1}...")
                    page_text = convert_image_to_text_gemini(tmp_path, api_key)
                    print(f"   📝 Extracted {len(page_text) if page_text else 0} characters")
                    if page_text and not page_text.startswith("Error"):
                        all_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                        print(f"   ✅ Page {page_num + 1} processed successfully")
                    else:
                        print(f"   ⚠️ No valid text from page {page_num + 1}")
                else:
                    print(f"   ⚠️ Gemini not available, using fallback for page {page_num + 1}")
                    page_text = convert_image_fallback(tmp_path)
                    if page_text and not page_text.startswith("Error"):
                        all_text.append(page_text)
            except Exception as e:
                print(f"   ❌ Error processing page {page_num + 1}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Close document before cleanup
        doc.close()
        
        # Clean up temp files with retry logic
        for tmp_path in temp_files:
            for attempt in range(3):
                try:
                    time.sleep(0.1)  # Small delay
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    break
                except Exception as e:
                    if attempt == 2:  # Last attempt
                        print(f"   ⚠️ Could not delete temp file (will be cleaned by system): {tmp_path}")
                    else:
                        time.sleep(0.2)  # Wait longer before retry
        
        result = "\n\n".join(all_text)
        print(f"✅ Extracted {len(result)} characters from PDF")
        return result if result.strip() else "Could not extract text from PDF"
        
    except ImportError as e:
        print(f"❌ PyMuPDF not installed: {e}")
        print("💡 Install with: pip install PyMuPDF")
        return "PDF processing not available - PyMuPDF not installed"
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        return f"Error processing PDF: {str(e)}"

def convert_image_fallback(image_path):
    """Fallback handwriting conversion"""
    try:
        # Try to use basic OCR if available
        import cv2
        import pytesseract
        
        # Read image
        image = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Use tesseract for OCR
        text = pytesseract.image_to_string(thresh)
        
        return text.strip() if text.strip() else "Could not extract text from image"
        
    except ImportError:
        return "Handwriting conversion not available. Please install required dependencies."
    except Exception as e:
        return f"Error processing image: {str(e)}"

def preprocess_image(image_path):
    """Preprocess image for better text recognition"""
    try:
        import cv2
        import numpy as np
        
        # Read image
        image = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Save processed image
        processed_path = image_path.replace('.', '_processed.')
        cv2.imwrite(processed_path, cleaned)
        
        return processed_path
        
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return image_path