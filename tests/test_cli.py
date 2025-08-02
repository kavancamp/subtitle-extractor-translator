import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

from click.testing import CliRunner  # noqa: E402

from cli import cli  # noqa: E402


@pytest.fixture
def runner():
    return CliRunner()


def test_extract_command(runner):
    result = runner.invoke(
        cli,
        [
            "extract",
            "sample.mp4",
            "--output",
            "out.srt",
        ],
    )
    assert result.exit_code == 0
    assert "Extracting subtitles" in result.output


# Mock the whisper model loading and transcription
@patch("cli.whisper.load_model")
def test_transcribe_creates_srt_file(mock_load_model, runner):
    # mock return value setup
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [
            {"start": 0, "end": 1, "text": "Hello World"},
            {"start": 1, "end": 2, "text": "Testing subtitles"},
        ]
    }
    mock_load_model.return_value = mock_model
    # dummy file
    with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_video:
        output_path = temp_video.name + ".srt"
        result = runner.invoke(
            cli,
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
        result = runner.invoke(
            cli,
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
