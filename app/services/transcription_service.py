import whisper
import asyncio
import os
import logging
from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
import re
import torch

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Service for transcribing audio and analyzing content"""
    
    def __init__(self):
        # Detect and configure GPU/CPU device
        self.device = self._get_device()
        logger.info(f"Using device: {self.device}")
        
        # Load Whisper model with appropriate device
        # Use base model for balance of speed/accuracy, but consider larger models for GPU
        model_name = "base"
        if self.device == "cuda":
            # Use larger model on GPU for better accuracy and speed
            model_name = "small"
            logger.info("GPU detected - using 'small' model for better accuracy")
            
            # Set CUDA memory fraction to prevent OOM
            torch.cuda.set_per_process_memory_fraction(0.8)
            
            # Ensure proper CUDA device selection
            torch.cuda.set_device(0)
        
        logger.info(f"Loading Whisper model '{model_name}' on device '{self.device}'")
        self.model = whisper.load_model(model_name, device=self.device)
        
        # Verify the model is on the correct device
        if hasattr(self.model, 'device'):
            logger.info(f"Model loaded on device: {self.model.device}")
        
        # Configure transcription options based on device
        self.transcribe_options = {
            "fp16": self.device == "cuda",  # Use FP16 only on GPU
            "language": None,  # Auto-detect language
            "task": "transcribe",
            "verbose": False
        }
        
        if self.device == "cuda":
            # GPU-specific optimizations
            self.transcribe_options.update({
                "beam_size": 5,  # Better accuracy on GPU
                "best_of": 5,    # Multiple attempts for better results
                "temperature": 0.0,  # Deterministic output
            })
        else:
            # CPU-specific optimizations for speed
            self.transcribe_options.update({
                "beam_size": 1,  # Faster on CPU
                "best_of": 1,    # Single attempt for speed
                "temperature": 0.0,
            })
        
        logger.info(f"Transcription options: {self.transcribe_options}")
        
        # Download NLTK data if not present
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
        
        self.stop_words = set(stopwords.words('english'))
    
    async def transcribe_segments(self, audio_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transcribe audio segments using Whisper"""
        transcriptions = []
        
        for i, segment in enumerate(audio_segments):
            try:
                logger.info(f"Transcribing segment {i+1}/{len(audio_segments)}")
                
                # Transcribe using Whisper with device-specific options
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._transcribe_with_options, segment['path']
                )
                
                # Clean up the transcript
                transcript = self._clean_transcript(result['text'])
                
                transcriptions.append({
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'duration': segment['duration'],
                    'transcript': transcript,
                    'confidence': self._calculate_confidence(result),
                    'word_count': len(transcript.split()),
                    'path': segment['path']
                })
                
            except Exception as e:
                logger.error(f"Error transcribing segment {i}: {str(e)}")
                # Add empty transcription for failed segments
                transcriptions.append({
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'duration': segment['duration'],
                    'transcript': "",
                    'confidence': 0.0,
                    'word_count': 0,
                    'path': segment['path']
                })
        
        return transcriptions
    
    async def identify_key_segments(self, transcriptions: List[Dict[str, Any]], max_segments: int = 5) -> List[Dict[str, Any]]:
        """Identify the most important segments based on content analysis"""
        try:
            # Filter out empty transcriptions
            valid_transcriptions = [t for t in transcriptions if t['transcript'].strip()]
            
            if not valid_transcriptions:
                return []
            
            # Calculate importance scores
            scored_segments = []
            
            for transcription in valid_transcriptions:
                score = self._calculate_importance_score(transcription, valid_transcriptions)
                
                scored_segments.append({
                    **transcription,
                    'importance_score': score
                })
            
            # Sort by importance score and return top segments
            scored_segments.sort(key=lambda x: x['importance_score'], reverse=True)
            
            # Return top segments, but ensure minimum transcript length
            key_segments = []
            for segment in scored_segments:
                if len(key_segments) >= max_segments:
                    break
                if segment['word_count'] >= 10:  # Minimum word count threshold
                    key_segments.append(segment)
            
            # If we don't have enough segments, add more with lower thresholds
            if len(key_segments) < max_segments:
                for segment in scored_segments:
                    if len(key_segments) >= max_segments:
                        break
                    if segment not in key_segments and segment['word_count'] >= 5:
                        key_segments.append(segment)
            
            logger.info(f"Selected {len(key_segments)} key segments from {len(valid_transcriptions)} total segments")
            return key_segments
            
        except Exception as e:
            logger.error(f"Error identifying key segments: {str(e)}")
            # Return first few segments as fallback
            return transcriptions[:max_segments]
    
    def _clean_transcript(self, text: str) -> str:
        """Clean and normalize transcript text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove filler words and sounds
        filler_words = ['um', 'uh', 'er', 'ah', 'like', 'you know', 'so']
        for filler in filler_words:
            text = re.sub(rf'\b{filler}\b', '', text, flags=re.IGNORECASE)
        
        # Clean up punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        return text.strip()
    
    def _calculate_confidence(self, whisper_result: Dict) -> float:
        """Calculate confidence score from Whisper result"""
        # Whisper doesn't provide direct confidence scores
        # We'll estimate based on segment consistency and word detection
        segments = whisper_result.get('segments', [])
        if not segments:
            return 0.5
        
        # Calculate average probability if available
        total_prob = 0
        count = 0
        
        for segment in segments:
            if 'avg_logprob' in segment:
                # Convert log probability to regular probability
                prob = np.exp(segment['avg_logprob'])
                total_prob += prob
                count += 1
        
        if count > 0:
            return min(total_prob / count, 1.0)
        else:
            return 0.5
    
    def _calculate_importance_score(self, transcription: Dict[str, Any], all_transcriptions: List[Dict[str, Any]]) -> float:
        """Calculate importance score for a transcript segment"""
        try:
            text = transcription['transcript']
            
            # Base score factors
            word_count_score = min(transcription['word_count'] / 100, 1.0)  # Normalize to 0-1
            confidence_score = transcription['confidence']
            duration_score = min(transcription['duration'] / 60, 1.0)  # Normalize to 0-1
            
            # Content-based scoring
            content_score = self._calculate_content_score(text, all_transcriptions)
            
            # Keyword density score
            keyword_score = self._calculate_keyword_density(text)
            
            # Combine scores with weights
            importance_score = (
                word_count_score * 0.2 +
                confidence_score * 0.2 +
                duration_score * 0.1 +
                content_score * 0.3 +
                keyword_score * 0.2
            )
            
            return importance_score
            
        except Exception as e:
            logger.error(f"Error calculating importance score: {str(e)}")
            return 0.0
    
    def _calculate_content_score(self, text: str, all_transcriptions: List[Dict[str, Any]]) -> float:
        """Calculate content importance using TF-IDF"""
        try:
            # Prepare all texts for TF-IDF
            all_texts = [t['transcript'] for t in all_transcriptions if t['transcript'].strip()]
            
            if len(all_texts) < 2:
                return 0.5
            
            # Calculate TF-IDF
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Find the index of current text
            current_index = None
            for i, t in enumerate(all_texts):
                if t == text:
                    current_index = i
                    break
            
            if current_index is None:
                return 0.0
            
            # Calculate average TF-IDF score for this segment
            current_vector = tfidf_matrix[current_index]
            score = np.mean(current_vector.data) if current_vector.data.size > 0 else 0.0
            
            return min(score * 2, 1.0)  # Scale and cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating content score: {str(e)}")
            return 0.0
    
    def _calculate_keyword_density(self, text: str) -> float:
        """Calculate keyword density score"""
        try:
            # Important keywords that might indicate key content
            important_keywords = [
                'important', 'key', 'main', 'primary', 'essential', 'crucial',
                'first', 'second', 'third', 'finally', 'conclusion', 'summary',
                'problem', 'solution', 'result', 'outcome', 'finding',
                'because', 'therefore', 'however', 'moreover', 'furthermore'
            ]
            
            words = word_tokenize(text.lower())
            keyword_count = sum(1 for word in words if word in important_keywords)
            
            if len(words) == 0:
                return 0.0
            
            density = keyword_count / len(words)
            return min(density * 10, 1.0)  # Scale and cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating keyword density: {str(e)}")
            return 0.0
    
    def _transcribe_with_options(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio file with device-specific optimizations"""
        try:
            # Log GPU memory usage if available
            if self.device == "cuda":
                memory_allocated = torch.cuda.memory_allocated(0) / 1024**3
                memory_reserved = torch.cuda.memory_reserved(0) / 1024**3
                logger.info(f"GPU memory before transcription: {memory_allocated:.2f}GB allocated, {memory_reserved:.2f}GB reserved")
            
            # Transcribe with the configured options
            result = self.model.transcribe(audio_path, **self.transcribe_options)
            
            # Log GPU memory usage after transcription
            if self.device == "cuda":
                memory_allocated = torch.cuda.memory_allocated(0) / 1024**3
                memory_reserved = torch.cuda.memory_reserved(0) / 1024**3
                logger.info(f"GPU memory after transcription: {memory_allocated:.2f}GB allocated, {memory_reserved:.2f}GB reserved")
                
                # Clean up GPU memory
                torch.cuda.empty_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in transcription: {str(e)}")
            # Fallback to basic transcription without options
            return self.model.transcribe(audio_path)
    
    def _get_device(self) -> str:
        """Detect and return the best available device for PyTorch"""
        try:
            # Check for forced CPU mode
            if os.getenv("FORCE_CPU", "").lower() == "true":
                logger.info("FORCE_CPU is set, using CPU mode")
                return "cpu"
            
            # Check for GPU availability
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                device_name = torch.cuda.get_device_name(0)
                memory_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
                logger.info(f"CUDA GPU available: {device_name} (Total devices: {device_count}, Memory: {memory_total:.1f}GB)")
                
                # Test GPU functionality
                try:
                    test_tensor = torch.tensor([1.0]).cuda()
                    logger.info("✅ GPU test successful - CUDA is working properly")
                    return "cuda"
                except Exception as e:
                    logger.warning(f"GPU test failed: {e}, falling back to CPU")
                    return "cpu"
            else:
                logger.info("CUDA not available, using CPU")
                return "cpu"
        except Exception as e:
            logger.warning(f"Error detecting device: {e}, defaulting to CPU")
            return "cpu"
