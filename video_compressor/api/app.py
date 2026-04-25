import threading
import uuid
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path

from ..video import compress_video_service, get_video_info_safe
from ..audio import compress_audio_service, get_audio_info_safe
from ..progress_handler import CancellationSource, ProgressEvent

# Global task storage
tasks = {}
tasks_lock = threading.Lock()
_cleanup_thread_started = False

def _cleanup_loop():
    """Background thread to clean up old tasks every 10 minutes."""
    while True:
        # Check every 10 minutes
        time.sleep(600)
        now = time.time()
        with tasks_lock:
            to_delete = []
            for tid, t in tasks.items():
                # Remove tasks that finished more than 1 hour ago
                if t.get("status") in ["success", "failed", "cancelled"]:
                    finished_at = t.get("finished_at")
                    if finished_at and (now - finished_at) > 3600:
                        to_delete.append(tid)
            
            for tid in to_delete:
                del tasks[tid]

def create_app():
    global _cleanup_thread_started
    app = Flask(__name__)
    # Restrict CORS to local development and electron context
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "app://."]}})

    if not _cleanup_thread_started:
        cleanup_thread = threading.Thread(target=_cleanup_loop, daemon=True)
        cleanup_thread.start()
        _cleanup_thread_started = True

    def _start_task(task_type, compression_func, **kwargs):
        task_id = str(uuid.uuid4())
        cancel_source = CancellationSource()
        
        with tasks_lock:
            # Basic cleanup if too many tasks (safety limit)
            if len(tasks) > 100:
                finished_ids = [tid for tid, t in tasks.items() if t["status"] in ["success", "failed", "cancelled"]]
                # Remove first few finished tasks
                for fid in finished_ids[:20]:
                    del tasks[fid]

            tasks[task_id] = {
                "id": task_id,
                "status": "pending",
                "progress": None,
                "result": None,
                "cancel_source": cancel_source,
                "type": task_type,
                "created_at": time.time()
            }
        
        def run_task():
            def on_progress(event: ProgressEvent):
                with tasks_lock:
                    if task_id in tasks:
                        tasks[task_id]["progress"] = {
                            "percent": event.percent,
                            "current_time": event.current_time,
                            "total_duration": event.total_duration,
                            "fps": event.fps,
                            "speed": event.speed,
                            "frame": event.frame,
                            "eta": event.eta,
                            "status": event.status
                        }
                        tasks[task_id]["status"] = "running"

            result = compression_func(
                on_progress=on_progress,
                cancellation_source=cancel_source,
                **kwargs
            )
            
            with tasks_lock:
                if task_id in tasks:
                    tasks[task_id]["status"] = result.status.value
                    tasks[task_id]["result"] = {
                        "is_success": result.is_success,
                        "output_path": result.output_path,
                        "output_size": result.output_size,
                        "compression_ratio": result.compression_ratio,
                        "error_message": result.error_message
                    }
                    tasks[task_id]["finished_at"] = time.time()

        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()
        
        return task_id

    @app.route("/api/info", methods=["GET"])
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

    @app.route("/api/compress/video", methods=["POST"])
    def start_video_compression():
        data = request.json
        input_path = data.get("input_path")
        if not input_path:
            return jsonify({"error": "input_path is required"}), 400
        
        task_id = _start_task(
            "video", 
            compress_video_service,
            input_path=input_path,
            output_path=data.get("output_path"),
            crf=data.get("crf"),
            preset=data.get("preset"),
            audio_bitrate=data.get("audio_bitrate"),
            audio_enabled=data.get("audio_enabled", True),
            max_fps=data.get("max_fps"),
            resolution=data.get("resolution"),
            volume_gain_db=data.get("volume_gain_db"),
            denoise_level=data.get("denoise_level")
        )
        
        return jsonify({"task_id": task_id})

    @app.route("/api/compress/audio", methods=["POST"])
    def start_audio_compression():
        data = request.json
        input_path = data.get("input_path")
        if not input_path:
            return jsonify({"error": "input_path is required"}), 400
        
        task_id = _start_task(
            "audio",
            compress_audio_service,
            input_path=input_path,
            output_path=data.get("output_path"),
            bitrate=data.get("bitrate"),
            volume_gain_db=data.get("volume_gain_db"),
            denoise_level=data.get("denoise_level"),
            keep_metadata=data.get("keep_metadata", True)
        )
        
        return jsonify({"task_id": task_id})

    @app.route("/api/status/<task_id>", methods=["GET"])
    def get_status(task_id):
        with tasks_lock:
            task = tasks.get(task_id)
            if not task:
                return jsonify({"error": "Task not found"}), 404
            
            return jsonify({
                "id": task["id"],
                "status": task["status"],
                "progress": task["progress"],
                "result": task["result"],
                "type": task["type"]
            })

    @app.route("/api/cancel/<task_id>", methods=["POST"])
    def cancel_task(task_id):
        with tasks_lock:
            task = tasks.get(task_id)
            if not task:
                return jsonify({"error": "Task not found"}), 404
            
            task["cancel_source"].cancel()
            return jsonify({"status": "cancelling"})

    @app.route("/api/tasks", methods=["GET"])
    def list_tasks():
        with tasks_lock:
            return jsonify([
                {
                    "id": t["id"],
                    "status": t["status"],
                    "type": t["type"]
                } for t in tasks.values()
            ])

    return app
