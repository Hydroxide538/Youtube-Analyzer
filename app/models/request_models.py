from pydantic import BaseModel, HttpUrl
from typing import Optional

class VideoRequest(BaseModel):
    """Request model for video processing"""
    url: str
    max_segments: Optional[int] = 5
    segment_length: Optional[int] = 60  # seconds
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
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
    key_points: list[str]
    timestamp: str
