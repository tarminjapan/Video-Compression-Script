import time

from flask import Blueprint, jsonify, request

from ...settings import SettingsManager

settings_bp = Blueprint("settings", __name__)
settings_manager = SettingsManager.get_instance()


@settings_bp.route("", methods=["GET"])
def get_settings():
    # Return all settings or default values
    settings = {
        "language": settings_manager.get("language", "en"),
        "appearance_mode": settings_manager.get("appearance_mode", "system"),
        "ffmpeg_path": settings_manager.get("ffmpeg_path", ""),
        "default_output_dir": settings_manager.get("default_output_dir", ""),
        # Add more default settings as needed
    }
    return jsonify(settings)


@settings_bp.route("", methods=["POST"])
def update_settings():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    settings_manager.update_all(data)

    return jsonify({"status": "success"})


@settings_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "timestamp": time.time(), "version": "1.0.0"})
