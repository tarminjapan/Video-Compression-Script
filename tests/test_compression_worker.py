import time

from video_compressor.gui.compression_worker import CompressionWorker


class TestParseProgress:
    def test_valid_line(self):
        line = "frame=  100 fps=25.0 q=28.0 size=  12345kB time=00:00:04.00 bitrate=25300.0kbits/s speed=1.0x"
        start = time.time() - 1.0
        result = CompressionWorker._parse_progress(line, 10.0, start)
        assert result is not None
        assert result["percent"] == 40.0
        assert result["fps"] == 25.0
        assert result["speed"] == 1.0
        assert result["frame"] == 100

    def test_zero_duration(self):
        line = "time=00:00:04.00"
        result = CompressionWorker._parse_progress(line, 0, time.time())
        assert result is None

    def test_no_time_match(self):
        line = "frame=  100 fps=25.0"
        result = CompressionWorker._parse_progress(line, 10.0, time.time())
        assert result is None

    def test_complete_line(self):
        line = "frame= 500 fps=30.0 q=25.0 size=  50000kB time=00:01:00.00 bitrate=6826.7kbits/s speed=1.5x"
        start = time.time() - 40.0
        result = CompressionWorker._parse_progress(line, 120.0, start)
        assert result is not None
        assert result["percent"] == 50.0
        assert result["fps"] == 30.0
        assert result["speed"] == 1.5

    def test_percent_capped_at_100(self):
        line = "time=00:02:00.00"
        result = CompressionWorker._parse_progress(line, 60.0, time.time())
        assert result is not None
        assert result["percent"] == 100.0

    def test_eta_calculation(self):
        line = "time=00:00:30.00 speed=1.0x"
        start = time.time() - 30.0
        result = CompressionWorker._parse_progress(line, 60.0, start)
        assert result is not None
        assert result["eta"] > 0

    def test_fractional_seconds(self):
        line = "time=00:00:05.50"
        result = CompressionWorker._parse_progress(line, 10.0, time.time())
        assert result is not None
        assert abs(result["current_time"] - 5.5) < 0.1

    def test_hours_minutes_seconds(self):
        line = "time=01:30:45.00"
        result = CompressionWorker._parse_progress(line, 7200.0, time.time())
        assert result is not None
        expected = 1 * 3600 + 30 * 60 + 45
        assert result["current_time"] == expected

    def test_no_fps(self):
        line = "time=00:00:05.00 speed=1.0x"
        result = CompressionWorker._parse_progress(line, 10.0, time.time())
        assert result is not None
        assert result["fps"] == 0.0

    def test_no_speed(self):
        line = "time=00:00:05.00 fps=25.0"
        result = CompressionWorker._parse_progress(line, 10.0, time.time())
        assert result is not None
        assert result["speed"] == 0.0


class TestCompressionWorkerInit:
    def test_initial_state(self):
        worker = CompressionWorker()
        assert worker.is_running is False

    def test_cancel_when_not_running(self):
        worker = CompressionWorker()
        worker.cancel()
        assert not worker.is_running
