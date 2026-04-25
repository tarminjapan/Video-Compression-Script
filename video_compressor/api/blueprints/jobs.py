from flask import Blueprint, jsonify, request

from ...audio import compress_audio_service
from ...video import compress_video_service
from ..job_runner import job_runner

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("/video", methods=["POST"])
def start_video_compression():
    data = request.json
    input_path = data.get("input_path")
    if not input_path:
        return jsonify({"error": "input_path is required"}), 400

    # Simple validation
    crf = data.get("crf")
    if crf is not None and not (0 <= crf <= 63):
        return jsonify({"error": "CRF must be between 0 and 63"}), 400

    preset = data.get("preset")
    if preset is not None and not (0 <= preset <= 13):
        return jsonify({"error": "Preset must be between 0 and 13"}), 400

    task_id = job_runner.start_task(
        "video",
        compress_video_service,
        input_path=input_path,
        output_path=data.get("output_path"),
        crf=crf,
        preset=preset,
        audio_bitrate=data.get("audio_bitrate"),
        audio_enabled=data.get("audio_enabled", True),
        max_fps=data.get("max_fps"),
        resolution=data.get("resolution"),
        volume_gain_db=data.get("volume_gain_db"),
        denoise_level=data.get("denoise_level"),
    )

    return jsonify({"task_id": task_id}), 202


@jobs_bp.route("/audio", methods=["POST"])
def start_audio_compression():
    data = request.json
    input_path = data.get("input_path")
    if not input_path:
        return jsonify({"error": "input_path is required"}), 400

    task_id = job_runner.start_task(
        "audio",
        compress_audio_service,
        input_path=input_path,
        output_path=data.get("output_path"),
        bitrate=data.get("bitrate"),
        volume_gain_db=data.get("volume_gain_db"),
        denoise_level=data.get("denoise_level"),
        keep_metadata=data.get("keep_metadata", True),
    )

    return jsonify({"task_id": task_id}), 202


@jobs_bp.route("", methods=["GET"])
def list_jobs():
    return jsonify(job_runner.list_tasks())


@jobs_bp.route("/<task_id>", methods=["GET"])
def get_job_status(task_id):
    task = job_runner.get_task(task_id)
    if not task:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(
        {
            "id": task["id"],
            "status": task["status"],
            "progress": task["progress"],
            "result": task["result"],
            "type": task["type"],
            "created_at": task.get("created_at"),
            "finished_at": task.get("finished_at"),
        }
    )


@jobs_bp.route("/<task_id>", methods=["DELETE"])
def cancel_job(task_id):
    success = job_runner.cancel_task(task_id)
    if not success:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({"status": "cancelling"})
