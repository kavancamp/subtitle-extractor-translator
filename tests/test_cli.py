# -*- coding: utf-8 -*-
import importlib
import os
import sys

import pytest
from click.testing import CliRunner

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import cli as cli_module  # noqa: E402

app = cli_module.cli


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_help_default_english(runner):
    result = runner.invoke(app)
    assert result.exit_code == 0
    assert "** Welcome to Subtitle Extractor & Translator CLI **" in result.output


def test_transcribe_help(runner):
    result = runner.invoke(app, ["transcribe", "--help"])
    assert result.exit_code == 0
    assert "Transcribe subtitles" in result.output


def test_clean_help(runner):
    result = runner.invoke(app, ["clean", "--help"])
    assert result.exit_code == 0
    assert "Clean an existing" in result.output
    assert "plain text" in result.output


def test_translate_help(runner):
    result = runner.invoke(app, ["translate", "--help"])
    assert result.exit_code == 0
    assert "Translate subtitles" in result.output


def test_extract_help(runner):
    result = runner.invoke(app, ["extract", "--help"])
    assert result.exit_code == 0
    assert "Extract subtitles from video" in result.output
    assert "fallback" in result.output


def test_cli_help_in_spanish(monkeypatch, runner):
    # Set env before (re)import so gettext loads Spanish catalog
    monkeypatch.setenv("APP_LANG", "es")

    # Reload the CLI module so the decorators re-evaluate with Spanish gettext
    import cli
    importlib.reload(cli)

    res = runner.invoke(cli.cli, ["--help"])
    assert res.exit_code == 0

    assert ("Transcribir" in res.output
            or "Transcripción" in res.output
            or "🌐 Opciones de idioma" in res.output
            or "- Limpiar" in res.output)
    
def test_unsupported_lang_falls_back_to_english(runner):
    result = runner.invoke(app, ["--lang", "xx"])
    assert result.exit_code == 0
    assert "** Welcome to Subtitle Extractor & Translator CLI **" in result.output


def test_lang_option_accepts_arbitrary_lang():
    r = CliRunner().invoke(app, ["--lang", "de"])
    assert r.exit_code == 0
    assert "** Welcome to Subtitle Extractor & Translator CLI **" in r.output


def test_help_text_customized():
    r = CliRunner().invoke(app, ["--help"])
    assert r.exit_code == 0
    assert "📖 Show this help and exit." in r.output
    assert "🌐 Interface language" in r.output
