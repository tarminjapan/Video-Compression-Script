import pytest
from unittest.mock import patch, MagicMock
from video_compressor.api.app import create_app
from video_compressor.api.job_runner import job_runner
from pathlib import Path

@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        # Clear tasks for clean test
        with job_runner.tasks_lock:
            job_runner.tasks.clear()
        yield client

def test_get_settings(client):
    response = client.get("/api/settings")
    assert response.status_code == 200
    assert "language" in response.json
    assert "appearance_mode" in response.json

def test_update_settings(client):
    new_settings = {"language": "ja", "appearance_mode": "dark"}
    response = client.post("/api/settings", json=new_settings)
    assert response.status_code == 200
    assert response.json["status"] == "success"
    
    # Verify changes
    response = client.get("/api/settings")
    assert response.json["language"] == "ja"
    assert response.json["appearance_mode"] == "dark"

def test_audio_compression_endpoint(client):
    with patch("video_compressor.api.blueprints.jobs.compress_audio_service"), \
         patch("threading.Thread"):
        
        response = client.post("/api/jobs/audio", json={"input_path": "test.mp3", "bitrate": "128k"})
        assert response.status_code == 202
        assert "task_id" in response.json

def test_list_jobs(client):
    with patch("video_compressor.api.blueprints.jobs.compress_video_service"), \
         patch("threading.Thread"):
        
        client.post("/api/jobs/video", json={"input_path": "test1.mp4"})
        client.post("/api/jobs/video", json={"input_path": "test2.mp4"})
        
        response = client.get("/api/jobs")
        assert response.status_code == 200
        assert len(response.json) == 2

def test_get_job_status(client):
    with patch("video_compressor.api.blueprints.jobs.compress_video_service"), \
         patch("threading.Thread"):
        
        resp = client.post("/api/jobs/video", json={"input_path": "test.mp4"})
        task_id = resp.json["task_id"]
        
        response = client.get(f"/api/jobs/{task_id}")
        assert response.status_code == 200
        assert response.json["id"] == task_id
        assert response.json["status"] == "pending"

def test_get_job_status_not_found(client):
    response = client.get("/api/jobs/non-existent-id")
    assert response.status_code == 404

def test_media_info_audio(client):
    with patch("video_compressor.api.blueprints.media.Path.exists", return_value=True), \
         patch("video_compressor.api.blueprints.media.get_video_info_safe", return_value=None), \
         patch("video_compressor.api.blueprints.media.get_audio_info_safe", return_value={"bitrate": "128k"}):
        
        response = client.get("/api/media-info?path=test.mp3")
        assert response.status_code == 200
        assert response.json["type"] == "audio"
        assert response.json["bitrate"] == "128k"

def test_media_info_not_found(client):
    with patch("video_compressor.api.blueprints.media.Path.exists", return_value=False):
        response = client.get("/api/media-info?path=non-existent.mp4")
        assert response.status_code == 404

def test_analyze_volume_endpoint(client):
    with patch("video_compressor.api.blueprints.media.Path.exists", return_value=True), \
         patch("video_compressor.api.blueprints.media.analyze_volume_level", return_value={"mean_volume": -15.0, "max_volume": -1.0}):
        
        response = client.post("/api/volume/analyze", json={"path": "test.mp4"})
        assert response.status_code == 200
        assert response.json["mean_volume"] == -15.0

def test_analyze_volume_error(client):
    with patch("video_compressor.api.blueprints.media.Path.exists", return_value=True), \
         patch("video_compressor.api.blueprints.media.analyze_volume_level", return_value={"mean_volume": None}):
        
        response = client.post("/api/volume/analyze", json={"path": "test.mp4"})
        assert response.status_code == 500
        assert "error" in response.json
