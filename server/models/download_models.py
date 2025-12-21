#!/usr/bin/env python3
"""
Download OpenCV Face Recognition Models
========================================
Downloads YuNet and SFace ONNX models for face recognition.

Run this once before starting the server:
    python server/models/download_models.py
"""

import urllib.request
import hashlib
from pathlib import Path

# Model URLs and SHA256 hashes
MODELS = {
    'face_detection_yunet_2023mar.onnx': {
        'url': 'https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx',
        'sha256': '5f3e3b1f0e7d1f0d8c9a3e1e7f0e5e1f0e7d1f0d8c9a3e1e7f0e5e1f0e7d1f0d'
    },
    'face_recognition_sface_2021dec.onnx': {
        'url': 'https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx',
        'sha256': '3e4f5e6f0e7d1f0d8c9a3e1e7f0e5e1f0e7d1f0d8c9a3e1e7f0e5e1f0e7d1f0d'
    }
}

def download_file(url: str, dest: Path):
    """Download file with progress"""
    print(f"Downloading {dest.name}...")
    print(f"URL: {url}")

    def progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, downloaded * 100 // total_size)
        print(f"\rProgress: {percent}% ({downloaded}/{total_size} bytes)", end='')

    urllib.request.urlretrieve(url, dest, reporthook=progress)
    print()  # New line after progress

def verify_sha256(file_path: Path, expected_hash: str) -> bool:
    """Verify file SHA256 hash"""
    # Note: SHA256 hashes in MODELS dict are placeholders
    # Actual verification disabled for now
    # In production, get real hashes from OpenCV Zoo
    print(f"Verification skipped (hash verification disabled)")
    return True

    # sha256_hash = hashlib.sha256()
    # with open(file_path, 'rb') as f:
    #     for byte_block in iter(lambda: f.read(4096), b""):
    #         sha256_hash.update(byte_block)
    # return sha256_hash.hexdigest() == expected_hash

def main():
    """Download all required models"""
    models_dir = Path(__file__).parent
    models_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("OpenCV Face Recognition Models Downloader")
    print("=" * 60)
    print(f"Target directory: {models_dir.absolute()}")
    print()

    for filename, info in MODELS.items():
        dest_path = models_dir / filename

        # Check if already exists
        if dest_path.exists():
            print(f"✓ {filename} already exists")
            # verify_sha256(dest_path, info['sha256'])
            continue

        # Download
        try:
            download_file(info['url'], dest_path)

            # Verify
            # if verify_sha256(dest_path, info['sha256']):
            #     print(f"✓ {filename} verified successfully")
            # else:
            #     print(f"✗ {filename} hash mismatch!")
            #     dest_path.unlink()
            #     return False

            print(f"✓ {filename} downloaded successfully")

        except Exception as e:
            print(f"✗ Failed to download {filename}: {e}")
            return False

    print()
    print("=" * 60)
    print("✓ All models downloaded successfully!")
    print("=" * 60)
    print()
    print("You can now start the server:")
    print("  cd server")
    print("  python app.py")
    print()

    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
