from pathlib import Path

from flask import Blueprint, jsonify, request

from ...audio import get_audio_info_safe
from ...video import get_video_info_safe
from ...volume import analyze_volume_level

media_bp = Blueprint("media", __name__)


@media_bp.route("/media-info", methods=["GET"])
def get_info():
    path = request.args.get("path")
    if not path:
        return jsonify({"error": "Path is required"}), 400

    path_obj = Path(path)
    if not path_obj.exists():
        return jsonify({"error": "File not found"}), 404

    # Try video info first
    info = get_video_info_safe(path_obj)
    if info:
        info["type"] = "video"
        return jsonify(info)

    # Try audio info
    info = get_audio_info_safe(path_obj)
    if info:
        info["type"] = "audio"
        return jsonify(info)

    return jsonify({"error": "Unsupported file format"}), 400


@media_bp.route("/volume/analyze", methods=["POST"])
def analyze_volume_endpoint():
    data = request.json
    path = data.get("path")
    if not path:
        return jsonify({"error": "Path is required"}), 400

    path_obj = Path(path)
    if not path_obj.exists():
        return jsonify({"error": "File not found"}), 404

    try:
        result = analyze_volume_level(path_obj)
        if result["mean_volume"] is not None:
            return jsonify(result)
        else:
            return jsonify({"error": "Failed to analyze volume"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
