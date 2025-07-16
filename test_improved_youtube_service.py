#!/usr/bin/env python3
"""
Test script for the improved YouTube service
This script tests the key functionality of the YouTube service without the computer use dependency
"""

import asyncio
import sys
import os
import tempfile
import logging
from pathlib import Path

# Add the app directory to the path so we can import the services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.youtube_service import YouTubeService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YouTubeServiceTester:
    """Test class for YouTube service functionality"""
    
    def __init__(self):
        self.youtube_service = YouTubeService()
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log a test result"""
        status = "PASS" if success else "FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message
        }
        self.test_results.append(result)
        logger.info(f"{test_name}: {status} - {message}")
        
    def test_url_validation(self):
        """Test URL validation functionality"""
        logger.info("Testing URL validation...")
        
        # Test valid YouTube URLs
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube-nocookie.com/watch?v=dQw4w9WgXcQ"
        ]
        
        # Test invalid URLs
        invalid_urls = [
            "https://www.google.com",
            "https://www.vimeo.com/123456",
            "not_a_url",
            "https://www.youtube.com/invalid",
            ""
        ]
        
        # Test valid URLs
        valid_count = 0
        for url in valid_urls:
            if self.youtube_service.is_valid_youtube_url(url):
                valid_count += 1
        
        self.log_test_result(
            "Valid URL Detection",
            valid_count == len(valid_urls),
            f"Detected {valid_count}/{len(valid_urls)} valid URLs"
        )
        
        # Test invalid URLs
        invalid_count = 0
        for url in invalid_urls:
            if not self.youtube_service.is_valid_youtube_url(url):
                invalid_count += 1
        
        self.log_test_result(
            "Invalid URL Rejection",
            invalid_count == len(invalid_urls),
            f"Rejected {invalid_count}/{len(invalid_urls)} invalid URLs"
        )
        
    def test_video_id_extraction(self):
        """Test video ID extraction"""
        logger.info("Testing video ID extraction...")
        
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/watch?v=dQw4w9WgXcQ&t=10s", "dQw4w9WgXcQ"),
            ("invalid_url", "")
        ]
        
        success_count = 0
        for url, expected_id in test_cases:
            extracted_id = self.youtube_service._extract_video_id(url)
            if extracted_id == expected_id:
                success_count += 1
        
        self.log_test_result(
            "Video ID Extraction",
            success_count == len(test_cases),
            f"Extracted {success_count}/{len(test_cases)} video IDs correctly"
        )
        
    def test_user_agent_generation(self):
        """Test user agent generation"""
        logger.info("Testing user agent generation...")
        
        try:
            # Generate multiple user agents
            user_agents = []
            for _ in range(10):
                ua = self.youtube_service._get_random_user_agent()
                user_agents.append(ua)
            
            # Check that we get different user agents
            unique_uas = set(user_agents)
            
            # Check that all user agents are valid strings
            all_valid = all(isinstance(ua, str) and len(ua) > 0 for ua in user_agents)
            
            self.log_test_result(
                "User Agent Generation",
                all_valid and len(unique_uas) > 1,
                f"Generated {len(unique_uas)} unique user agents"
            )
            
        except Exception as e:
            self.log_test_result(
                "User Agent Generation",
                False,
                f"Error: {str(e)}"
            )
            
    def test_headers_generation(self):
        """Test HTTP headers generation"""
        logger.info("Testing headers generation...")
        
        try:
            headers = self.youtube_service._get_enhanced_headers()
            
            # Check required headers
            required_headers = ['Accept', 'Accept-Language', 'User-Agent']
            has_required = all(header in headers for header in required_headers)
            
            # Check that headers are strings
            all_strings = all(isinstance(value, str) for value in headers.values())
            
            self.log_test_result(
                "Headers Generation",
                has_required and all_strings,
                f"Generated {len(headers)} headers"
            )
            
        except Exception as e:
            self.log_test_result(
                "Headers Generation",
                False,
                f"Error: {str(e)}"
            )
            
    async def test_video_accessibility_check(self):
        """Test video accessibility check"""
        logger.info("Testing video accessibility check...")
        
        try:
            # Test with a known public video (Rick Roll - should be accessible)
            test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            
            result = await self.youtube_service._check_video_accessibility(test_url)
            
            # Check that we get a valid response structure
            has_accessible_key = 'accessible' in result
            has_title = 'title' in result
            
            self.log_test_result(
                "Video Accessibility Check",
                has_accessible_key and has_title,
                f"Accessibility: {result.get('accessible', 'Unknown')}, Title: {result.get('title', 'Unknown')}"
            )
            
        except Exception as e:
            self.log_test_result(
                "Video Accessibility Check",
                False,
                f"Error: {str(e)}"
            )
            
    def test_temp_directory_creation(self):
        """Test temporary directory creation"""
        logger.info("Testing temporary directory creation...")
        
        try:
            temp_dir = self.youtube_service.temp_dir
            
            # Check that temp directory exists
            dir_exists = os.path.exists(temp_dir)
            
            # Check that it's writable
            test_file = os.path.join(temp_dir, "test.txt")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                is_writable = os.path.exists(test_file)
                if is_writable:
                    os.remove(test_file)
            except:
                is_writable = False
            
            self.log_test_result(
                "Temporary Directory",
                dir_exists and is_writable,
                f"Directory: {temp_dir}, Exists: {dir_exists}, Writable: {is_writable}"
            )
            
        except Exception as e:
            self.log_test_result(
                "Temporary Directory",
                False,
                f"Error: {str(e)}"
            )
            
    def test_timestamp_formatting(self):
        """Test timestamp formatting"""
        logger.info("Testing timestamp formatting...")
        
        test_cases = [
            (0, "0:00"),
            (30, "0:30"),
            (60, "1:00"),
            (90, "1:30"),
            (3600, "1:00:00"),
            (3665, "1:01:05"),
            (7200, "2:00:00")
        ]
        
        success_count = 0
        for seconds, expected in test_cases:
            result = self.youtube_service.format_timestamp(seconds)
            if result == expected:
                success_count += 1
            else:
                logger.warning(f"Timestamp {seconds}s: expected {expected}, got {result}")
        
        self.log_test_result(
            "Timestamp Formatting",
            success_count == len(test_cases),
            f"Formatted {success_count}/{len(test_cases)} timestamps correctly"
        )
        
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("Starting YouTube service tests...")
        
        # Run synchronous tests
        self.test_url_validation()
        self.test_video_id_extraction()
        self.test_user_agent_generation()
        self.test_headers_generation()
        self.test_temp_directory_creation()
        self.test_timestamp_formatting()
        
        # Run asynchronous tests
        await self.test_video_accessibility_check()
        
        # Print summary
        self.print_test_summary()
        
    def print_test_summary(self):
        """Print test summary"""
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed = sum(1 for result in self.test_results if result["status"] == "FAIL")
        total = len(self.test_results)
        
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            logger.info("\nFAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    logger.info(f"  - {result['test']}: {result['message']}")
        
        logger.info("="*60)
        
        return failed == 0

async def main():
    """Main test function"""
    logger.info("YouTube Service Improvement Test")
    logger.info("="*60)
    
    tester = YouTubeServiceTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("All tests passed! ✅")
        sys.exit(0)
    else:
        logger.error("Some tests failed! ❌")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
