import os
from pathlib import Path

from click.testing import CliRunner

import cli


def test_transcribe_rejects_non_srt_or_txt(tmp_path):
    vid = tmp_path / "in.mp4"
    vid.write_bytes(b"")
    runner = CliRunner()
    res = runner.invoke(cli.cli, ["transcribe", str(vid), "--output", "oops.mov"])
    assert res.exit_code != 0
    assert "File must end with" in res.output

def test_extract_rejects_non_srt(tmp_path):
    vid = tmp_path / "in.mov"
    vid.write_bytes(b"")
    runner = CliRunner()
    res = runner.invoke(cli.cli, ["extract", str(vid), "--output", "out.mp3"])
    assert res.exit_code != 0
    assert "File must end with" in res.output

def test_clean_rejects_non_txt(tmp_path):
    srt = tmp_path / "subtitles.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n\n", encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(cli.cli, ["clean", str(srt), "--output", "clean.srt"])
    assert res.exit_code != 0
    assert "File must end with" in res.output
