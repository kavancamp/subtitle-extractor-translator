# -*- coding: utf-8 -*-
import importlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)
import pytest

import cli as cli_module

app = cli_module.cli 

from click.testing import CliRunner

TEST_VIDEO_PATH = "./test.mp4"
SRT_FILE = "test_output.srt"


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_help_default_english(runner):
    # APP_LANG default (en) -> English help text
    result = runner.invoke(app)  
    assert result.exit_code == 0
    assert "Welcome to Subtitle Extractor" in result.output


def test_invalid_language_code_translation(runner, tmp_path):
    srt_file = tmp_path / "test.srt"
    srt_file.write_text("1\n00:00:01,000 --> 00:00:02,000\nHello\n")

    result = runner.invoke(
        app,
        [
            "translate",
            str(srt_file),
            "--target-lang",
            "xx",  # invalid code should error from the translator
            "--output",
            str(tmp_path / "out.srt"),
        ],
    )
    assert result.exit_code != 0 or "Error" in result.output


# def test_cli_help_in_spanish(monkeypatch, runner):
#     # Make help text load in Spanish without reloading the module
#     res = runner.invoke(app, ["--help"], env={"APP_LANG": "es"})
#     assert res.exit_code == 0
#     assert "Transcripción" in res.output



def test_unsupported_lang_falls_back_to_english(runner):
    result = runner.invoke(app, ["--lang", "xx"])
    assert result.exit_code == 0
    assert "Welcome to Subtitle Extractor" in result.output


@pytest.mark.skipif(
    not os.path.exists(TEST_VIDEO_PATH),
    reason="Test video not available",
)
def test_extract_command_success(runner):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / SRT_FILE
        result = runner.invoke(
            app,
            ["extract", TEST_VIDEO_PATH, "--output", str(output_path)],
        )
        assert result.exit_code == 0
        assert output_path.exists()


def test_extract_help(runner):
    result = runner.invoke(app, ["extract", "--help"])
    assert result.exit_code == 0
    assert (
        "- Extract subtitles from video; "
        "fallback to transcribe if none found" in result.output
    )


def test_extract_missing_file_error(runner):
    result = runner.invoke(app, ["extract", "nonexistent.mp4"])
    assert result.exit_code != 0
    assert "Error" in result.output or "does not exist" in result.output


@patch("cli.whisper.load_model")
@patch(
    "cli.subprocess.run",
    side_effect=subprocess.CalledProcessError(1, "ffmpeg"),
)
@patch("cli.has_subtitles", return_value=True)
def test_ffmpeg_extraction_failure(
    mock_has_subs, mock_run, mock_whisper, runner, tmp_path
):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [{"start": 0, "end": 1, "text": "Fallback"}]
    }
    mock_whisper.return_value = mock_model

    video = tmp_path / "test.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")  # dummy header
    out = tmp_path / "out.srt"

    result = runner.invoke(
        app, ["extract", str(video), "--output", str(out)]
    )
    assert result.exit_code == 0
    assert "Falling back to transcription" in result.output


@pytest.mark.skipif(
    not os.path.exists(TEST_VIDEO_PATH),
    reason="Test video not available",
)
def test_extract_invalid_file_format(runner, tmp_path):
    txt_file = tmp_path / "not_a_video.txt"
    txt_file.write_text("This is not a video.")
    result = runner.invoke(app, ["extract", str(txt_file)])
    assert result.exit_code != 0
    assert "Invalid video format" in result.output


def test_transcribe_invalid_file_format(runner, tmp_path):
    txt_file = tmp_path / "not_a_video.txt"
    txt_file.write_text("This is not a video.")
    result = runner.invoke(app, ["transcribe", str(txt_file)])
    assert result.exit_code != 0
    assert "Invalid video format" in result.output


@patch("cli.whisper.load_model")
def test_transcribe_command_success(mock_load_model, runner, tmp_path):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [{"start": 0, "end": 1, "text": "Test"}]
    }
    mock_load_model.return_value = mock_model

    video_path = tmp_path / "dummy.mp4"
    video_path.write_bytes(b"\x00\x00\x00\x20ftyp")
    output_path = tmp_path / "out.srt"

    result = runner.invoke(
        app,
        [
            "transcribe",
            str(video_path),
            "--output",
            str(output_path),
            "--language",
            "en",
        ],
    )
    assert result.exit_code == 0
    assert "Transcription complete." in result.output


@patch("cli.has_subtitles", return_value=False)
@patch("cli.whisper.load_model")
def test_extract_falls_back_to_transcribe(
    mock_load_model, mock_has_subtitles
):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [
            {"start": 0, "end": 1, "text": "Fallback transcription"}
        ]
    }
    mock_load_model.return_value = mock_model

    runner = CliRunner()
    with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_video:
        output_path = temp_video.name + ".srt"
        result = runner.invoke(
            app,
            [
                "extract",
                temp_video.name,
                "--output",
                output_path,
            ],
        )
        assert result.exit_code == 0
        with open(output_path, "r", encoding="utf-8") as f:
            assert "Fallback transcription" in f.read()


def test_transcribe_help(runner):
    result = runner.invoke(app, ["transcribe", "--help"])
    assert result.exit_code == 0
    assert "- Transcribe subtitles from video or audio" in result.output


@patch("cli.whisper.load_model")
def test_transcribe_creates_srt_file(mock_load_model, runner):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [
            {"start": 0, "end": 1, "text": "Hello World"},
            {"start": 1, "end": 2, "text": "Testing subtitles"},
        ]
    }
    mock_load_model.return_value = mock_model

    with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_video:
        output_path = temp_video.name + ".srt"
        result = runner.invoke(
            app,
            [
                "transcribe",
                temp_video.name,
                "--model",
                "base",
                "--language",
                "en",
                "--output",
                output_path,
            ],
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Hello World" in content
            assert "Testing subtitles" in content


@patch("cli.whisper.load_model")
def test_transcribe_output_with_no_extension(mock_load_model, runner):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [{"start": 0, "end": 1, "text": "Hello"}]
    }
    mock_load_model.return_value = mock_model

    with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_video:
        output_path = temp_video.name + "_output"
        result = runner.invoke(
            app,
            ["transcribe", temp_video.name, "--output", output_path],
        )
        assert result.exit_code == 0
        assert os.path.exists(output_path)


@patch("cli.whisper.load_model")
@patch(
    "cli.open", side_effect=PermissionError("Mocked permission denied")
)
def test_transcribe_invalid_output_path(
    mock_open, mock_load_model, runner, tmp_path
):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [{"start": 0, "end": 1, "text": "Test"}]
    }
    mock_load_model.return_value = mock_model

    video_path = tmp_path / "dummy.mp4"
    video_path.write_bytes(b"\x00\x00\x00\x20ftyp")

    output_path = tmp_path / "readonly_dir" / "out.srt"
    output_path.parent.mkdir()

    result = runner.invoke(
        app,
        ["transcribe", str(video_path), "--output", str(output_path)],
    )

    assert result.exit_code != 0
    # Error is wrapped in ClickException with message
    assert "failed to write transcription" in result.output.lower()


@patch("cli.GoogleTranslator.translate")
def test_translate_srt_file(mock_translate):
    mock_translate.side_effect = lambda text: f"TRANSLATED: {text}"
    runner = CliRunner()

    srt_content = """1
00:00:01,000 --> 00:00:02,000
Hello

2
00:00:03,000 --> 00:00:04,000
How are you?
"""

    with tempfile.NamedTemporaryFile(
        "w+", suffix=".srt", delete=False
    ) as temp_in:
        temp_in.write(srt_content)
        temp_in.flush()

        output_path = temp_in.name.replace(".srt", "_fr.srt")
        result = runner.invoke(app,
            [
                "translate",
                temp_in.name,
                "--target-lang",
                "fr",
                "--output",
                output_path,
            ],
        )
        assert result.exit_code == 0
        assert "Translating" in result.output
        assert os.path.exists(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "TRANSLATED: Hello" in content
            assert "TRANSLATED: How are you?" in content


def test_transcribe_nonexistent_file(runner):
    result = runner.invoke(app, ["transcribe", "nonexistent.mp4"])
    assert result.exit_code != 0
    assert "Invalid value for 'VIDEO_PATH'" in result.output


def test_translate_missing_required_args(runner):
    result = runner.invoke(app, ["translate"])
    assert result.exit_code != 0
    assert "Missing argument 'SRT_FILE'" in result.output


def test_cli_accepts_lang_option(runner):
    result = runner.invoke(app, ["--lang", "fr"])
    assert result.exit_code == 0
    assert "Welcome to Subtitle Extractor" in result.output


def test_transcribe_rejects_invalid_extension(runner, tmp_path):
    bad = tmp_path / "not_video.txt"
    bad.write_text("hi")
    res = runner.invoke(app, ["transcribe", str(bad)])
    assert res.exit_code != 0
    assert "Invalid video format" in res.output


@patch("cli.subprocess.run")
@patch("cli.has_subtitles", return_value=True)
@patch("cli.whisper.load_model")  # should not be called
def test_extract_prefers_ffmpeg_when_subs_present(
    mock_whisper, mock_has_subs, mock_run, runner, tmp_path
):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")
    out = tmp_path / "out.srt"
    res = runner.invoke(app, ["extract", str(video), "--output", str(out)]
    )
    assert res.exit_code == 0
    mock_run.assert_called_once()  # ffmpeg invoked
    assert not mock_whisper.called  # Whisper not used



@patch("cli.whisper.load_model")
@patch(
    "cli.subprocess.run",
    side_effect=subprocess.CalledProcessError(1, "ffmpeg"),
)
@patch("cli.has_subtitles", return_value=True)
def test_extract_fallback_calls_whisper(
    mock_has, mock_run, mock_load, runner, tmp_path
):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [{"start": 0, "end": 1, "text": "fallback"}]
    }
    mock_load.return_value = mock_model

    video = tmp_path / "v.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")
    out = tmp_path / "out.srt"
    res = runner.invoke(app, ["extract", str(video), "--output", str(out)]
    )
    assert res.exit_code == 0
    assert out.exists()
    assert "fallback" in out.read_text()


@patch("cli.whisper.load_model")
def test_transcribe_writes_srt_numbering_and_timestamps(
    mock_load, runner, tmp_path
):
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
    res = runner.invoke(app, ["transcribe", str(video), "--output", str(out)]
    )
    assert res.exit_code == 0
    data = out.read_text()
    assert "1\n" in data and "2\n" in data
    assert "00:00:00,000 --> 00:00:01,250" in data
    assert "00:00:01,250 --> 00:00:02,500" in data
    assert "Hello" in data and "World" in data


from unittest.mock import patch


@patch("cli.GoogleTranslator.translate")
def test_translate_preserves_srt_structure(
    mock_translate, runner, tmp_path
):
    mock_translate.side_effect = (
        lambda s: f"X-{s}"
    )  # mark translated text
    srt = tmp_path / "in.srt"
    srt.write_text(
        "1\n00:00:01,000 --> 00:00:02,000\nHello\n\n"
        "2\n00:00:02,500 --> 00:00:03,000\nWorld\n"
    )
    out = tmp_path / "out.srt"
    res = runner.invoke(app,
        [
            "translate",
            str(srt),
            "--target-lang",
            "fr",
            "--output",
            str(out),
        ],
    )
    assert res.exit_code == 0
    data = out.read_text()
    assert "1" in data and "2" in data
    assert "00:00:01,000 --> 00:00:02,000" in data
    assert "X-Hello" in data and "X-World" in data


@patch(
    "cli.GoogleTranslator.translate", side_effect=Exception("bad lang")
)
def test_translate_handles_translator_failure(
    mock_translate, runner, tmp_path
):
    srt = tmp_path / "in.srt"
    srt.write_text("1\n00:00:01,000 --> 00:00:02,000\nHello\n")
    out = tmp_path / "out.srt"
    res = runner.invoke(app,
        [
            "translate",
            str(srt),
            "--target-lang",
            "xx",
            "--output",
            str(out),
        ],
    )
    assert (
        res.exit_code != 0
    )  # or check for ClickException message if you raise one


@patch(
    "cli.whisper.load_model", side_effect=RuntimeError("GPU missing")
)
def test_transcribe_handles_whisper_failure(runner, tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")
    out = tmp_path / "o.srt"
    res = runner.invoke(app, ["transcribe", str(video), "--output", str(out)]
    )
    assert res.exit_code != 0


def test_extract_invalid_extension_blocks_early(runner, tmp_path):
    bad = tmp_path / "clip.doc"
    bad.write_text("nope")
    res = runner.invoke(app, ["extract", str(bad)])
    assert res.exit_code != 0
    assert "Invalid video format" in res.output


@patch("cli.whisper.load_model")
def test_transcribe_passes_model_name(mock_load, runner, tmp_path):
    mock_load.return_value = MagicMock(
        transcribe=lambda *a, **k: {"segments": []}
    )
    video = tmp_path / "v.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")
    out = tmp_path / "o.srt"
    runner.invoke(
        app,
        [
            "transcribe",
            str(video),
            "--model",
            "small",
            "--output",
            str(out),
        ],
    )
    mock_load.assert_called_with("small")


def test_lang_option_accepts_arbitrary_lang():
    r = CliRunner().invoke(app, ["--lang", "de"])
    assert r.exit_code == 0
    assert "Welcome to Subtitle Extractor" in r.output
