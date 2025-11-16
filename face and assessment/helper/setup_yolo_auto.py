"""
Automatic YOLO Setup Script - Downloads and configures YOLO for phone detection
"""

import os
import urllib.request
import sys
from config import Config

def download_file(url, destination):
    """Download a file with progress"""
    try:
        print(f"Downloading {os.path.basename(destination)}...")
        
        def reporthook(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size)
            sys.stdout.write(f"\r  Progress: {percent}%")
            sys.stdout.flush()
        
        urllib.request.urlretrieve(url, destination, reporthook)
        print("\n  ✓ Downloaded successfully!")
        return True
    except Exception as e:
        print(f"\n  ❌ Download failed: {str(e)}")
        return False

def setup_yolo():
    """Setup YOLO models for object detection"""
    print("="*60)
    print("YOLO Setup for Phone Detection")
    print("="*60)
    
    # Create models directory
    yolo_dir = os.path.join(Config.MODELS_DIR, "yolo")
    os.makedirs(yolo_dir, exist_ok=True)
    print(f"\n✓ Created directory: {yolo_dir}")
    
    # Files to download
    files = {
        "yolov3.cfg": "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg",
        "yolov3.weights": "https://pjreddie.com/media/files/yolov3.weights",
        "coco.names": "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names"
    }
    
    success_count = 0
    
    for filename, url in files.items():
        destination = os.path.join(yolo_dir, filename)
        
        # Check if file already exists
        if os.path.exists(destination):
            print(f"\n✓ {filename} already exists")
            success_count += 1
            continue
        
        print(f"\n📥 Downloading {filename}...")
        if download_file(url, destination):
            success_count += 1
    
    print("\n" + "="*60)
    if success_count == 3:
        print("✅ YOLO Setup Complete!")
        print("="*60)
        print("\nPhone detection is now enabled.")
        print("The system will detect mobile phones during exams.")
        return True
    else:
        print(f"⚠️ YOLO Setup Incomplete ({success_count}/3 files)")
        print("="*60)
        print("\nSome files failed to download.")
        print("Phone detection will not work.")
        return False

if __name__ == "__main__":
    try:
        setup_yolo()
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup error: {str(e)}")
