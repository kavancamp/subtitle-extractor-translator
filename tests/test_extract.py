import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from click.testing import CliRunner

import cli as cli_module

app = cli_module.cli
TEST_VIDEO_PATH = "../baldursGate.mp4"
SRT_FILE = "test_output.srt"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.mark.skipif(not os.path.exists(TEST_VIDEO_PATH), reason="Test video not available")
def test_extract_command_success(runner):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / SRT_FILE
        result = runner.invoke(app, ["extract", TEST_VIDEO_PATH, "--output", str(output_path)])
        assert result.exit_code == 0
        assert output_path.exists()


def test_extract_missing_file_error(runner):
    result = runner.invoke(app, ["extract", "nonexistent.mp4"])
    assert result.exit_code != 0
    assert "Invalid value for 'VIDEO_PATH'" in result.output or "does not exist" in result.output


def test_extract_help(runner):
    result = runner.invoke(app, ["extract", "--help"])
    assert result.exit_code == 0
    # your CLI text: "- Extract subtitles from video; fallback to transcription"
    assert "Extract subtitles from video" in result.output
    assert "fallback to transcription" in result.output


def test_extract_invalid_file_format(runner, tmp_path):
    txt_file = tmp_path / "not_a_video.txt"
    txt_file.write_text("This is not a video.")
    result = runner.invoke(app, ["extract", str(txt_file)])
    assert result.exit_code != 0
    assert "Invalid video format" in result.output


@patch("cli.whisper.load_model")
@patch("cli.subprocess.run", side_effect=subprocess.CalledProcessError(1, "ffmpeg"))
@patch("cli.has_subtitles", return_value=True)
def test_ffmpeg_extraction_failure(mock_has_subs, mock_run, mock_whisper, runner, tmp_path):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"segments": [{"start": 0, "end": 1, "text": "Fallback"}]}
    mock_whisper.return_value = mock_model

    video = tmp_path / "test.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")
    out = tmp_path / "out.srt"

    result = runner.invoke(app, ["extract", str(video), "--output", str(out)])
    assert result.exit_code == 0
    assert "Falling back to transcription" in result.output


@patch("cli.whisper.load_model")
@patch("cli.has_subtitles", return_value=False)
def test_extract_fallback_transcribe_clean(mock_has, mock_load, runner, tmp_path):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"segments": [{"start": 0.0, "end": 0.8, "text": "fallback clean"}]}
    mock_load.return_value = mock_model

    video = tmp_path / "v.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")
    out = tmp_path / "plain.txt"

    res = runner.invoke(app, ["extract", str(video), "--output", str(out), "--clean"])
    assert res.exit_code == 0, res.output
    data = out.read_text(encoding="utf-8")
    assert "fallback clean" in data
    assert "-->" not in data


@patch("cli.subprocess.run")
@patch("cli.has_subtitles", return_value=True)
def test_extract_clean_converts_existing_srt_to_txt(mock_has, mock_run, runner, tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")

    out_srt = tmp_path / "out.srt"
    out_srt.write_text(
        "1\n00:00:00,000 --> 00:00:00,500\nHi\n\n2\n00:00:00,500 --> 00:00:01,000\nThere\n",
        encoding="utf-8",
    )

    res = runner.invoke(app, ["extract", str(video), "--output", str(out_srt), "--clean"])
    assert res.exit_code == 0, res.output

    out_txt = tmp_path / "out.txt"
    assert out_txt.exists()
    txt = out_txt.read_text(encoding="utf-8")
    assert "Hi" in txt and "There" in txt
    assert "-->" not in txt


@patch("cli.subprocess.run")
@patch("cli.has_subtitles", return_value=True)
@patch("cli.whisper.load_model")  # should not be called
def test_extract_prefers_ffmpeg_when_subs_present(mock_whisper, mock_has_subs, mock_run, runner, tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")
    out = tmp_path / "out.srt"
    res = runner.invoke(app, ["extract", str(video), "--output", str(out)])
    assert res.exit_code == 0
    mock_run.assert_called_once()
    assert not mock_whisper.called


@patch("cli.whisper.load_model")
@patch("cli.subprocess.run", side_effect=subprocess.CalledProcessError(1, "ffmpeg"))
@patch("cli.has_subtitles", return_value=True)
def test_extract_fallback_calls_whisper(mock_has, mock_run, mock_load, runner, tmp_path):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"segments": [{"start": 0, "end": 1, "text": "fallback"}]}
    mock_load.return_value = mock_model

    video = tmp_path / "v.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")
    out = tmp_path / "out.srt"
    res = runner.invoke(app, ["extract", str(video), "--output", str(out)])
    assert res.exit_code == 0
    assert out.exists()
    assert "fallback" in out.read_text()


def test_extract_invalid_extension_blocks_early(runner, tmp_path):
    bad = tmp_path / "clip.doc"
    bad.write_text("nope")
    res = runner.invoke(app, ["extract", str(bad)])
    assert res.exit_code != 0
    assert "Invalid video format" in res.output
