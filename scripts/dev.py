#!/usr/bin/env python3
"""
Development helper script for YouTube Analyzer
Provides easy commands for development workflow
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DOCKER_DIR = PROJECT_ROOT / "docker"

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {cmd}")
            print(f"Error output: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception running command: {cmd}")
        print(f"Exception: {e}")
        return False

def dev_up(build=False):
    """Start development environment"""
    print("🚀 Starting development environment...")
    
    cmd = "docker-compose -f docker-compose.dev.yml up"
    if build:
        cmd += " --build"
    
    print(f"Running: {cmd}")
    os.system(f"cd {DOCKER_DIR} && {cmd}")

def dev_down():
    """Stop development environment"""
    print("🛑 Stopping development environment...")
    cmd = "docker-compose -f docker-compose.dev.yml down"
    print(f"Running: {cmd}")
    os.system(f"cd {DOCKER_DIR} && {cmd}")

def dev_build():
    """Build development image"""
    print("🔨 Building development image...")
    cmd = "docker-compose -f docker-compose.dev.yml build"
    print(f"Running: {cmd}")
    os.system(f"cd {DOCKER_DIR} && {cmd}")

def dev_rebuild():
    """Rebuild development image from scratch"""
    print("🔄 Rebuilding development image from scratch...")
    cmd = "docker-compose -f docker-compose.dev.yml build --no-cache"
    print(f"Running: {cmd}")
    os.system(f"cd {DOCKER_DIR} && {cmd}")

def dev_logs():
    """Show development logs"""
    print("📋 Showing development logs...")
    cmd = "docker-compose -f docker-compose.dev.yml logs -f"
    print(f"Running: {cmd}")
    os.system(f"cd {DOCKER_DIR} && {cmd}")

def dev_shell():
    """Open shell in development container"""
    print("🐚 Opening shell in development container...")
    cmd = "docker-compose -f docker-compose.dev.yml exec youtube-summarizer /bin/bash"
    print(f"Running: {cmd}")
    os.system(f"cd {DOCKER_DIR} && {cmd}")

def dev_status():
    """Show development container status"""
    print("📊 Development container status:")
    cmd = "docker-compose -f docker-compose.dev.yml ps"
    print(f"Running: {cmd}")
    os.system(f"cd {DOCKER_DIR} && {cmd}")

def dev_restart():
    """Restart development environment"""
    print("🔄 Restarting development environment...")
    dev_down()
    dev_up()

def requirements_changed():
    """Rebuild when requirements.txt changes"""
    print("📦 Requirements changed - rebuilding dependencies...")
    print("This will be faster than a full rebuild since only the dependency layer changes.")
    cmd = "docker-compose -f docker-compose.dev.yml build --no-cache youtube-summarizer"
    print(f"Running: {cmd}")
    os.system(f"cd {DOCKER_DIR} && {cmd}")
    print("✅ Dependencies rebuilt! Run 'python scripts/dev.py up' to start.")

def show_help():
    """Show help and usage examples"""
    print("""
🎯 YouTube Analyzer Development Helper

QUICK START:
  python scripts/dev.py up --build    # First time setup
  python scripts/dev.py up            # Start development (daily use)
  
COMMON COMMANDS:
  up [--build]     Start development environment
  down             Stop development environment
  build            Build development image
  rebuild          Rebuild from scratch (when requirements change)
  logs             Show container logs
  shell            Open shell in container
  status           Show container status
  restart          Restart the environment
  requirements     Rebuild after requirements.txt changes
  
DEVELOPMENT WORKFLOW:
  1. First time:       python scripts/dev.py up --build
  2. Daily coding:     python scripts/dev.py up
  3. Code changes:     Just save files - auto-reloads! 
  4. Requirements:     python scripts/dev.py requirements
  5. Full rebuild:     python scripts/dev.py rebuild
  
TIPS:
  • Code changes are instant - no rebuilding needed
  • Only rebuild when requirements.txt changes
  • Use 'logs' to debug issues
  • Use 'shell' to run commands inside container
""")

def main():
    parser = argparse.ArgumentParser(description="Development helper for YouTube Analyzer")
    parser.add_argument("command", nargs="?", default="help", 
                       choices=["up", "down", "build", "rebuild", "logs", "shell", 
                               "status", "restart", "requirements", "help"])
    parser.add_argument("--build", action="store_true", help="Build image when starting up")
    
    args = parser.parse_args()
    
    if args.command == "up":
        dev_up(build=args.build)
    elif args.command == "down":
        dev_down()
    elif args.command == "build":
        dev_build()
    elif args.command == "rebuild":
        dev_rebuild()
    elif args.command == "logs":
        dev_logs()
    elif args.command == "shell":
        dev_shell()
    elif args.command == "status":
        dev_status()
    elif args.command == "restart":
        dev_restart()
    elif args.command == "requirements":
        requirements_changed()
    elif args.command == "help":
        show_help()
    else:
        show_help()

if __name__ == "__main__":
    main()
