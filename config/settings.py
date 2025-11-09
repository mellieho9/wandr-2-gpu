import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Settings:
    """Application settings"""

    # Flask
    PORT = int(os.environ.get("PORT", 8080))
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")

    # GPU Models
    WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")

    # Video Processing
    VIDEO_OUTPUT_DIR = os.environ.get("VIDEO_OUTPUT_DIR", "/tmp/videos")

    # Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    # Redis
    REDIS_HOST = os.environ.get("REDIS_HOST")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        """Validate required settings"""
        errors = []

        # Google credentials are optional - warn if missing
        if not cls.GOOGLE_APPLICATION_CREDENTIALS:
            logger.warning(
                "GOOGLE_APPLICATION_CREDENTIALS not set - OCR will be disabled"
            )
        elif not os.path.exists(cls.GOOGLE_APPLICATION_CREDENTIALS):
            logger.warning(
                f"Credentials file not found: {cls.GOOGLE_APPLICATION_CREDENTIALS}"
            )

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        return True


settings = Settings()
