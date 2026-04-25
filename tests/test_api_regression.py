import pytest
import time
from unittest.mock import patch, MagicMock
from video_compressor.api.app import create_app
from video_compressor.api.job_runner import job_runner

@pytest.fixture
def client(settings_manager):
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        with job_runner.tasks_lock:
            job_runner.tasks.clear()
        yield client

def test_full_video_compression_flow(client):
    """
    Test the full flow of video compression from the API perspective.
    1. Start a video compression job.
    2. Check the job status (should be pending or running).
    3. Simulate job completion.
    4. Check the final status and results.
    """
    # 1. Start job
    with patch("video_compressor.api.blueprints.jobs.compress_video_service") as mock_service, \
         patch("threading.Thread") as mock_thread:
        
        # Mock service return value
        mock_result = MagicMock()
        mock_result.status.value = "success"
        mock_result.is_success = True
        mock_result.output_path = "output.mp4"
        mock_result.output_size = 500000
        mock_result.compression_ratio = 0.45
        mock_result.error_message = None
        mock_service.return_value = mock_result

        response = client.post("/api/jobs/video", json={
            "input_path": "input.mp4",
            "crf": 28,
            "preset": 8
        })
        assert response.status_code == 202
        task_id = response.json["task_id"]

        # 2. Check initial status
        response = client.get(f"/api/jobs/{task_id}")
        assert response.json["status"] == "pending"

        # 3. Simulate job execution
        # Ensure thread was started
        assert mock_thread.called, "Thread was not started"
        
        # In reality, the job runner starts a thread. We manually run the target function.
        run_task_func = mock_thread.call_args[1]["target"]
        run_task_func()

        # 4. Check final status
        response = client.get(f"/api/jobs/{task_id}")
        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert response.json["result"]["output_path"] == "output.mp4"
        assert response.json["result"]["compression_ratio"] == 0.45

def test_job_cancellation_flow(client):
    """
    Test the flow of cancelling a job.
    """
    with patch("video_compressor.api.blueprints.jobs.compress_video_service"), \
         patch("threading.Thread"):
        
        # Start job
        response = client.post("/api/jobs/video", json={"input_path": "input.mp4"})
        task_id = response.json["task_id"]

        # Cancel job
        response = client.delete(f"/api/jobs/{task_id}")
        assert response.status_code == 200
        assert response.json["status"] == "cancelling"

        # Verify status in job runner
        response = client.get(f"/api/jobs/{task_id}")
        assert response.json["status"] == "cancelling"

def test_settings_persistence_integration(client):
    """
    Test that settings updated via API are reflected in subsequent calls.
    """
    # Update settings
    update_data = {
        "language": "ja",
        "ffmpeg_path": "/usr/local/bin/ffmpeg",
        "default_output_dir": "/tmp/output"
    }
    client.post("/api/settings", json=update_data)

    # Get settings and verify
    response = client.get("/api/settings")
    assert response.json["language"] == "ja"
    assert response.json["ffmpeg_path"] == "/usr/local/bin/ffmpeg"
    assert response.json["default_output_dir"] == "/tmp/output"
