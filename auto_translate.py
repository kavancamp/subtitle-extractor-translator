import os
import subprocess

import click
import polib
from deep_translator import GoogleTranslator


@click.command()
@click.option(
    "--source",
    "-s",
    required=True,
    help="Source language code (e.g., 'en')",
)
@click.option(
    "--langs",
    "-l",
    required=True,
    help="Target language codes (e.g., fr, es, de)",
)
def auto_translate(source, langs):
    """Auto-translates .po files and compiles them into .mo files."""
    base_path = os.path.join(os.path.dirname(__file__), "locales")
    langs = [lang.strip() for lang in langs.split(",")]
    lc = "LC_MESSAGES"
    try:
        subprocess.run(
            [
                "xgettext",
                "--from-code=UTF-8",
                "--language=Python",
                "--keyword=_",
                "-o",
                os.path.join(base_path, "messages.pot"),
                "cli.py",
                os.path.join("functions/validators.py"),
                os.path.join("functions/has_subtitles.py"),
            ]
        )
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")

    for lang in langs:
        try:
            subprocess.run(
                [
                    "cp",
                    os.path.join(base_path, "messages.pot"),
                    os.path.join(base_path, lang, lc, "messages.po"),
                ]
            )
        except Exception as e:
            click.echo(f"❌ Unexpected error: {e}")
            continue

        click.echo(f"🔁 Translating to: {lang}")
        lang_dir = os.path.join(base_path, lang, lc)
        os.makedirs(lang_dir, exist_ok=True)
        po_path = os.path.join(lang_dir, "messages.po")

        if not os.path.exists(po_path):
            try:
                click.echo(f"⚠️ Missing file, creating new: {po_path}")
                subprocess.run(
                    [
                        "msginit",
                        "--no-translator",
                        "--input",
                        os.path.join(base_path, "messages.pot"),
                        "--locale",
                        lang,
                        "--output-file",
                        po_path,
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                click.echo(f"❌ msginit failed: {e}")
                continue
            except Exception as e:
                click.echo(f"❌ Unexpected error: {e}")
                continue

        po = polib.pofile(po_path)

        for entry in po.untranslated_entries():
            if entry.msgid.strip():
                try:
                    entry.msgstr = GoogleTranslator(
                        source=source, target=lang
                    ).translate(entry.msgid)
                except Exception as e:
                    click.echo(f"❌ Failed for '{entry.msgid}': {e}")

        # Save updated .po file
        po.save(po_path)
        click.echo(f"✅ Saved updated translations to {po_path}")

        # Generate .mo file
        mo_path = os.path.join(base_path, lang, lc, "messages.mo")
        po.save_as_mofile(mo_path)
        click.echo(f"📦 Compiled .mo file saved to {mo_path}")


if __name__ == "__main__":
    auto_translate()

# python3 auto_translate.py --source en --langs bn,de,es,fr,haw,hi,ko,ru,ur,hmn
