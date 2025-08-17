#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click

from functions.i18n import _, set_language  # noqa: E402

set_language(os.getenv("APP_LANG", "en"))

# Domain logic
from functions.has_subtitles import has_subtitles  # noqa: E402
from functions.validators import (  # noqa: E402
    validate_srt,
    validate_video_extension,
)
from functions.write import (  # noqa: E402
    clean_srt_file_to_txt,
    write_segments,
)

# ------------------------- Optional runtime stubs -------------------------

try:
    from deep_translator import (
        GoogleTranslator,  # (used only by translate command)
    )
except Exception:

    class GoogleTranslator:  # type: ignore
        def __init__(self, *_, **__):
            raise ImportError("deep-translator not installed")

        def translate(self, *_, **__):
            raise ImportError("deep-translator not installed")


try:
    import whisper  # real package, if present
except Exception:
    # Minimal stub so `cli.whisper.load_model` exists for mocking in tests
    class _WhisperStub:
        def load_model(self, *args, **kwargs):
            raise ImportError("Whisper not installed")

    whisper = _WhisperStub()  # type: ignore


# ------------------------------ Utilities ---------------------------------
def transcribe_video(
    video_path: str,
    model: str,
    language: str,
    output: str,
    clean: bool = False,
) -> str:
    """Run Whisper, then delegate writing to write_segments."""
    try:
        model_instance = whisper.load_model(model)
    except Exception as e:
        raise click.ClickException(
            "Whisper "
            + _(" is required for transcription. ")
            + _("Install it with: ")
            + "pip install openai_whisper"
        ) from e

    result = model_instance.transcribe(video_path, language=language)
    segments = result.get("segments", [])
    try:
        return write_segments(segments, output, clean)
    except Exception as e:
        raise click.ClickException(
            _("⚠️ Failed to write transcription: ") + str(e)
        ) from e


# -------------------------- Custom help option ----------------------------
def _show_help(ctx: click.Context, _param, value):
    if value:
        click.echo(ctx.get_help(), color=ctx.color)
        ctx.exit()


class CustomGroup(click.Group):
    """Group that installs a custom help option with custom help text."""

    def get_help_option(self, ctx):
        return click.Option(
            ["--help", "-h"],
            is_flag=True,
            expose_value=False,
            is_eager=True,
            help=_("📖 Show this help and exit."),
            callback=_show_help,
        )


# ------------------------------- CLI root ---------------------------------
@click.group(cls=CustomGroup, invoke_without_command=True)
@click.option(
    "--lang",
    default="en",
    help=(
        _("🌐 Interface language options: \n")
        + "en, de, es, fr, ja, ko, pt, pt, br, ru, zh\n"
        + _("Defaults to English.")
    ),
)
@click.pass_context
def cli(ctx: click.Context, lang: str):
    # Install translation for runtime messages.
    set_language(lang)
    ctx.ensure_object(dict)
    ctx.obj["_"] = _

    if ctx.invoked_subcommand is None:
        desired = lang
        current = os.getenv("APP_LANG", "en")
        if desired != current:
            # Re-execute script with APP_LANG=<desired> and --help
            env = dict(os.environ, APP_LANG=desired)
            os.execvpe(
                sys.executable,
                [sys.executable, sys.argv[0], "--help"],
                env,
            )
        else:
            click.echo(
                _("** Welcome to ")
                + "Subtitle Extractor & Translator CLI **\n"
            )
            click.echo(ctx.get_help())
            click.echo("")
    else:
        click.echo(
            _("** Welcome to ")
            + "Subtitle Extractor & Translator CLI **\n"
        )


# -------------------------------- Commands --------------------------------
@cli.command(help=_("- Transcribe subtitles from video or audio"))
@click.argument(
    "video_path",
    type=click.Path(
        exists=True, dir_okay=False, readable=True, resolve_path=True
    ),
    callback=validate_video_extension,
)
@click.option(
    "--language",
    default="en",
    help=_("Language hint for transcription") + " (e.g., en, es, zh).",
)
@click.option(
    "--output",
    default="transcription.srt",
    callback=validate_srt,  # must be .srt for this command
    help=_("Output '.srt' file"),
)
@click.option(
    "--model",
    default="base",
    help="Whisper "
    + _("model size to use.")
    + "\n"
    + _("Options: ")
    + "(tiny, base, small, medium, large)",
)
@click.option(
    "--clean",
    is_flag=True,
    default=False,
    help=_("Also write plain '.txt' (no numbering/timestamps)."),
)
@click.pass_context
def transcribe(ctx, video_path, model, language, output, clean):
    _ = ctx.obj["_"]
    short_in = Path(video_path).name
    short_out = Path(output).name

    click.echo(
        _("🎙️ Transcribing ")
        + short_in
        + _(" with language ")
        + language
        + _(" to ")
        + short_out
    )

    final_output = transcribe_video(
        video_path, model, language, output, clean
    )

    click.echo(_("✅ Transcription complete."))
    if clean:
        txt_path = Path(output).with_suffix(".txt")
        click.echo(_("🧹 Clean transcript saved to ") + txt_path.name)
    else:
        click.echo(
            _("Subtitles saved to ") + Path(final_output).name + " 📝"
        )


@cli.command(
    help=_("- Extract subtitles from video; fallback to transcription")
)
@click.argument(
    "video_path",
    type=click.Path(
        exists=True, dir_okay=False, readable=True, resolve_path=True
    ),
    callback=validate_video_extension,
)
@click.option(
    "--output",
    default="subtitles.srt",
    callback=validate_srt,  # must be .srt
    help=_("Output subtitle file name"),
)
@click.option(
    "--language",
    default="en",
    help=_("Language for fallback transcription"),
)
@click.option(
    "--model",
    default="base",
    help="Whisper"
    + _(" model size to use")
    + _(" (tiny, base, small, medium, large)"),
)
@click.option(
    "--clean",
    is_flag=True,
    default=False,
    help=_("Also write plain '.txt' (no timestamps or extra lines)"),
)
@click.pass_context
def extract(ctx, video_path, output, language, model, clean):
    _ = ctx.obj["_"]
    short_in = Path(video_path).name
    short_out = Path(output).name

    click.echo(
        _("🎬 Extracting subtitles from ")
        + short_in
        + _("... to ")
        + short_out
    )

    # 1) Try embedded subs
    used_ffmpeg = False
    if has_subtitles(ctx, file_path=video_path):
        click.echo(
            _("📺 Embedded subtitles found. Extracting with ")
            + "ffmpeg..."
        )
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    video_path,
                    "-map",
                    "0:s:0",
                    "-c:s",
                    "srt",
                    output,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            used_ffmpeg = True
            click.echo(_("✅ Subtitles saved to ") + short_out + " 📝")

            if clean:
                # Make a .txt from the extracted .srt
                txt_out = Path(output).with_suffix(".txt")
                clean_srt_file_to_txt(output, str(txt_out))
                click.echo(
                    _("🧹 Clean transcript saved to ") + txt_out.name
                )

            return output

        except subprocess.CalledProcessError as e:
            click.echo(
                _(
                    "⚠️ Extraction failed. Falling back to transcription."
                ).format(code=e.returncode)
            )

    # 2) Fallback to Whisper (if no subs or ffmpeg failed)
    if not used_ffmpeg:
        click.echo(
            _("⚠️ No embedded subtitles found. Using ")
            + "Whisper"
            + _(" for transcription.")
        )
        final_out = transcribe_video(
            video_path, model, language, output, clean
        )
        click.echo(_("✅ Fallback transcription complete."))
        if clean:
            txt_path = Path(output).with_suffix(".txt")
            click.echo(
                _("🧹 Clean transcript saved to ") + txt_path.name
            )
        else:
            click.echo(
                _("Subtitles saved to ") + Path(final_out).name + " 📝"
            )
        return final_out


@cli.command(help=_("- Translate subtitles and save to '.srt' "))
@click.argument(
    "srt_file",
    type=click.Path(
        exists=True, dir_okay=False, readable=True, resolve_path=True
    ),
)
@click.option(
    "--target-lang",
    required=True,
    help=_("Target language") + "(e.g., es, fr, de)",
)
@click.option(
    "--output",
    default="translated.srt",
    callback=validate_srt,  # must be .srt
    help=_("Translated subtitle output file"),
)
@click.option(
    "--clean",
    is_flag=True,
    default=False,
    help=_("Also write plain '.txt' (no numbering/timestamps)."),
)
@click.pass_context
def translate(
    ctx: click.Context,
    srt_file: str,
    target_lang: str,
    output: str,
    clean: bool,
):
    _ = ctx.obj["_"]
    short_name = Path(srt_file).name
    out_name = Path(output).name

    click.echo(
        _("🌐 Translating ")
        + short_name
        + _(" to ")
        + target_lang
        + _(" -> ")
        + out_name
    )

    try:
        translator = GoogleTranslator(source="auto", target=target_lang)
    except ImportError:
        raise click.ClickException(
            _("The ")
            + "'deep-translator'"
            + _(" package is required for translation. \n")
            + _("Install it with: ")
            + "pip install deep-translator"
        )

    try:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(srt_file, "r", encoding="utf-8") as infile, open(
            output, "w", encoding="utf-8"
        ) as outfile:
            for line in infile:
                s = line.strip()
                if not s or s.isdigit() or "-->" in s:
                    # keep indices, blank lines, and timing lines
                    outfile.write(line)
                else:
                    translated = translator.translate(s)
                    outfile.write(translated + "\n")
    except Exception as e:
        raise click.ClickException(_("⚠️ Translation failed: ") + str(e))

    click.echo(
        _("✅ Translation complete. Saved to ") + out_name + " 📝"
    )

    if clean:
        try:
            txt_out = Path(output).with_suffix(".txt")
            clean_srt_file_to_txt(output, str(txt_out))
            click.echo(
                _("🧹 Clean transcript saved to ") + txt_out.name
            )
        except Exception as e:
            raise click.ClickException(_("⚠️ Clean failed: ") + str(e))


@cli.command(
    help=(
        _(" - Clean an existing '.srt' or '.txt' into plain text\n")
        + _("  (no empty lines or timestamps).")
    )
)
@click.argument(
    "srt_file",
    type=click.Path(
        exists=True, dir_okay=False, readable=True, resolve_path=True
    ),
)
@click.option(
    "--output",
    default=None,  # defaults to input[:-4] + ".txt"
    help=_(
        "Output text file (defaults to input name with '.txt' extension)"
    ),
)
def clean(srt_file, output):
    try:
        out_path = clean_srt_file_to_txt(srt_file, output)
    except click.BadParameter as e:
        raise click.BadParameter(_("Invalid input file: ") + str(e))
    except Exception as e:
        raise click.ClickException(
            _("⚠️ Failed to clean ")
            + Path(srt_file).name
            + ": "
            + str(e)
        )

    click.echo(
        _("🧹 Clean transcript saved to ") + Path(out_path).name + " 📝"
    )
    click.echo(_("Done."))


# ------------------------------- Entrypoint -------------------------------
if __name__ == "__main__":
    cli()
