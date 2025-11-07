import os
import torch
from faster_whisper import WhisperModel
import ffmpeg


class WhisperGPU:
    """GPU-accelerated Whisper transcription"""
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper model
        
        Args:
            model_size: tiny, base, small, medium, large
        """
        self.model_size = model_size
        
        # Use GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        
        print(f"Loading Whisper model '{model_size}' on {device}")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
    
    def transcribe(self, video_path: str) -> str:
        """
        Transcribe audio from video
        
        Args:
            video_path: Path to video file
            
        Returns:
            Full transcription text
        """
        # Extract audio to temporary file
        audio_path = video_path.replace('.mp4', '.wav')
        
        try:
            # Extract audio using ffmpeg
            (
                ffmpeg
                .input(video_path)
                .output(audio_path, acodec='pcm_s16le', ac=1, ar='16k')
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Transcribe
            segments, info = self.model.transcribe(audio_path, beam_size=5)
            
            # Combine all segments
            transcription = " ".join([segment.text for segment in segments])
            
            return transcription.strip()
        
        finally:
            # Cleanup audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)
    
    def gpu_available(self) -> bool:
        """Check if GPU is available"""
        return torch.cuda.is_available()
