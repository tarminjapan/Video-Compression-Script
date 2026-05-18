from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from backend.api.app import create_app
from backend.api.job_runner import job_runner
from backend.settings import SettingsManager
from flask.testing import FlaskClient


@pytest.fixture
def client(settings_manager: SettingsManager) -> Generator[FlaskClient, None, None]:
    _ = settings_manager
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        with job_runner.tasks_lock:
            job_runner.tasks.clear()
        yield client


def test_full_video_compression_flow(client: FlaskClient) -> None:
    """Test the full flow of video compression from the API perspective.
    1. Start a video compression job.
    2. Check the job status (should be pending or running).
    3. Simulate job completion.
    4. Check the final status and results.
    """
    mock_executor = MagicMock()
    mock_result = MagicMock()
    mock_result.status.value = "success"
    mock_result.is_success = True
    mock_result.output_path = "output.mp4"
    mock_result.output_size = 500000
    mock_result.compression_ratio = 0.45
    mock_result.error_message = None

    with (
        patch("backend.api.blueprints.jobs.Path.exists", return_value=True),
        patch("backend.api.blueprints.jobs.compress_video_service", return_value=mock_result),
        patch.object(job_runner, "executor", mock_executor),
    ):
        response = client.post(
            "/api/jobs/video", json={"input_path": "input.mp4", "crf": 28, "preset": 8}
        )
        assert response.status_code == 202
        task_id = response.get_json()["task_id"]

        response = client.get(f"/api/jobs/{task_id}")
        assert response.get_json()["status"] == "pending"

        assert mock_executor.submit.called, "Task was not submitted"

        run_task_func = mock_executor.submit.call_args[0][0]
        run_task_func()

        response = client.get(f"/api/jobs/{task_id}")
        assert response.status_code == 200
        assert response.get_json()["status"] == "success"
        assert response.get_json()["result"]["output_path"] == "output.mp4"
        assert response.get_json()["result"]["compression_ratio"] == 0.45


def test_job_cancellation_flow(client: FlaskClient) -> None:
    """Test the flow of cancelling a job."""
    with (
        patch("backend.api.blueprints.jobs.Path.exists", return_value=True),
        patch("backend.api.blueprints.jobs.compress_video_service"),
        patch.object(job_runner, "executor", MagicMock()),
    ):
        # Start job
        response = client.post("/api/jobs/video", json={"input_path": "input.mp4"})
        task_id = response.get_json()["task_id"]

        # Cancel job
        response = client.delete(f"/api/jobs/{task_id}")
        assert response.status_code == 200
        assert response.get_json()["status"] == "cancelling"

        # Verify status in job runner
        response = client.get(f"/api/jobs/{task_id}")
        assert response.get_json()["status"] == "cancelling"


def test_settings_persistence_integration(client: FlaskClient) -> None:
    """Test that settings updated via API are reflected in subsequent calls."""
    # Update settings
    update_data = {
        "language": "ja",
        "ffmpeg_path": "",
        "default_output_dir": "test_output",
    }
    client.post("/api/settings", json=update_data)

    # Get settings and verify
    response = client.get("/api/settings")
    assert response.get_json()["language"] == "ja"
    assert response.get_json()["ffmpeg_path"] == ""
    assert response.get_json()["default_output_dir"] == "test_output"
