#!/usr/bin/env python3
"""
Startup script for YouTube Video Summarizer
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found. Please install FFmpeg:")
        print("   - Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("   - macOS: brew install ffmpeg")
        print("   - Windows: Download from https://ffmpeg.org/download.html")
        return False

def check_ollama():
    """Check if Ollama is running and has the required model"""
    try:
        # Check if Ollama is running
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            
            # Check if llama3.1 model is available
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            if any('llama3.1' in name for name in model_names):
                print("✅ Llama 3.1 model is available")
                return True
            else:
                print("⚠️  Llama 3.1 model not found")
                print("   Run: ollama pull llama3.1:8b")
                return False
        else:
            print("❌ Ollama is not responding")
            return False
            
    except requests.exceptions.RequestException:
        print("❌ Ollama is not running")
        print("   Start Ollama: ollama serve")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['temp', 'logs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Directories created")

def start_application():
    """Start the FastAPI application"""
    print("🚀 Starting YouTube Video Summarizer...")
    print("   Access the application at: http://localhost:8000")
    print("   Press Ctrl+C to stop")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'app.main:app', 
            '--host', '0.0.0.0', 
            '--port', '8000', 
            '--reload'
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped")

def main():
    """Main startup function"""
    print("🎬 YouTube Video Summarizer - Startup Script")
    print("=" * 50)
    
    # Check system requirements
    check_python_version()
    
    if not check_ffmpeg():
        sys.exit(1)
    
    if not check_ollama():
        print("\n⚠️  Ollama setup required. Please:")
        print("1. Start Ollama: ollama serve")
        print("2. Pull model: ollama pull llama3.1:8b")
        print("3. Run this script again")
        sys.exit(1)
    
    # Setup application
    create_directories()
    
    if not install_dependencies():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ All checks passed! Starting application...")
    print("=" * 50)
    
    # Start the application
    start_application()

if __name__ == "__main__":
    main()
