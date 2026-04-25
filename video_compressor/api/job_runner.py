import threading
import time
import uuid
from collections.abc import Callable
from typing import Any

from ..progress_handler import CancellationSource, ProgressEvent


class JobRunner:
    def __init__(self, max_concurrent_tasks: int = 2):
        self.tasks: dict[str, Any] = {}
        self.tasks_lock = threading.Lock()
        self.semaphore = threading.Semaphore(max_concurrent_tasks)
        self._cleanup_thread_started = False

    def start_cleanup_thread(self):
        if not self._cleanup_thread_started:
            cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            cleanup_thread.start()
            self._cleanup_thread_started = True

    def _cleanup_loop(self):
        """Background thread to clean up old tasks every 10 minutes."""
        while True:
            # Check every 10 minutes
            time.sleep(600)
            now = time.time()
            with self.tasks_lock:
                to_delete = []
                for tid, t in self.tasks.items():
                    # Remove tasks that finished more than 1 hour ago
                    if t.get("status") in ["success", "failed", "cancelled"]:
                        finished_at = t.get("finished_at")
                        if finished_at and (now - finished_at) > 3600:
                            to_delete.append(tid)

                for tid in to_delete:
                    del self.tasks[tid]

    def start_task(self, task_type: str, compression_func: Callable, **kwargs) -> str:
        task_id = str(uuid.uuid4())
        cancel_source = CancellationSource()

        with self.tasks_lock:
            # Basic cleanup if too many tasks (safety limit)
            if len(self.tasks) > 100:
                finished_ids = [
                    tid
                    for tid, t in self.tasks.items()
                    if t["status"] in ["success", "failed", "cancelled"]
                ]
                # Remove first few finished tasks
                for fid in finished_ids[:20]:
                    del self.tasks[fid]

            self.tasks[task_id] = {
                "id": task_id,
                "status": "pending",
                "progress": None,
                "result": None,
                "cancel_source": cancel_source,
                "type": task_type,
                "created_at": time.time(),
            }

        def run_task():
            with self.semaphore:

                def on_progress(event: ProgressEvent):
                    with self.tasks_lock:
                        if task_id in self.tasks:
                            self.tasks[task_id]["progress"] = {
                                "percent": event.percent,
                                "current_time": event.current_time,
                                "total_duration": event.total_duration,
                                "fps": event.fps,
                                "speed": event.speed,
                                "frame": event.frame,
                                "eta": event.eta,
                                "status": event.status,
                            }
                            self.tasks[task_id]["status"] = "running"

                try:
                    result = compression_func(
                        on_progress=on_progress, cancellation_source=cancel_source, **kwargs
                    )

                    with self.tasks_lock:
                        if task_id in self.tasks:
                            self.tasks[task_id]["status"] = result.status.value
                            self.tasks[task_id]["result"] = {
                                "is_success": result.is_success,
                                "output_path": result.output_path,
                                "output_size": result.output_size,
                                "compression_ratio": result.compression_ratio,
                                "error_message": result.error_message,
                            }
                            self.tasks[task_id]["finished_at"] = time.time()
                except Exception as e:
                    with self.tasks_lock:
                        if task_id in self.tasks:
                            self.tasks[task_id]["status"] = "failed"
                            self.tasks[task_id]["result"] = {
                                "is_success": False,
                                "error_message": str(e),
                            }
                            self.tasks[task_id]["finished_at"] = time.time()

        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()

        return task_id

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        with self.tasks_lock:
            return self.tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        with self.tasks_lock:
            task = self.tasks.get(task_id)
            if task:
                task["cancel_source"].cancel()
                return True
        return False

    def list_tasks(self) -> list:
        with self.tasks_lock:
            return [
                {"id": t["id"], "status": t["status"], "type": t["type"]}
                for t in self.tasks.values()
            ]


# Singleton instance
job_runner = JobRunner()
