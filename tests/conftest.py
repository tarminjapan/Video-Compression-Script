import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from backend.settings import SettingsManager


@pytest.fixture
def settings_manager(tmp_dir: Path):
    SettingsManager.reset_instance()
    with patch("backend.settings.get_config_dir", return_value=tmp_dir):
        mgr = SettingsManager.get_instance()
        yield mgr
    SettingsManager.reset_instance()


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_video_files(tmp_dir: Path):
    files = []
    for name in ["video.mp4", "movie.mkv", "clip.avi", "film.mov"]:
        p = tmp_dir / name
        p.write_text("")
        files.append(p)
    return files


@pytest.fixture
def sample_audio_files(tmp_dir: Path):
    files = []
    for name in ["song.mp3", "track.wav", "audio.flac", "music.aac"]:
        p = tmp_dir / name
        p.write_text("")
        files.append(p)
    return files
