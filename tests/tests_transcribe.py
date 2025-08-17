import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

import cli

app = cli.cli


class DummyModel:
    def transcribe(self, video_path, language="en"):
        return {"segments": [{"start": 0.0, "end": 1.0, "text": "Hello world"}]}


@pytest.fixture(autouse=True)
def patch_whisper_default(monkeypatch):
    monkeypatch.setattr(cli.whisper, "load_model", lambda m: DummyModel())


@pytest.fixture
def runner():
    return CliRunner()


def test_transcribe_creates_srt_and_clean(tmp_path, runner):
    video = tmp_path / "fake.mp4"
    video.write_text("dummy video")
    srt_out = tmp_path / "out.srt"
    result = runner.invoke(app, ["transcribe", str(video), "--output", str(srt_out), "--clean"])
    assert result.exit_code == 0
    assert srt_out.exists()
    assert srt_out.with_suffix(".txt").exists()


def test_transcribe_invalid_file_format(runner, tmp_path):
    txt_file = tmp_path / "not_a_video.txt"
    txt_file.write_text("This is not a video.")
    result = runner.invoke(app, ["transcribe", str(txt_file)])
    assert result.exit_code != 0
    assert "Invalid video format" in result.output


@patch("cli.whisper.load_model")
def test_transcribe_command_success(mock_load_model, runner, tmp_path):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"segments": [{"start": 0, "end": 1, "text": "Test"}]}
    mock_load_model.return_value = mock_model

    video_path = tmp_path / "dummy.mp4"
    video_path.write_bytes(b"\x00\x00\x00\x20ftyp")
    output_path = tmp_path / "out.srt"

    result = runner.invoke(
        app, ["transcribe", str(video_path), "--output", str(output_path), "--language", "en"]
    )
    assert result.exit_code == 0
    assert "Transcription complete." in result.output


@patch("cli.whisper.load_model")
def test_transcribe_creates_srt_file(mock_load_model, runner, tmp_path):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [
            {"start": 0, "end": 1, "text": "Hello World"},
            {"start": 1, "end": 2, "text": "Testing subtitles"},
        ]
    }
    mock_load_model.return_value = mock_model

    with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_video:
        output_path = Path(temp_video.name).with_suffix(".srt")
        result = runner.invoke(
            app, ["transcribe", temp_video.name, "--model", "base", "--language", "en", "--output", str(output_path)]
        )
        assert result.exit_code == 0, result.output
        assert output_path.exists()
        data = output_path.read_text(encoding="utf-8")
        assert "Hello World" in data and "Testing subtitles" in data


@pytest.mark.xfail(reason="If you allow .txt for transcribe output, keep this xfail.")
def test_transcribe_should_reject_txt(tmp_path):
    video = tmp_path / "fake.mp4"
    video.write_text("vid")
    runner = CliRunner()
    result = runner.invoke(app, ["transcribe", str(video), "--output", "wrong.txt"])
    assert result.exit_code != 0
    assert "must end with" in result.output


def test_transcribe_nonexistent_file(runner):
    result = runner.invoke(app, ["transcribe", "nonexistent.mp4"])
    assert result.exit_code != 0
    assert "Invalid value for 'VIDEO_PATH'" in result.output


def test_transcribe_rejects_invalid_extension(runner, tmp_path):
    bad = tmp_path / "not_video.txt"
    bad.write_text("hi")
    res = runner.invoke(app, ["transcribe", str(bad)])
    assert res.exit_code != 0
    assert "Invalid video format" in res.output


@patch("cli.whisper.load_model")
def test_transcribe_writes_srt_numbering_and_timestamps(mock_load, runner, tmp_path):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [
            {"start": 0.0, "end": 1.25, "text": "Hello"},
            {"start": 1.25, "end": 2.5, "text": "World"},
        ]
    }
    mock_load.return_value = mock_model

    video = tmp_path / "v.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")
    out = tmp_path / "o.srt"
    res = runner.invoke(app, ["transcribe", str(video), "--output", str(out)])
    assert res.exit_code == 0
    data = out.read_text()
    assert "1\n" in data and "2\n" in data
    assert "00:00:00,000 --> 00:00:01,250" in data
    assert "00:00:01,250 --> 00:00:02,500" in data
    assert "Hello" in data and "World" in data


@patch("cli.whisper.load_model", side_effect=RuntimeError("GPU missing"))
def test_transcribe_handles_whisper_failure(mock_load, runner, tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")
    out = tmp_path / "o.srt"
    res = runner.invoke(app, ["transcribe", str(video), "--output", str(out)])
    assert res.exit_code != 0


@patch("cli.whisper.load_model")
def test_transcribe_passes_model_name(mock_load, runner, tmp_path):
    mock_load.return_value = MagicMock(transcribe=lambda *a, **k: {"segments": []})
    video = tmp_path / "v.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")
    out = tmp_path / "o.srt"
    runner.invoke(app, ["transcribe", str(video), "--model", "small", "--output", str(out)])
    mock_load.assert_called_with("small")
