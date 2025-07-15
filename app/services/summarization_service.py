import ollama
import asyncio
import logging
from typing import List, Dict, Any
import json
import re
import os

logger = logging.getLogger(__name__)

class SummarizationService:
    """Service for generating summaries using Ollama"""
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        # Configure Ollama client to use external host
        ollama_host = os.getenv('OLLAMA_HOST', 'localhost:11434')
        self.client = ollama.AsyncClient(host=f'http://{ollama_host}')
        
    async def summarize_segments(self, key_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate summaries for key segments using Ollama"""
        summaries = []
        
        for i, segment in enumerate(key_segments):
            try:
                logger.info(f"Summarizing segment {i+1}/{len(key_segments)}")
                
                # Generate summary for this segment
                summary_data = await self._generate_segment_summary(segment)
                
                summaries.append({
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'timestamp': self._format_timestamp(segment['start_time']),
                    'duration': segment['duration'],
                    'original_transcript': segment['transcript'],
                    'summary': summary_data['summary'],
                    'key_points': summary_data['key_points'],
                    'importance_score': segment.get('importance_score', 0.0),
                    'confidence': segment.get('confidence', 0.0)
                })
                
            except Exception as e:
                logger.error(f"Error summarizing segment {i}: {str(e)}")
                # Add fallback summary
                summaries.append({
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'timestamp': self._format_timestamp(segment['start_time']),
                    'duration': segment['duration'],
                    'original_transcript': segment['transcript'],
                    'summary': f"Summary unavailable. Original transcript: {segment['transcript'][:200]}...",
                    'key_points': [],
                    'importance_score': segment.get('importance_score', 0.0),
                    'confidence': 0.0
                })
        
        return summaries
    
    async def _generate_segment_summary(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary and key points for a single segment"""
        transcript = segment['transcript']
        
        if not transcript.strip():
            return {
                'summary': "No content available for this segment.",
                'key_points': []
            }
        
        # Create prompt for summarization
        prompt = self._create_summarization_prompt(transcript, segment)
        
        try:
            # Call Ollama API
            response = await self.client.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert at creating concise, informative summaries of video content. Focus on extracting the most important information and key insights.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.3,
                    'top_p': 0.9,
                    'max_tokens': 300
                }
            )
            
            # Parse the response
            content = response['message']['content']
            return self._parse_summary_response(content)
            
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            # Fallback to simple extractive summary
            return self._create_fallback_summary(transcript)
    
    def _create_summarization_prompt(self, transcript: str, segment: Dict[str, Any]) -> str:
        """Create a prompt for the summarization model"""
        duration = segment.get('duration', 0)
        start_time = self._format_timestamp(segment.get('start_time', 0))
        
        prompt = f"""
Please analyze and summarize the following video transcript segment:

**Segment Info:**
- Timestamp: {start_time}
- Duration: {duration:.1f} seconds
- Word count: {len(transcript.split())} words

**Transcript:**
{transcript}

**Instructions:**
1. Create a concise summary (2-3 sentences) that captures the main points
2. Extract 3-5 key points or insights from this segment
3. Focus on actionable information, important concepts, or significant statements

**Response Format:**
SUMMARY: [Your 2-3 sentence summary here]

KEY_POINTS:
- [Key point 1]
- [Key point 2]
- [Key point 3]
- [Additional points if relevant]

Keep the summary clear, informative, and focused on the most valuable content from this segment.
"""
        return prompt
    
    def _parse_summary_response(self, content: str) -> Dict[str, Any]:
        """Parse the model's response to extract summary and key points"""
        try:
            # Extract summary
            summary_match = re.search(r'SUMMARY:\s*(.*?)(?=KEY_POINTS:|$)', content, re.DOTALL | re.IGNORECASE)
            summary = summary_match.group(1).strip() if summary_match else ""
            
            # Extract key points
            key_points_match = re.search(r'KEY_POINTS:\s*(.*)', content, re.DOTALL | re.IGNORECASE)
            key_points_text = key_points_match.group(1).strip() if key_points_match else ""
            
            # Parse key points (look for bullet points or numbered lists)
            key_points = []
            if key_points_text:
                lines = key_points_text.split('\n')
                for line in lines:
                    line = line.strip()
                    # Remove bullet points, numbers, or dashes
                    line = re.sub(r'^[-•*\d+\.)\s]+', '', line).strip()
                    if line and len(line) > 10:  # Minimum length for a key point
                        key_points.append(line)
            
            # Fallback if parsing failed
            if not summary:
                summary = content[:200] + "..." if len(content) > 200 else content
            
            if not key_points:
                # Try to extract sentences as key points
                sentences = re.split(r'[.!?]+', content)
                key_points = [s.strip() for s in sentences if len(s.strip()) > 20][:3]
            
            return {
                'summary': summary,
                'key_points': key_points[:5]  # Limit to 5 key points
            }
            
        except Exception as e:
            logger.error(f"Error parsing summary response: {str(e)}")
            return self._create_fallback_summary(content)
    
    def _create_fallback_summary(self, text: str) -> Dict[str, Any]:
        """Create a simple extractive summary as fallback"""
        try:
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
            
            # Take first few sentences as summary
            summary_sentences = sentences[:2] if len(sentences) >= 2 else sentences
            summary = '. '.join(summary_sentences) + '.'
            
            # Use remaining sentences as key points
            key_points = sentences[2:5] if len(sentences) > 2 else sentences[1:4]
            key_points = [point + '.' for point in key_points if point]
            
            return {
                'summary': summary,
                'key_points': key_points
            }
            
        except Exception as e:
            logger.error(f"Error creating fallback summary: {str(e)}")
            return {
                'summary': text[:200] + "..." if len(text) > 200 else text,
                'key_points': []
            }
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS or HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    async def check_ollama_connection(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            # Try to list available models
            models = await self.client.list()
            model_names = [model['name'] for model in models['models']]
            
            if self.model_name not in model_names:
                logger.warning(f"Model {self.model_name} not found. Available models: {model_names}")
                # Try to use the first available model
                if model_names:
                    self.model_name = model_names[0]
                    logger.info(f"Switching to model: {self.model_name}")
                else:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking Ollama connection: {str(e)}")
            return False
    
    async def generate_overall_summary(self, segment_summaries: List[Dict[str, Any]], video_title: str) -> Dict[str, Any]:
        """Generate an overall summary of the entire video"""
        try:
            # Combine all segment summaries
            combined_content = []
            for i, segment in enumerate(segment_summaries):
                combined_content.append(f"Segment {i+1} ({segment['timestamp']}): {segment['summary']}")
            
            combined_text = '\n\n'.join(combined_content)
            
            prompt = f"""
Based on the following segment summaries from the video "{video_title}", create an overall summary:

{combined_text}

Please provide:
1. A comprehensive summary of the entire video (3-4 sentences)
2. The main themes or topics covered
3. Key takeaways or conclusions

Format your response as:
OVERALL_SUMMARY: [Your comprehensive summary]
MAIN_THEMES: [List of main themes]
KEY_TAKEAWAYS: [List of key takeaways]
"""
            
            response = await self.client.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert at synthesizing information from multiple sources to create comprehensive overviews.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.3,
                    'top_p': 0.9,
                    'max_tokens': 400
                }
            )
            
            content = response['message']['content']
            return self._parse_overall_summary(content)
            
        except Exception as e:
            logger.error(f"Error generating overall summary: {str(e)}")
            return {
                'overall_summary': f"This video covers multiple topics as analyzed in {len(segment_summaries)} key segments.",
                'main_themes': [],
                'key_takeaways': []
            }
    
    def _parse_overall_summary(self, content: str) -> Dict[str, Any]:
        """Parse the overall summary response"""
        try:
            # Extract overall summary
            summary_match = re.search(r'OVERALL_SUMMARY:\s*(.*?)(?=MAIN_THEMES:|$)', content, re.DOTALL | re.IGNORECASE)
            overall_summary = summary_match.group(1).strip() if summary_match else ""
            
            # Extract main themes
            themes_match = re.search(r'MAIN_THEMES:\s*(.*?)(?=KEY_TAKEAWAYS:|$)', content, re.DOTALL | re.IGNORECASE)
            themes_text = themes_match.group(1).strip() if themes_match else ""
            
            # Extract key takeaways
            takeaways_match = re.search(r'KEY_TAKEAWAYS:\s*(.*)', content, re.DOTALL | re.IGNORECASE)
            takeaways_text = takeaways_match.group(1).strip() if takeaways_match else ""
            
            # Parse lists
            main_themes = self._parse_list_items(themes_text)
            key_takeaways = self._parse_list_items(takeaways_text)
            
            return {
                'overall_summary': overall_summary or content[:300],
                'main_themes': main_themes,
                'key_takeaways': key_takeaways
            }
            
        except Exception as e:
            logger.error(f"Error parsing overall summary: {str(e)}")
            return {
                'overall_summary': content[:300] if content else "Summary unavailable",
                'main_themes': [],
                'key_takeaways': []
            }
    
    def _parse_list_items(self, text: str) -> List[str]:
        """Parse list items from text"""
        if not text:
            return []
        
        lines = text.split('\n')
        items = []
        
        for line in lines:
            line = line.strip()
            # Remove bullet points, numbers, or dashes
            line = re.sub(r'^[-•*\d+\.)\s]+', '', line).strip()
            if line and len(line) > 5:
                items.append(line)
        
        return items[:5]  # Limit to 5 items
