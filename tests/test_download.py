"""Tests for wr_analyzer.download."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wr_analyzer.download import download_video, extract_video_id


# ---------------------------------------------------------------------------
# extract_video_id
# ---------------------------------------------------------------------------

class TestExtractVideoId:
    """Pure logic — no network calls."""

    def test_full_url(self):
        assert extract_video_id("https://www.youtube.com/watch?v=JjoDryfoCGs") == "JjoDryfoCGs"

    def test_full_url_with_extra_params(self):
        assert extract_video_id("https://www.youtube.com/watch?v=JjoDryfoCGs&t=120") == "JjoDryfoCGs"

    def test_short_url(self):
        assert extract_video_id("https://youtu.be/JjoDryfoCGs") == "JjoDryfoCGs"

    def test_short_url_with_query(self):
        assert extract_video_id("https://youtu.be/JjoDryfoCGs?t=30") == "JjoDryfoCGs"

    def test_mobile_url(self):
        assert extract_video_id("https://m.youtube.com/watch?v=JjoDryfoCGs") == "JjoDryfoCGs"

    def test_bare_id(self):
        assert extract_video_id("JjoDryfoCGs") == "JjoDryfoCGs"

    def test_local_path_returns_none(self):
        assert extract_video_id("videos/JjoDryfoCGs.mp4") is None

    def test_absolute_path_returns_none(self):
        assert extract_video_id("/home/user/video.mp4") is None

    def test_relative_path_returns_none(self):
        assert extract_video_id("./my-video.mp4") is None

    def test_random_string_returns_none(self):
        assert extract_video_id("not-a-video-id-too-long") is None

    def test_empty_string_returns_none(self):
        assert extract_video_id("") is None

    def test_youtube_url_missing_v_param(self):
        assert extract_video_id("https://www.youtube.com/watch") is None

    def test_bare_id_with_hyphens_underscores(self):
        assert extract_video_id("abc-_DE1234") == "abc-_DE1234"


# ---------------------------------------------------------------------------
# download_video
# ---------------------------------------------------------------------------

class TestDownloadVideo:
    """Tests that don't hit the network — yt-dlp is mocked."""

    def test_returns_cached_file(self, tmp_path: Path):
        """If the file already exists, skip download and return it."""
        cached = tmp_path / "JjoDryfoCGs.mp4"
        cached.write_bytes(b"fake video data")

        progress: list[str] = []
        result = download_video(
            "JjoDryfoCGs", tmp_path, on_progress=progress.append,
        )

        assert result == cached
        assert any("cached" in m.lower() or "Using" in m for m in progress)

    @patch("wr_analyzer.download.yt_dlp.YoutubeDL")
    def test_downloads_when_not_cached(self, mock_ydl_cls: MagicMock, tmp_path: Path):
        """When no cached file, yt-dlp should be invoked."""
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Simulate yt-dlp creating the file on download.
        output_path = tmp_path / "abc12345678.mp4"

        def fake_download(urls):
            output_path.write_bytes(b"downloaded")

        mock_ydl.download.side_effect = fake_download

        result = download_video("abc12345678", tmp_path)

        assert result == output_path
        mock_ydl.download.assert_called_once()
        # Verify the URL passed to yt-dlp.
        url_arg = mock_ydl.download.call_args[0][0][0]
        assert "abc12345678" in url_arg

    @patch("wr_analyzer.download.yt_dlp.YoutubeDL")
    def test_passes_resolution(self, mock_ydl_cls: MagicMock, tmp_path: Path):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.download.side_effect = lambda _: (tmp_path / "abc12345678.mp4").write_bytes(b"v")

        download_video("abc12345678", tmp_path, resolution=720)

        # Check the format string contains the resolution.
        opts = mock_ydl_cls.call_args[0][0]
        assert "720" in opts["format"]

    @patch("wr_analyzer.download.yt_dlp.YoutubeDL")
    def test_cleans_up_on_failure(self, mock_ydl_cls: MagicMock, tmp_path: Path):
        """Partial file should be removed when download raises."""
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        output_path = tmp_path / "abc12345678.mp4"

        def failing_download(urls):
            output_path.write_bytes(b"partial")
            raise Exception("network error")

        mock_ydl.download.side_effect = failing_download

        with pytest.raises(RuntimeError, match="Download failed"):
            download_video("abc12345678", tmp_path)

        assert not output_path.exists(), "Partial file should be cleaned up"

    @patch("wr_analyzer.download.yt_dlp.YoutubeDL")
    def test_time_range_passed(self, mock_ydl_cls: MagicMock, tmp_path: Path):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.download.side_effect = lambda _: (tmp_path / "abc12345678.mp4").write_bytes(b"v")

        download_video("abc12345678", tmp_path, start_time=60.0, end_time=120.0)

        opts = mock_ydl_cls.call_args[0][0]
        assert "download_ranges" in opts

    def test_creates_output_dir(self, tmp_path: Path):
        """output_dir should be created if it doesn't exist."""
        nested = tmp_path / "a" / "b" / "c"
        cached = nested / "JjoDryfoCGs.mp4"

        # Pre-create the file so we don't actually download.
        nested.mkdir(parents=True)
        cached.write_bytes(b"fake")

        result = download_video("JjoDryfoCGs", nested)
        assert result == cached
