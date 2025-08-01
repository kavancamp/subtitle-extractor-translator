import os
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)
from click.testing import CliRunner  # noqa: E402

from cli import cli  # noqa: E402

runner = CliRunner()


def test_extract_command():
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


def test_transcribe_command():
    result = runner.invoke(
        cli,
        [
            "transcribe",
            "sample.mp4",
            "--language",
            "en",
            "--output",
            "out.srt",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Transcribing" in result.output


def test_translate_command():
    result = runner.invoke(
        cli,
        [
            "translate",
            "captions.srt",
            "--target-lang",
            "fr",
            "--output",
            "fr.srt",
        ],
    )
    assert result.exit_code == 0
    assert "Translating" in result.output
