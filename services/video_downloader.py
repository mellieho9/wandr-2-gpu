import os
import yt_dlp
from typing import Optional

from config.settings import settings


class VideoDownloader:
    """Download videos from TikTok and Instagram"""

    def __init__(self):
        self.output_dir = settings.VIDEO_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def download(self, url: str, job_id: str) -> str:
        """
        Download video and return local file path

        Args:
            url: Video URL (TikTok or Instagram)
            job_id: Unique job identifier

        Returns:
            Path to downloaded video file
        """
        output_path = os.path.join(self.output_dir, f"{job_id}.mp4")

        ydl_opts = {
            "format": "best",
            "outtmpl": output_path,
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            return output_path
        except Exception as e:
            raise Exception(f"Failed to download video: {str(e)}")

    def cleanup(self, file_path: str):
        """Remove downloaded video file"""
        if os.path.exists(file_path):
            os.remove(file_path)
