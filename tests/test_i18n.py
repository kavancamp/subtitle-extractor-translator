# -*- coding: utf-8 -*-
import gettext
import os

import pytest
from click.testing import CliRunner


@pytest.fixture
def french_gettext():
    locale_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../locales")
    )
    lang = "fr"
    try:
        trans = gettext.translation(
            "messages", localedir=locale_dir, languages=[lang]
        )
        return trans.gettext
    except FileNotFoundError:
        pytest.skip("French translation not found.")


def test_french_translation_known_string(french_gettext):
    _ = french_gettext
    assert (
        _("Subtitles saved to {output} 📝")
        != "Subtitles saved to {output} 📝"
        or ""
    )


def test_french_translation_error_message(french_gettext):
    _ = french_gettext
    assert (
        _(
            "⚠️ No embedded subtitles found. Using Whisper for transcription."
        )
        != "⚠️ No embedded subtitles found. Using Whisper for transcription."
        or ""
    )


def test_missing_translation_fallback():
    locale_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../locales")
    )
    with pytest.raises(FileNotFoundError):
        gettext.translation(
            "messages", localedir=locale_dir, languages=["xx"]
        ).install()
        
def test_placeholder_breakage(tmp_path, runner):
    video = tmp_path / "v.mp4"; video.write_bytes(b"\x00")
    bad = "🎬 Extracting subtitles from {video_path}... to {outpution_ph}"
    with patch.object(i18n, "_", side_effect=lambda s: bad if "Extracting subtitles" in s else s):
        res = runner.invoke(app, ["extract", str(video), "--output", str(tmp_path/"o.srt")])
        assert res.exit_code != 1