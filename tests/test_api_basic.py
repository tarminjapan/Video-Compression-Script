import time
import pytest
from unittest.mock import patch, MagicMock
from video_compressor.api.app import create_app, tasks, tasks_lock

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_api_info_endpoint(client):
    with patch("video_compressor.api.app.Path.exists", return_value=True), \
         patch("video_compressor.api.app.get_video_info_safe", return_value={"width": 1920, "height": 1080}):
        response = client.get("/api/info?path=test.mp4")
        assert response.status_code == 200
        assert response.json["width"] == 1920
        assert response.json["type"] == "video"

def test_start_task_adds_timestamp(client):
    with patch("video_compressor.api.app.compress_video_service"), \
         patch("threading.Thread"):
        # Clear tasks for clean test
        with tasks_lock:
            tasks.clear()
            
        response = client.post("/api/compress/video", json={"input_path": "test.mp4"})
        assert response.status_code == 200
        task_id = response.json["task_id"]
        
        with tasks_lock:
            assert task_id in tasks
            assert "created_at" in tasks[task_id]
            assert isinstance(tasks[task_id]["created_at"], float)

def test_task_completion_adds_finished_at(client):
    mock_result = MagicMock()
    mock_result.status.value = "success"
    mock_result.is_success = True
    mock_result.output_path = "out.mp4"
    mock_result.output_size = 1000
    mock_result.compression_ratio = 0.5
    mock_result.error_message = None

    # We want to test the run_task logic, but it's nested.
    # We can capture the target function of the thread and run it manually.
    with patch("video_compressor.api.app.compress_video_service", return_value=mock_result), \
         patch("threading.Thread") as mock_thread:
        
        with tasks_lock:
            tasks.clear()

        client.post("/api/compress/video", json={"input_path": "test.mp4"})
        
        # Get the run_task function from the Thread call
        run_task_func = mock_thread.call_args[1]["target"]
        run_task_func()
        
        # Now check if finished_at is set
        with tasks_lock:
            task_id = list(tasks.keys())[0]
            assert "finished_at" in tasks[task_id]
            assert isinstance(tasks[task_id]["finished_at"], float)
