from flask import Flask

from config.settings import settings
from endpoints.health import health_bp
from endpoints.processing import processing_bp

# Validate settings on startup
settings.validate()

app = Flask(__name__)

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(processing_bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.PORT, debug=False)
