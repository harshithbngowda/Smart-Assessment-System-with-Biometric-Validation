"""
YOLO Model Setup Script
Downloads required YOLO model files for object detection
"""

import os
import urllib.request
import sys
from config import Config

def download_file(url, filename, description):
    """Download a file with progress indication"""
    print(f"Downloading {description}...")
    
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, (downloaded * 100) // total_size)
            sys.stdout.write(f"\r{description}: {percent}% ({downloaded}/{total_size} bytes)")
            sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, filename, progress_hook)
        print(f"\n✓ {description} downloaded successfully!")
        return True
    except Exception as e:
        print(f"\n✗ Error downloading {description}: {str(e)}")
        return False

def setup_yolo_models():
    """Download and setup YOLO model files"""
    print("Setting up YOLO models for object detection...")
    print("This will download approximately 250MB of data.\n")
    
    # Create directories
    Config.create_directories()
    yolo_dir = os.path.join(Config.MODELS_DIR, "yolo")
    os.makedirs(yolo_dir, exist_ok=True)
    
    # YOLO model URLs
    files_to_download = [
        {
            "url": "https://pjreddie.com/media/files/yolov3.weights",
            "filename": os.path.join(yolo_dir, "yolov3.weights"),
            "description": "YOLOv3 Weights (248MB)"
        },
        {
            "url": "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg",
            "filename": os.path.join(yolo_dir, "yolov3.cfg"),
            "description": "YOLOv3 Configuration"
        },
        {
            "url": "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names",
            "filename": os.path.join(yolo_dir, "coco.names"),
            "description": "COCO Class Names"
        }
    ]
    
    success_count = 0
    
    for file_info in files_to_download:
        # Check if file already exists
        if os.path.exists(file_info["filename"]):
            print(f"✓ {file_info['description']} already exists, skipping...")
            success_count += 1
            continue
        
        # Download the file
        if download_file(file_info["url"], file_info["filename"], file_info["description"]):
            success_count += 1
        else:
            print(f"Failed to download {file_info['description']}")
    
    print(f"\nSetup complete! {success_count}/{len(files_to_download)} files ready.")
    
    if success_count == len(files_to_download):
        print("✓ All YOLO model files are ready!")
        print("✓ Object detection (phone detection) will be enabled.")
    else:
        print("⚠ Some files failed to download.")
        print("⚠ Object detection will be disabled, but face recognition will still work.")
    
    print("\nYou can now run the main application with: python main.py")

def check_yolo_setup():
    """Check if YOLO models are properly set up"""
    yolo_files = [
        Config.YOLO_WEIGHTS_PATH,
        Config.YOLO_CONFIG_PATH,
        Config.YOLO_CLASSES_PATH
    ]
    
    all_exist = all(os.path.exists(f) for f in yolo_files)
    
    if all_exist:
        print("✓ YOLO models are properly set up!")
        return True
    else:
        print("✗ YOLO models are not set up.")
        missing_files = [f for f in yolo_files if not os.path.exists(f)]
        print("Missing files:")
        for f in missing_files:
            print(f"  - {f}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Biometric Assessment System - YOLO Setup")
    print("=" * 60)
    
    # Check current status
    if check_yolo_setup():
        response = input("\nYOLO models are already set up. Re-download? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            sys.exit(0)
    
    # Confirm download
    response = input("\nThis will download ~250MB of data. Continue? (Y/n): ")
    if response.lower() == 'n':
        print("Setup cancelled.")
        sys.exit(0)
    
    # Setup YOLO models
    setup_yolo_models()
    
    print("\n" + "=" * 60)
    print("Setup complete! You can now run: python main.py")
    print("=" * 60)
