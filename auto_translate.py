#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path

import click
import deepl
import polib

# Project root = auto_translate.py's directory
ROOT = Path(__file__).resolve().parent

# Directories to skip when globbing for .py sources
SKIP_DIRS = {
    "venv",
    ".git",
    "locales",
    "tests",
}  # add "tests" if you want to exclude tests


def python_sources(root: Path) -> list[str]:
    files = []
    for p in root.rglob("*.py"):
        # Skip unwanted dirs
        parts = set(p.parts)
        if parts & SKIP_DIRS:
            continue
        files.append(str(p))
    return files


def run_checked(cmd: list[str]) -> None:
    click.echo(f"→ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


# --------------------------------------------------------------------
# Config
# --------------------------------------------------------------------
BASE = Path(__file__).resolve().parent / "locales"
LC = "LC_MESSAGES"
POT = BASE / "messages.pot"
PY_FILES = [
    "functions/validators.py",
    "functions/has_subtitles.py",
    "functions/i18n.py",
    "functions/write.py",
    "cli.py",
]

# Emoji/symbol prefix splitter (keep emoji/symbols untouched)
LEADING_SYMBOLS_RE = re.compile(r"^([\W_]+)(.*)$", flags=re.UNICODE)

# Preserve Mustache {{name}} and Python {name} placeholders via XML tags for DeepL
MUSTACHE_RE = re.compile(r"{{\s*([^{}]+?)\s*}}")
FORMAT_RE = re.compile(r"{\s*([a-zA-Z0-9_]+)\s*}")

# 🔒 Words that must never be translated (brand/library/CLI tokens)
# matching is case sensitive.
PROTECTED_WORDS = {
    "Whisper",
    "openai-whisper",
    "OpenAI",
    "DeepL",
    "ffmpeg",
    "ffprobe",
    "SRT",
    "CLI",
    "pip",
}

# Map to DeepL codes
DEEPL_LANG_MAP = {
    "en": "EN",
    "en-gb": "EN-GB",
    "es": "ES",
    "fr": "FR",
    "de": "DE",
    "it": "IT",
    "nl": "NL",
    "pl": "PL",
    "pt": "PT-PT",
    "pt-br": "PT-BR",
    "ru": "RU",
    "ja": "JA",
    "zh": "ZH",
}


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def split_leading_symbols(s: str) -> tuple[str, str]:
    m = LEADING_SYMBOLS_RE.match(s)
    if not m:
        return "", s
    return m.group(1), m.group(2)


def protect_placeholders_to_xml(text: str):
    """
    Replace placeholders with XML tags for DeepL tag_handling="xml".
    - {{name}} -> <m id="0"/>
    - {name}   -> <ph id="1"/>
    Returns (xml_text, restore_map) where restore_map maps the xml tag back to the original token.
    """
    restore: dict[str, str] = {}
    idx = 0

    def repl_mustache(m):
        nonlocal idx
        orig = m.group(0)
        tag = f'<m id="{idx}"/>'
        restore[tag] = orig
        idx += 1
        return tag

    def repl_format(m):
        nonlocal idx
        orig = m.group(0)
        tag = f'<ph id="{idx}"/>'
        restore[tag] = orig
        idx += 1
        return tag

    text = MUSTACHE_RE.sub(repl_mustache, text)
    text = FORMAT_RE.sub(repl_format, text)
    return text, restore


def protect_terms(
    text: str, start_index: int = 0
) -> tuple[str, dict[str, str], int]:
    """
    Replace PROTECTED_WORDS with <term id="N"/> placeholders.
    Returns (protected_text, restore_map, next_index).
    - Uses literal replacement; replaces ALL occurrences.
    - Index continues from start_index so it doesn't clash with other tags.
    """
    restore: dict[str, str] = {}
    idx = start_index

    # Sort by length desc to avoid partial overlaps (e.g., 'pip' before 'pipx' issues)
    for word in sorted(PROTECTED_WORDS, key=len, reverse=True):
        # Replace repeatedly for all occurrences
        search_pos = 0
        while True:
            at = text.find(word, search_pos)
            if at == -1:
                break
            tag = f'<term id="{idx}"/>'
            restore[tag] = word
            text = text[:at] + tag + text[at + len(word) :]  # noqa E203
            search_pos = at + len(tag)
            idx += 1
    return text, restore, idx


def restore_from_map(text: str, restore_map: dict[str, str]) -> str:
    # Replace longer tags first just in case
    for tag, orig in sorted(
        restore_map.items(), key=lambda kv: -len(kv[0])
    ):
        text = text.replace(tag, orig)
    return text


def needs_translation(entry: polib.POEntry) -> bool:
    return (not entry.msgstr) or entry.fuzzy


def map_lang_to_deepl(code: str) -> str:
    c = code.lower()
    return DEEPL_LANG_MAP.get(c, c.upper())


# --------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------
@click.command()
@click.option(
    "--source",
    "-s",
    required=True,
    help="Source language code (e.g., en)",
)
@click.option(
    "--langs",
    "-l",
    required=True,
    help="Comma-separated target codes (e.g., es,fr,de)",
)
def auto_translate(source: str, langs: str) -> None:
    """
    Extract strings, update per-language .po, machine-translate missing/fuzzy entries
    with DeepL using XML tag-handling so placeholders survive, protect product/library
    names, and compile .mo.
    """
    targets = [c.strip() for c in langs.split(",") if c.strip()]
    BASE.mkdir(parents=True, exist_ok=True)

    # Initialize DeepL
    auth_key = os.environ.get("DEEPL_AUTH_KEY")
    if not auth_key:
        raise click.ClickException(
            "DEEPL_AUTH_KEY not set in environment."
        )
    translator = deepl.Translator(auth_key)

    # 1) Extract to POT
    click.echo(
        "🧰 Extracting translatable strings → locales/messages.pot"
    )
    SOURCES = python_sources(ROOT)

    # Sanity log: confirm cli.py is in SOURCES
    if str(ROOT / "cli.py") not in SOURCES:
        click.echo(
            "⚠️  cli.py not found in SOURCES — check SKIP_DIRS/glob logic.",
            err=True,
        )

    run_checked(
        [
            "xgettext",
            "--from-code=UTF-8",
            "--language=Python",
            "--keyword=_",
            "-o",
            str(ROOT / "locales" / "messages.pot"),
            *SOURCES,
        ]
    )

    src_deepl = map_lang_to_deepl(source)

    for lang in targets:
        lang_dir = BASE / lang / LC
        po_path = lang_dir / "messages.po"
        mo_path = lang_dir / "messages.mo"
        lang_dir.mkdir(parents=True, exist_ok=True)

        # 2) Ensure PO exists, then merge with POT
        if not po_path.exists():
            click.echo(f"📄 Creating new catalog for {lang}")
            run(
                [
                    "msginit",
                    "--no-translator",
                    "--locale",
                    lang,
                    "--input",
                    str(POT),
                    "--output-file",
                    str(po_path),
                ]
            )
        else:
            click.echo(f"🔄 Merging POT into {po_path}")
            run(
                [
                    "msgmerge",
                    "--update",
                    "--backup=none",
                    str(po_path),
                    str(POT),
                ]
            )

        # 3) Translate missing/fuzzy entries
        click.echo(f"🌍 Translating missing strings → {lang}")
        po = polib.pofile(str(po_path))
        tgt_deepl = map_lang_to_deepl(lang)

        for entry in po:
            if not needs_translation(entry):
                continue

            msgid = entry.msgid
            if not msgid or not msgid.strip():
                continue

            prefix, rest = split_leading_symbols(msgid)

            # Only symbols/whitespace? Mirror source.
            if not rest.strip():
                entry.msgstr = msgid
                if "fuzzy" in entry.flags:
                    entry.flags.remove("fuzzy")
                continue

            # Protect placeholders
            xml_in, restore_placeholders = protect_placeholders_to_xml(
                rest
            )
            # Continue indexing after existing placeholder ids
            next_idx = (
                0
                + sum(1 for _ in re.finditer(r'<m id="\d+"/>', xml_in))
                + sum(1 for _ in re.finditer(r'<ph id="\d+"/>', xml_in))
            )
            xml_in, restore_terms, _ = protect_terms(
                xml_in, start_index=next_idx
            )

            # Retry with light backoff
            for attempt in range(3):
                try:
                    xml_out = translator.translate_text(
                        xml_in,
                        source_lang=src_deepl,
                        target_lang=tgt_deepl,
                        tag_handling="xml",
                    )
                    translated = str(xml_out)
                    # Restore brand terms and placeholders
                    translated = restore_from_map(
                        translated, restore_terms
                    )
                    translated = restore_from_map(
                        translated, restore_placeholders
                    )
                    entry.msgstr = f"{prefix}{translated}"
                    if "fuzzy" in entry.flags:
                        entry.flags.remove("fuzzy")
                    break
                except Exception as e:
                    if attempt == 2:
                        click.echo(
                            f"⚠️ DeepL translation failed for '{msgid[:60]}…' [{lang}]: {e}"
                        )
                        entry.msgstr = msgid  # degrade gracefully
                        if "fuzzy" in entry.flags:
                            entry.flags.remove("fuzzy")
                    time.sleep(0.6 * (attempt + 1))

        po.save(str(po_path))
        click.echo(f"✅ Saved {po_path}")

        # 4) Compile .mo
        po.save_as_mofile(str(mo_path))
        click.echo(f"📦 Compiled {mo_path}")


if __name__ == "__main__":
    try:
        auto_translate()
    except subprocess.CalledProcessError as e:
        click.echo(
            f"❌ Command failed: {' '.join(e.cmd)} (exit {e.returncode})"
        )
        raise
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")
        raise
