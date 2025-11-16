"""
Setup YOLOv4-Tiny for Phone Detection (More Compatible)
YOLOv4-tiny works better with newer OpenCV versions
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
            if total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                sys.stdout.write(f"\r  Progress: {percent}%")
                sys.stdout.flush()
        
        urllib.request.urlretrieve(url, destination, reporthook)
        print("\n  ✓ Downloaded successfully!")
        return True
    except Exception as e:
        print(f"\n  ❌ Download failed: {str(e)}")
        return False

def setup_yolo_v4():
    """Setup YOLOv4-tiny for object detection"""
    print("="*60)
    print("YOLOv4-Tiny Setup for Phone Detection")
    print("(More compatible with OpenCV 4.x)")
    print("="*60)
    
    # Create models directory
    yolo_dir = os.path.join(Config.MODELS_DIR, "yolo")
    os.makedirs(yolo_dir, exist_ok=True)
    print(f"\n✓ Created directory: {yolo_dir}")
    
    # Files to download - YOLOv4-tiny
    files = {
        "yolov4-tiny.cfg": "https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg",
        "yolov4-tiny.weights": "https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights",
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
        print("✅ YOLOv4-Tiny Setup Complete!")
        print("="*60)
        print("\nPhone detection is now enabled.")
        print("YOLOv4-tiny is faster and more compatible.")
        return True
    else:
        print(f"⚠️ YOLO Setup Incomplete ({success_count}/3 files)")
        print("="*60)
        return False

if __name__ == "__main__":
    try:
        setup_yolo_v4()
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup error: {str(e)}")
