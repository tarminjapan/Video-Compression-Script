import time
from typing import Any

from flask import Flask
from flask_cors import CORS

from .blueprints.jobs import jobs_bp
from .blueprints.media import media_bp
from .blueprints.settings import settings_bp
from .config import config_by_name
from .job_runner import job_runner


def create_app(config_name: str | dict[str, Any] = "dev"):
    app = Flask(__name__)

    # Configure app
    if isinstance(config_name, dict):
        app.config.from_mapping(config_name)
    else:
        app.config.from_object(config_by_name[config_name])

    # Restrict CORS to local development and electron context
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "app://."]}})

    # Start background cleanup
    job_runner.start_cleanup_thread()

    # Register Blueprints
    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
    app.register_blueprint(media_bp, url_prefix="/api")
    app.register_blueprint(settings_bp, url_prefix="/api/settings")

    # Add a root health check for convenience
    @app.route("/api/health")
    def root_health():
        return {"status": "healthy", "timestamp": time.time(), "version": "1.0.0"}

    # Register root_health explicitly is not needed as decorator does it,
    # but to satisfy 'not accessed' we can reference it
    _ = root_health

    return app
