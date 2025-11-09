import logging
import threading
import torch
from typing import Dict

from config.settings import settings
from services.video_downloader import VideoDownloader
from services.whisper_gpu import WhisperGPU
from services.ocr_service import OCRService
from utils.job_store import JobStore

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """Orchestrates GPU-accelerated video processing"""

    def __init__(self, job_store: JobStore):
        self.downloader = VideoDownloader()
        self.whisper = WhisperGPU(model_size=settings.WHISPER_MODEL)
        self.ocr = OCRService()
        self.job_store = job_store

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
        logger.info(f"Starting processing for job {job_id}: {url}")

        try:
            # Step 1: Download
            logger.info(f"[{job_id}] Step 1/3: Downloading video")
            self.job_store.update_job(
                job_id, {"status": "downloading", "progress": {"step": 1, "total": 3}}
            )
            video_path = self.downloader.download(url, job_id)
            logger.info(f"[{job_id}] Video downloaded: {video_path}")

            # Step 2: Transcribe
            logger.info(f"[{job_id}] Step 2/3: Transcribing audio")
            self.job_store.update_job(
                job_id, {"status": "transcribing", "progress": {"step": 2, "total": 3}}
            )
            transcription = self.whisper.transcribe(video_path)
            logger.info(
                f"[{job_id}] Transcription completed: {len(transcription)} characters"
            )

            # Step 3: OCR
            logger.info(f"[{job_id}] Step 3/3: Extracting text from frames")
            self.job_store.update_job(
                job_id,
                {"status": "extracting_text", "progress": {"step": 3, "total": 3}},
            )
            ocr_text = self.ocr.extract_text(video_path)
            logger.info(f"[{job_id}] OCR completed: {len(ocr_text)} characters")

            # Complete
            logger.info(f"[{job_id}] Processing completed successfully")
            self.job_store.update_job(
                job_id,
                {
                    "status": "completed",
                    "result": {"transcription": transcription, "ocr_text": ocr_text},
                },
            )

        except Exception as e:
            logger.error(f"[{job_id}] Processing failed: {str(e)}", exc_info=True)
            self.job_store.update_job(job_id, {"status": "failed", "error": str(e)})

        finally:
            # Cleanup
            if video_path:
                logger.debug(f"[{job_id}] Cleaning up video file: {video_path}")
                self.downloader.cleanup(video_path)

    def gpu_available(self) -> bool:
        """Check if GPU is available"""
        return torch.cuda.is_available()
