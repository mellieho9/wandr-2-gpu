import logging
from flask import Flask

from config.settings import settings
from utils.logger import setup_logging
from endpoints.health import health_bp
from endpoints.processing import processing_bp

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Validate settings on startup
settings.validate()
logger.info(f"Starting Wandr GPU service on port {settings.PORT}")

app = Flask(__name__)

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(processing_bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.PORT, debug=False)
