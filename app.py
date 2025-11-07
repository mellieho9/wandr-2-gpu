import os
from flask import Flask
from dotenv import load_dotenv

from endpoints.health import health_bp
from endpoints.processing import processing_bp

load_dotenv()

app = Flask(__name__)

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(processing_bp)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
