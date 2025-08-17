import os
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import cli as cli_module  # noqa: E402

app = cli_module.cli
from functions.write import (
    clean_srt_file_to_txt,
    clean_srt_lines
)


@pytest.fixture
def runner():
    return CliRunner()


def test_clean_command_basic(tmp_path, runner):
    srt_file = tmp_path / "sample.srt"
    srt_file.write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n\n", encoding="utf-8")
    out_txt = tmp_path / "clean.txt"

    # ✅ invoke the group with the subcommand name
    res = runner.invoke(app, ["clean", str(srt_file), "--output", str(out_txt)])
    assert res.exit_code == 0, res.output
    assert out_txt.exists()
    assert out_txt.read_text(encoding="utf-8").strip() == "hello"


def test_clean_srt_lines_unit():
    lines = [
        "1\n",
        "00:00:00,000 --> 00:00:01,000\n",
        " Hello \n",
        "\n",
        "2\n",
        "00:00:01,500 --> 00:00:02,000\n",
        "World\n",
        "\n",
    ]
    cleaned = clean_srt_lines(lines)
    assert cleaned == ["Hello", "World"]


def test_clean_rejects_non_txt_output_when_supplied(tmp_path, runner):
    srt = tmp_path / "foo.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nX\n\n", encoding="utf-8")

    res = runner.invoke(app, ["clean", str(srt), "--output", str(tmp_path / "bad.ext")])
    assert res.exit_code != 0
    # Your validator says "File must end with: .txt"
    assert "output file must end with" in res.output.lower()


def test_clean_defaults_to_input_basename_txt(tmp_path, runner):
    src = tmp_path / "episode01.en.srt"
    src.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n\n", encoding="utf-8")

    res = runner.invoke(app, ["clean", str(src)])
    assert res.exit_code == 0, res.output

    expected = src.parent / (src.name[:-4] + ".txt")
    assert expected.exists()
    assert expected.read_text(encoding="utf-8").strip() == "Hi"


def test_clean_accepts_txt_input(tmp_path, runner):
    txt_in = tmp_path / "already.txt"
    txt_in.write_text("Hello\n\nWorld\n", encoding="utf-8")

    res = runner.invoke(app, ["clean", str(txt_in)])
    assert res.exit_code == 0, res.output

    expected = txt_in.parent / (txt_in.name[:-4] + ".txt")
    assert expected.exists()
    assert expected.read_text(encoding="utf-8").strip() == "Hello\nWorld"
