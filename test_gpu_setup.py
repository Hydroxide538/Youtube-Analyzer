#!/usr/bin/env python3
"""
Test script to verify GPU setup for YouTube Analyzer
"""

import sys
import os
import logging

# Add the app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_pytorch_installation():
    """Test PyTorch installation and GPU detection"""
    print("=" * 60)
    print("Testing PyTorch Installation and GPU Detection")
    print("=" * 60)
    
    try:
        import torch
        print(f"✓ PyTorch version: {torch.__version__}")
        
        # Test CUDA availability
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            print(f"✓ CUDA available: {device_count} device(s)")
            
            for i in range(device_count):
                device_name = torch.cuda.get_device_name(i)
                memory_total = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                print(f"  - Device {i}: {device_name} ({memory_total:.1f} GB)")
        else:
            print("ℹ CUDA not available, will use CPU")
            
        return True
        
    except ImportError as e:
        print(f"✗ PyTorch not installed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing PyTorch: {e}")
        return False

def test_whisper_installation():
    """Test Whisper installation"""
    print("\n" + "=" * 60)
    print("Testing Whisper Installation")
    print("=" * 60)
    
    try:
        import whisper
        print("✓ Whisper installed successfully")
        
        # Test model loading
        print("Testing model loading...")
        model = whisper.load_model("tiny")  # Use tiny model for quick test
        print("✓ Whisper model loaded successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Whisper not installed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing Whisper: {e}")
        return False

def test_transcription_service():
    """Test the transcription service"""
    print("\n" + "=" * 60)
    print("Testing Transcription Service")
    print("=" * 60)
    
    try:
        from services.transcription_service import TranscriptionService
        
        # Create service instance
        service = TranscriptionService()
        print(f"✓ TranscriptionService initialized")
        print(f"  - Using device: {service.device}")
        print(f"  - Model loaded: {service.model}")
        
        return True
        
    except ImportError as e:
        print(f"✗ TranscriptionService import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing TranscriptionService: {e}")
        return False

def test_other_dependencies():
    """Test other required dependencies"""
    print("\n" + "=" * 60)
    print("Testing Other Dependencies")
    print("=" * 60)
    
    dependencies = [
        ('numpy', 'NumPy'),
        ('scipy', 'SciPy'),
        ('sklearn', 'Scikit-learn'),
        ('nltk', 'NLTK'),
        ('requests', 'Requests'),
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('ollama', 'Ollama'),
        ('pydantic', 'Pydantic'),
        ('websockets', 'WebSockets'),
        ('jinja2', 'Jinja2'),
        ('aiofiles', 'Aiofiles'),
        ('pydub', 'PyDub'),
        ('yt_dlp', 'YT-DLP')
    ]
    
    all_good = True
    
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - not installed")
            all_good = False
    
    return all_good

def main():
    """Main test function"""
    print("YouTube Analyzer GPU Setup Test")
    print("=" * 60)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run all tests
    tests = [
        test_pytorch_installation,
        test_whisper_installation,
        test_transcription_service,
        test_other_dependencies
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if all(results):
        print("✓ All tests passed! GPU setup is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
