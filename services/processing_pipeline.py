import threading
import torch
from typing import Dict

from config.settings import settings
from services.video_downloader import VideoDownloader
from services.whisper_gpu import WhisperGPU
from services.ocr_service import OCRService
from utils.job_store import JobStore


class ProcessingPipeline:
    """Orchestrates GPU-accelerated video processing"""

    def __init__(self):
        self.downloader = VideoDownloader()
        self.whisper = WhisperGPU(model_size=settings.WHISPER_MODEL)
        self.ocr = OCRService()
        self.job_store = JobStore()

    def process_async(self, job_id: str, url: str, schema: Dict, prompt: str):
        """Start processing in background thread"""
        thread = threading.Thread(
            target=self._process, args=(job_id, url, schema, prompt)
        )
        thread.daemon = True
        thread.start()

    def _process(self, job_id: str, url: str, schema: Dict, prompt: str):
        """Execute full processing pipeline"""
        video_path = None

        try:
            # Step 1: Download
            self.job_store.update_job(
                job_id, {"status": "downloading", "progress": {"step": 1, "total": 3}}
            )
            video_path = self.downloader.download(url, job_id)

            # Step 2: Transcribe
            self.job_store.update_job(
                job_id, {"status": "transcribing", "progress": {"step": 2, "total": 3}}
            )
            transcription = self.whisper.transcribe(video_path)

            # Step 3: OCR
            self.job_store.update_job(
                job_id,
                {"status": "extracting_text", "progress": {"step": 3, "total": 3}},
            )
            ocr_text = self.ocr.extract_text(video_path)

            # Complete
            self.job_store.update_job(
                job_id,
                {
                    "status": "completed",
                    "result": {"transcription": transcription, "ocr_text": ocr_text},
                },
            )

        except Exception as e:
            self.job_store.update_job(job_id, {"status": "failed", "error": str(e)})

        finally:
            # Cleanup
            if video_path:
                self.downloader.cleanup(video_path)

    def gpu_available(self) -> bool:
        """Check if GPU is available"""
        return torch.cuda.is_available()
