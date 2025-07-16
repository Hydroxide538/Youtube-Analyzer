from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class VideoRequest(BaseModel):
    """Request model for video processing"""
    url: str
    max_segments: Optional[int] = 5
    segment_length: Optional[int] = 60  # seconds
    video_type: Optional[str] = "auto"  # "youtube", "conference", or "auto"
    username: Optional[str] = None  # For conference videos requiring authentication
    password: Optional[str] = None  # For conference videos requiring authentication
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "max_segments": 5,
                "segment_length": 60,
                "video_type": "youtube"
            }
        }

class ConferenceVideoRequest(BaseModel):
    """Request model for conference video processing with authentication"""
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    max_segments: Optional[int] = 5
    segment_length: Optional[int] = 60  # seconds
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://conference.example.com/session/123",
                "username": "user@example.com",
                "password": "password123",
                "max_segments": 5,
                "segment_length": 60
            }
        }

class VideoSegment(BaseModel):
    """Model for video segment data"""
    start_time: float
    end_time: float
    transcript: str
    importance_score: float

class SummaryResult(BaseModel):
    """Model for summary results"""
    segment: VideoSegment
    summary: str
    key_points: List[str]
    timestamp: str
