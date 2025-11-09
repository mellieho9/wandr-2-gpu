import os
import cv2
import torch
from google.cloud import vision
from typing import List


class OCRService:
    """GPU-accelerated frame extraction + Google Vision OCR"""

    def __init__(self):
        self.vision_client = vision.ImageAnnotatorClient()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def extract_text(self, video_path: str, sample_rate: int = 30) -> str:
        """
        Extract text from video frames

        Args:
            video_path: Path to video file
            sample_rate: Extract 1 frame every N frames

        Returns:
            Combined text from all frames
        """
        frames = self._extract_frames(video_path, sample_rate)

        all_text = []
        for frame_data in frames:
            text = self._ocr_frame(frame_data)
            if text:
                all_text.append(text)

        # Deduplicate and combine
        unique_text = list(dict.fromkeys(all_text))
        return " ".join(unique_text)

    def _extract_frames(self, video_path: str, sample_rate: int) -> List[bytes]:
        """Extract frames using OpenCV (GPU-accelerated if available)"""
        cap = cv2.VideoCapture(video_path)
        frames = []
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % sample_rate == 0:
                # Encode frame to JPEG
                _, buffer = cv2.imencode(".jpg", frame)
                frames.append(buffer.tobytes())

            frame_count += 1

        cap.release()
        return frames

    def _ocr_frame(self, frame_data: bytes) -> str:
        """Run OCR on single frame using Google Vision"""
        try:
            image = vision.Image(content=frame_data)
            response = self.vision_client.text_detection(image=image)

            if response.text_annotations:
                return response.text_annotations[0].description

            return ""
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
