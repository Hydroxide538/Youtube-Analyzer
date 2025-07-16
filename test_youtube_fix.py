#!/usr/bin/env python3
"""
Test script to verify the YouTube download fix.
This script tests the enhanced yt-dlp fallback with multiple retry strategies.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.computer_use_service import ComputerUseService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_youtube_download():
    """Test YouTube download with the enhanced fallback method"""
    
    # Test URLs (use short, publicly available videos)
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll - short, always available
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo - first YouTube video
        "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Gangnam Style - very popular
    ]
    
    print("🧪 Testing YouTube Download Fix")
    print("=" * 50)
    
    computer_use = ComputerUseService()
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📹 Test {i}: {url}")
        print("-" * 40)
        
        try:
            # Test the fallback download directly
            result = await computer_use._fallback_download(url)
            
            if result.get("success"):
                print(f"✅ SUCCESS: {result.get('message')}")
                print(f"   Strategy used: {result.get('strategy_used', 'unknown')}")
                print(f"   Attempt: {result.get('attempt', 'unknown')}")
                
                # Check if audio file exists
                audio_path = result.get("audio_path")
                if audio_path and os.path.exists(audio_path):
                    file_size = os.path.getsize(audio_path)
                    print(f"   Audio file: {audio_path}")
                    print(f"   File size: {file_size:,} bytes")
                    
                    # Clean up test file
                    try:
                        os.remove(audio_path)
                        print("   ✅ Test file cleaned up")
                    except Exception as cleanup_error:
                        print(f"   ⚠️ Cleanup warning: {cleanup_error}")
                else:
                    print(f"   ⚠️ Warning: Audio file not found at {audio_path}")
                    
            else:
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            logger.error(f"Test failed with exception: {str(e)}")
        
        # Small delay between tests
        await asyncio.sleep(2)
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

async def test_single_url():
    """Test a single URL provided by user"""
    
    if len(sys.argv) < 2:
        print("Usage: python test_youtube_fix.py [URL]")
        print("Or run without arguments to test default URLs")
        return
    
    url = sys.argv[1]
    print(f"🧪 Testing single URL: {url}")
    print("=" * 50)
    
    computer_use = ComputerUseService()
    
    try:
        result = await computer_use._fallback_download(url)
        
        if result.get("success"):
            print(f"✅ SUCCESS: {result.get('message')}")
            print(f"   Strategy used: {result.get('strategy_used', 'unknown')}")
            print(f"   Attempt: {result.get('attempt', 'unknown')}")
            
            # Get video info if available
            info = result.get("info", {})
            if info:
                print(f"   Title: {info.get('title', 'Unknown')}")
                print(f"   Duration: {info.get('duration', 'Unknown')} seconds")
                print(f"   Uploader: {info.get('uploader', 'Unknown')}")
            
            # Check audio file
            audio_path = result.get("audio_path")
            if audio_path and os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                print(f"   Audio file: {audio_path}")
                print(f"   File size: {file_size:,} bytes")
                
                # Ask user if they want to keep the file
                keep = input("\n🗂️ Keep the downloaded file? (y/N): ").strip().lower()
                if keep != 'y':
                    os.remove(audio_path)
                    print("   ✅ File cleaned up")
                else:
                    print(f"   📁 File kept at: {audio_path}")
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        logger.error(f"Test failed with exception: {str(e)}")

async def main():
    """Main test function"""
    
    print("🔧 YouTube Download Fix Tester")
    print("Testing enhanced yt-dlp fallback with multiple retry strategies")
    print()
    
    # Check if yt-dlp is installed
    try:
        import yt_dlp
        print(f"✅ yt-dlp version: {yt_dlp.version.__version__}")
    except ImportError:
        print("❌ yt-dlp not installed. Please install with: pip install yt-dlp")
        return
    except Exception as e:
        print(f"⚠️ yt-dlp import warning: {e}")
    
    print()
    
    # Run tests
    if len(sys.argv) > 1:
        await test_single_url()
    else:
        await test_youtube_download()

if __name__ == "__main__":
    asyncio.run(main())
