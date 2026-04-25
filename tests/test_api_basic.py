import time
import pytest
from unittest.mock import patch, MagicMock
from video_compressor.api.app import create_app
from video_compressor.api.job_runner import job_runner

@pytest.fixture
def client(settings_manager):
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client

def test_api_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"

def test_api_media_info_endpoint(client):
    with patch("video_compressor.api.blueprints.media.Path.exists", return_value=True), \
         patch("video_compressor.api.blueprints.media.get_video_info_safe", return_value={"width": 1920, "height": 1080}):
        response = client.get("/api/media-info?path=test.mp4")
        assert response.status_code == 200
        assert response.json["width"] == 1920
        assert response.json["type"] == "video"

def test_start_task_adds_timestamp(client):
    with patch("video_compressor.api.blueprints.jobs.compress_video_service"), \
         patch("threading.Thread"):
        # Clear tasks for clean test
        with job_runner.tasks_lock:
            job_runner.tasks.clear()
            
        response = client.post("/api/jobs/video", json={"input_path": "test.mp4"})
        assert response.status_code == 202
        task_id = response.json["task_id"]
        
        with job_runner.tasks_lock:
            assert task_id in job_runner.tasks
            assert "created_at" in job_runner.tasks[task_id]
            assert isinstance(job_runner.tasks[task_id]["created_at"], float)

def test_task_completion_adds_finished_at(client):
    mock_result = MagicMock()
    mock_result.status.value = "success"
    mock_result.is_success = True
    mock_result.output_path = "out.mp4"
    mock_result.output_size = 1000
    mock_result.compression_ratio = 0.5
    mock_result.error_message = None

    with patch("video_compressor.api.blueprints.jobs.compress_video_service", return_value=mock_result), \
         patch("threading.Thread") as mock_thread:
        
        with job_runner.tasks_lock:
            job_runner.tasks.clear()

        client.post("/api/jobs/video", json={"input_path": "test.mp4"})
        
        # Get the run_task function from the Thread call
        run_task_func = mock_thread.call_args[1]["target"]
        run_task_func()
        
        # Now check if finished_at is set
        with job_runner.tasks_lock:
            task_id = list(job_runner.tasks.keys())[0]
            assert "finished_at" in job_runner.tasks[task_id]
            assert isinstance(job_runner.tasks[task_id]["finished_at"], float)

def test_cancel_task(client):
    with patch("video_compressor.api.blueprints.jobs.compress_video_service"), \
         patch("threading.Thread"):
        
        with job_runner.tasks_lock:
            job_runner.tasks.clear()

        response = client.post("/api/jobs/video", json={"input_path": "test.mp4"})
        task_id = response.json["task_id"]
        
        response = client.delete(f"/api/jobs/{task_id}")
        assert response.status_code == 200
        assert response.json["status"] == "cancelling"
