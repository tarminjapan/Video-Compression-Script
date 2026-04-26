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

    return app
