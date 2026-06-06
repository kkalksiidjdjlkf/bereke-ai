#!/usr/bin/env python3
"""
Quick Start Validation Script
Checks if all dependencies are installed and system is ready.
"""

import sys
import subprocess


def check_python_version():
    """Verify Python version >= 3.8."""
    print("✓ Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False


def check_imports():
    """Check if all required packages are installed."""
    print("\n✓ Checking dependencies...")
    
    packages = {
        'cv2': 'opencv-python',
        'mediapipe': 'mediapipe',
        'librosa': 'librosa',
        'numpy': 'numpy',
        'scipy': 'scipy',
    }
    
    all_installed = True
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} NOT installed")
            all_installed = False
    
    # Check PyAudio (optional)
    try:
        __import__('pyaudio')
        print(f"  ✅ pyaudio (audio support enabled)")
    except ImportError:
        print(f"  ⚠️  pyaudio NOT installed (audio disabled)")
    
    return all_installed


def check_camera():
    """Test if camera is accessible."""
    print("\n✓ Checking camera...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("  ✅ Camera accessible")
            cap.release()
            return True
        else:
            print("  ❌ Camera not accessible")
            return False
    except Exception as e:
        print(f"  ❌ Error checking camera: {e}")
        return False


def check_files():
    """Verify all project files exist."""
    print("\n✓ Checking project files...")
    
    required_files = [
        'main.py',
        'config.py',
        'face_analyzer.py',
        'voice_analyzer.py',
        'breathing_analyzer.py',
        'wellbeing_monitor.py',
        'examples.py',
        'README.md',
        'requirements.txt',
    ]
    
    import os
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} NOT found")
            all_exist = False
    
    return all_exist


def main():
    """Run all checks."""
    print("""
╔════════════════════════════════════════════════════════════╗
║      WELLBEING MONITORING SYSTEM - SETUP VALIDATOR       ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    results = {
        'Python Version': check_python_version(),
        'Dependencies': check_imports(),
        'Camera': check_camera(),
        'Project Files': check_files(),
    }
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    
    all_passed = True
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check:20} {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 System is ready!")
        print("\nNext steps:")
        print("  1. Install missing packages (if any):")
        print("     pip install -r requirements.txt")
        print("\n  2. Start monitoring:")
        print("     python main.py")
        print("\n  3. Run examples:")
        print("     python examples.py")
        return 0
    else:
        print("\n⚠️  System needs fixes:")
        print("\n  Run this to install dependencies:")
        print("     pip install -r requirements.txt")
        
        if not results['Camera']:
            print("\n  Camera setup:")
            print("     - Check camera connection")
            print("     - Try: python -c 'import cv2; print(cv2.VideoCapture(0).isOpened())'")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
