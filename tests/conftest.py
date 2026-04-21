import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def reset_singletons():
    from video_compressor.gui.i18n.translations import TranslationManager
    from video_compressor.gui.utils import SettingsManager

    TranslationManager.reset_instance()
    SettingsManager.reset_instance()
    yield
    TranslationManager.reset_instance()
    SettingsManager.reset_instance()


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def settings_manager(tmp_dir):
    from video_compressor.gui.utils import SettingsManager

    SettingsManager.reset_instance()
    with patch("video_compressor.gui.utils.get_config_dir", return_value=tmp_dir):
        mgr = SettingsManager.get_instance()
        yield mgr
    SettingsManager.reset_instance()


@pytest.fixture
def translation_manager(settings_manager):
    from video_compressor.gui.i18n.translations import TranslationManager

    TranslationManager.reset_instance()
    env = {k: v for k, v in os.environ.items() if k != "AME_LANGUAGE"}
    with patch.dict(os.environ, env, clear=True):
        mgr = TranslationManager()
        TranslationManager._instance = mgr
        yield mgr
    TranslationManager.reset_instance()


@pytest.fixture
def sample_video_files(tmp_dir):
    files = []
    for name in ["video.mp4", "movie.mkv", "clip.avi", "film.mov"]:
        p = tmp_dir / name
        p.write_text("")
        files.append(p)
    return files


@pytest.fixture
def sample_audio_files(tmp_dir):
    files = []
    for name in ["song.mp3", "track.wav", "audio.flac", "music.aac"]:
        p = tmp_dir / name
        p.write_text("")
        files.append(p)
    return files
