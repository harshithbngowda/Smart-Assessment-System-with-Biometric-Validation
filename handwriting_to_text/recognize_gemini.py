"""
Handwriting Recognition using Google Gemini Vision API
Fast, accurate, and easy to use
"""

from __future__ import annotations
import google.generativeai as genai
from PIL import Image
from pathlib import Path
import sys
import os


def recognize_with_gemini(
    image_path: str,
    api_key: str = None,
    output_path: str = None,
    prompt: str = None
) -> str:
    """
    Recognize handwritten text using Google Gemini Vision.
    
    Args:
        image_path: Path to handwriting image
        api_key: Google Gemini API key (or set GEMINI_API_KEY env variable)
        output_path: Optional path to save output
        prompt: Custom prompt (default: extract handwriting)
    
    Returns:
        Recognized text
    """
    print("="*70)
    print("HANDWRITING RECOGNITION - Google Gemini Vision")
    print("="*70)
    
    # Get API key
    if api_key is None:
        api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        print("\n❌ No API key found!")
        print("\n🔑 Get your FREE API key:")
        print("   1. Go to: https://makersuite.google.com/app/apikey")
        print("   2. Click 'Create API Key'")
        print("   3. Copy the key")
        print("\n💡 Then run:")
        print("   python recognize_gemini.py <image_path> <your_api_key>")
        print("\n   Or set environment variable:")
        print("   set GEMINI_API_KEY=your_api_key_here")
        return ""
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    # Use gemini-2.5-flash (fast and supports vision/images)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Load image
    print(f"\nInput: {image_path}")
    image = Image.open(image_path)
    
    # Default prompt for handwriting recognition
    if prompt is None:
        prompt = """
        Please read all the handwritten text in this image and transcribe it exactly as written.
        
        Rules:
        - Transcribe ALL text you see
        - Preserve the original line breaks
        - Keep punctuation and spacing
        - If text is unclear, make your best guess
        - Output ONLY the transcribed text, no explanations
        """
    
    # Generate response
    print("\n🤖 Processing with Gemini...")
    response = model.generate_content([prompt, image])
    
    # Extract text
    text = response.text.strip()
    
    # Display result
    print("\n" + "="*70)
    print("RECOGNIZED TEXT:")
    print("="*70)
    print(text)
    print("="*70)
    
    # Save output
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"\n✅ Saved to: {output_path}")
    
    return text


# Backwards-compatible wrapper expected by backend/handwriting_converter.py
def convert_image_to_text_gemini(image_path: str, api_key: str | None = None) -> str:
    """Return plain text transcription from an image using Gemini Vision."""
    try:
        result = recognize_with_gemini(image_path=image_path, api_key=api_key)
        # Filter out any error messages that might have been included
        if result and not result.startswith("Error") and not result.startswith("❌"):
            return result
        return ""
    except Exception as e:
        print(f"Error in Gemini conversion: {e}")
        return ""


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║        Handwriting Recognition with Google Gemini Vision         ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) < 2:
        print("Usage: python recognize_gemini.py <image_path> [api_key] [output_path]")
        print("\nExample:")
        print("   python recognize_gemini.py input/image-12.jpg YOUR_API_KEY")
        print("   python recognize_gemini.py input/image-12.jpg YOUR_API_KEY output/result.txt")
        print("\n🔑 Get FREE API key: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    image_path = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    recognize_with_gemini(
        image_path=image_path,
        api_key=api_key,
        output_path=output_path
    )
