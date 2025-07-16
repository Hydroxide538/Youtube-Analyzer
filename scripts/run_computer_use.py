#!/usr/bin/env python3
"""
Startup script for YouTube Analyzer with Computer Use capabilities.
This script manages the Docker containers for YouTube video analysis with bot detection evasion.
"""

import os
import sys
import subprocess
import time
import signal
import json
from pathlib import Path

def print_banner():
    """Print the application banner"""
    print("=" * 80)
    print("🤖 YouTube Analyzer with Computer Use")
    print("Bot Detection Evasion using Llama4 Vision Model")
    print("=" * 80)
    print()

def check_dependencies():
    """Check if required dependencies are installed"""
    required_commands = ['docker', 'docker-compose']
    missing = []
    
    for cmd in required_commands:
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(cmd)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Please install Docker and Docker Compose first.")
        return False
    
    print("✅ All dependencies found")
    return True

def get_project_root():
    """Get the project root directory"""
    return Path(__file__).parent.parent

def pull_ollama_models():
    """Pull required Ollama models"""
    print("📥 Pulling required Ollama models...")
    
    models = [
        "llama3.1:8b",
        "llama3.1:70b",  # For better performance if available
    ]
    
    for model in models:
        print(f"  Pulling {model}...")
        try:
            result = subprocess.run([
                'docker', 'exec', 'youtube-analyzer-ollama', 
                'ollama', 'pull', model
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"  ✅ {model} pulled successfully")
            else:
                print(f"  ⚠️  {model} pull failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"  ⏱️  {model} pull timed out")
        except Exception as e:
            print(f"  ❌ Error pulling {model}: {e}")

def start_services():
    """Start the Docker services"""
    print("🚀 Starting YouTube Analyzer with Computer Use...")
    
    project_root = get_project_root()
    compose_file = project_root / "docker" / "docker-compose.computer-use.yml"
    
    try:
        # Start services
        subprocess.run([
            'docker-compose', 
            '-f', str(compose_file), 
            'up', '-d'
        ], check=True, cwd=project_root)
        
        print("✅ Services started successfully!")
        
        # Wait for Ollama to be ready
        print("⏳ Waiting for Ollama service to be ready...")
        for i in range(30):
            try:
                result = subprocess.run([
                    'curl', '-s', 'http://localhost:11434/api/tags'
                ], capture_output=True, timeout=5)
                
                if result.returncode == 0:
                    print("✅ Ollama service is ready!")
                    break
            except:
                pass
            
            time.sleep(2)
            print(f"  Waiting... ({i+1}/30)")
        
        # Pull models after Ollama is ready
        pull_ollama_models()
        
        # Wait for main application to be ready
        print("⏳ Waiting for YouTube Analyzer to be ready...")
        for i in range(30):
            try:
                result = subprocess.run([
                    'curl', '-s', 'http://localhost:8000/health'
                ], capture_output=True, timeout=5)
                
                if result.returncode == 0:
                    print("✅ YouTube Analyzer is ready!")
                    break
            except:
                pass
            
            time.sleep(2)
            print(f"  Waiting... ({i+1}/30)")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start services: {e}")
        return False

def stop_services():
    """Stop the Docker services"""
    print("🛑 Stopping YouTube Analyzer services...")
    
    project_root = get_project_root()
    compose_file = project_root / "docker" / "docker-compose.computer-use.yml"
    
    try:
        subprocess.run([
            'docker-compose', 
            '-f', str(compose_file), 
            'down'
        ], check=True, cwd=project_root)
        
        print("✅ Services stopped successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to stop services: {e}")
        return False

def show_logs():
    """Show application logs"""
    project_root = get_project_root()
    compose_file = project_root / "docker" / "docker-compose.computer-use.yml"
    
    try:
        subprocess.run([
            'docker-compose', 
            '-f', str(compose_file), 
            'logs', '-f'
        ], cwd=project_root)
        
    except KeyboardInterrupt:
        print("\n📋 Log viewing stopped")

def show_status():
    """Show service status"""
    project_root = get_project_root()
    compose_file = project_root / "docker" / "docker-compose.computer-use.yml"
    
    try:
        subprocess.run([
            'docker-compose', 
            '-f', str(compose_file), 
            'ps'
        ], cwd=project_root)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get status: {e}")

def print_usage_info():
    """Print usage information"""
    print("\n" + "=" * 80)
    print("📖 Usage Information")
    print("=" * 80)
    print()
    print("🌐 Web Interface:")
    print("   http://localhost:8000")
    print()
    print("🔧 Ollama API:")
    print("   http://localhost:11434")
    print()
    print("📝 Features:")
    print("   • Traditional yt-dlp download with enhanced strategies")
    print("   • Computer use fallback for bot detection evasion")
    print("   • Llama4 vision model for browser automation")
    print("   • Human-like interaction patterns")
    print("   • CAPTCHA and verification handling")
    print()
    print("⚙️  Configuration:")
    print("   Computer use is enabled by default in this setup")
    print("   Models: llama3.1:8b (default), llama3.1:70b (if available)")
    print("   Max iterations: 20 per video")
    print("   Screenshot delay: 2.0 seconds")
    print("   Action delay: 1.0 seconds")
    print()
    print("🛠️  Troubleshooting:")
    print("   • Check logs: python scripts/run_computer_use.py logs")
    print("   • Check status: python scripts/run_computer_use.py status")
    print("   • If issues persist, try: python scripts/run_computer_use.py restart")
    print()

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print("\n\n🛑 Received interrupt signal. Stopping services...")
    stop_services()
    sys.exit(0)

def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print_banner()
    
    if len(sys.argv) < 2:
        command = "start"
    else:
        command = sys.argv[1].lower()
    
    if command == "start":
        if not check_dependencies():
            sys.exit(1)
        
        if start_services():
            print_usage_info()
            print("✅ YouTube Analyzer with Computer Use is running!")
            print("🌐 Open http://localhost:8000 in your browser")
            print()
            print("Press Ctrl+C to stop the services...")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            sys.exit(1)
    
    elif command == "stop":
        stop_services()
    
    elif command == "restart":
        stop_services()
        time.sleep(2)
        if start_services():
            print_usage_info()
            print("✅ YouTube Analyzer restarted successfully!")
        else:
            sys.exit(1)
    
    elif command == "logs":
        show_logs()
    
    elif command == "status":
        show_status()
    
    elif command == "help":
        print("Available commands:")
        print("  start    - Start the services (default)")
        print("  stop     - Stop the services")
        print("  restart  - Restart the services")
        print("  logs     - Show application logs")
        print("  status   - Show service status")
        print("  help     - Show this help message")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python scripts/run_computer_use.py help' for available commands")
        sys.exit(1)

if __name__ == "__main__":
    main()
