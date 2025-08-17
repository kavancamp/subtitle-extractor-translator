# -*- coding: utf-8 -*-
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import cli as cli_module  # noqa: E402

app = cli_module.cli


@pytest.fixture
def runner():
    return CliRunner()


@patch("cli.whisper.load_model")
def test_transcribe_clean_writes_plain_text_no_timestamps(mock_load, runner, tmp_path):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [
            {"start": 0.0, "end": 0.5, "text": "hello"},
            {"start": 0.5, "end": 1.0, "text": "world"},
        ]
    }
    mock_load.return_value = mock_model

    video = tmp_path / "v.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp")
    out = tmp_path / "clean.txt"

    res = runner.invoke(app, ["transcribe", str(video), "--output", str(out), "--clean"])
    assert res.exit_code == 0, res.output
    data = out.read_text(encoding="utf-8")
    assert "hello" in data and "world" in data
    assert "-->" not in data
    assert "1\n" not in data


@patch("cli.whisper.load_model")
def test_transcribe_noclean(mock_load, runner, tmp_path):
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
    assert res.exit_code == 0, res.output
    data = out.read_text(encoding="utf-8")
    assert "-->" in data
    assert "1\n" in data and "2\n" in data
    assert "Hello" in data and "World" in data


@patch("cli.GoogleTranslator.translate")
def test_translate_srt_file(mock_translate, runner):
    mock_translate.side_effect = lambda text: f"TRANSLATED: {text}"
    srt_content = """1
00:00:01,000 --> 00:00:02,000
Hello

2
00:00:03,000 --> 00:00:04,000
How are you?
"""
    with tempfile.NamedTemporaryFile("w+", suffix=".srt", delete=False) as temp_in:
        temp_in.write(srt_content)
        temp_in.flush()

        output_path = temp_in.name.replace(".srt", "_fr.srt")
        result = runner.invoke(app, ["translate", temp_in.name, "--target-lang", "fr", "--output", output_path])
        assert result.exit_code == 0
        assert "Translating" in result.output
        assert os.path.exists(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "TRANSLATED: Hello" in content
            assert "TRANSLATED: How are you?" in content


def test_translate_missing_required_args(runner):
    result = runner.invoke(app, ["translate"])
    assert result.exit_code != 0
    assert "Missing argument 'SRT_FILE'" in result.output


@patch("cli.GoogleTranslator.translate")
def test_translate_preserves_srt_structure(mock_translate, runner, tmp_path):
    mock_translate.side_effect = lambda s: f"X-{s}"
    srt = tmp_path / "in.srt"
    srt.write_text(
        "1\n00:00:01,000 --> 00:00:02,00
    )