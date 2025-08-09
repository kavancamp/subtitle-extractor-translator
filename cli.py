# cli.py
import gettext
import os
import subprocess
import sys
from pathlib import Path

import click
from deep_translator import GoogleTranslator

from functions.has_subtitles import has_subtitles
from functions.validators import validate_video_extension

try:
    import whisper  # real package, if present
except Exception:
    # Minimal stub so `cli.whisper.load_model` exists for mocking
    class _WhisperStub:
        def load_model(self, *args, **kwargs):
            raise ImportError("whisper not installed")

    whisper = _WhisperStub()


def _(x):  # placeholder so module import doesn't crash before install
    return x


def set_language(lang: str) -> None:
    """
    Install gettext translations for runtime messages.
    """
    global _
    localedir = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "locales"
    )
    try:
        trans = gettext.translation(
            domain="messages",
            localedir=localedir,
            languages=[lang],
            fallback=False,  # change to True if you want silent fallback
        )
        _ = trans.gettext
        trans.install()  # also sets builtins._
    except Exception:
        # Fallback to English
        _ = gettext.gettext
        gettext.install(
            "messages", localedir=localedir, names=("ngettext",)
        )


set_language(os.getenv("APP_LANG", "en"))


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    ms = int((s - int(s)) * 1000)
    return f"{h:02}:{m:02}:{int(s):02},{ms:03}"


def transcribe_video(
    video_path: str, model: str, language: str, output: str
) -> None:
    try:
        model_instance = whisper.load_model(model)
    except Exception as e:
        # Package not installed or other load error
        raise click.ClickException(
            "Whisper is required for transcription. "
            "Install it with: pip install openai-whisper"
        ) from e
    result = model_instance.transcribe(video_path, language=language)

    try:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result["segments"], start=1):
                f.write(f"{i}\n")
                f.write(
                    f"{format_timestamp(segment['start'])} --> {format_timestamp(segment['end'])}\n"
                )
                f.write(f"{segment['text'].strip()}\n\n")
    except Exception as e:
        # surface clean message for Click
        raise RuntimeError(
            _(f"❌ Failed to write transcription to {output}: {e}")
        )


# ---- CLI --------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.option(
    "--lang",
    default="en",
    help=_(
        "Interface language (e.g., en, es, fr, de). Defaults to English."
    ),
)
@click.pass_context
def cli(ctx: click.Context, lang: str):
    # Install translation for runtime messages. (Help text was fixed via APP_LANG.)
    set_language(lang)
    ctx.ensure_object(dict)
    ctx.obj["_"] = _

    if ctx.invoked_subcommand is None:
        desired = lang
        current = os.getenv("APP_LANG", "en")
        if desired != current:
            # Re-execuce script with APP_LANG=<desired> and --help
            env = dict(os.environ, APP_LANG=desired)
            # Use the same entrypoint as invoked (script path)
            os.execvpe(
                sys.executable,
                [sys.executable, sys.argv[0], "--help"],
                env,
            )

        # Otherwise, print help in whatever APP_LANG was at import time
        click.echo(
            _("\n**Welcome to Subtitle Extractor & Translator CLI**\n")
        )
        click.echo(ctx.get_help())
        click.echo("")
    else:
        click.echo(
            _("\n**Welcome to Subtitle Extractor & Translator CLI**\n")
        )


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
    help=_("Language model for transcription (e.g., en, es, zh)."),
)
@click.option(
    "--output", default="transcription.srt", help=_("Output SRT file")
)
@click.option(
    "--model",
    default="base",
    help=_(
        "Whisper model size (tiny, base, small, medium, large, turbo)"
    ),
)
@click.pass_context
def transcribe(
    ctx: click.Context,
    video_path: str,
    model: str,
    language: str,
    output: str,
):
    _ = ctx.obj["_"]
    click.echo(
        _(
            "Transcribing {video_path} with language {language} to {output}"
        ).format(
            video_path=video_path, language=language, output=output
        )
    )
    try:
        transcribe_video(video_path, model, language, output)
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo(_("Transcription complete."))
    click.echo(
        _("Subtitles saved to {output} 📝").format(output=output)
    )


@cli.command(
    help=_("- Extract subtitles from video; fallback to transcribed")
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
    help=_("Output subtitle file name"),
)
@click.option(
    "--language",
    default="en",
    help=_("Language for fallback transcription"),
)
@click.option(
    "--model", default="base", help=_("Whisper model size to use")
)
@click.pass_context
def extract(
    ctx: click.Context,
    video_path: str,
    output: str,
    language: str,
    model: str,
):
    _ = ctx.obj["_"]
    click.echo(
        _("🎬 Extracting subtitles from {video_path}...").format(
            video_path=video_path
        )
    )

    if has_subtitles(ctx, file_path=video_path):
        click.echo(
            _("📺 Embedded subtitles found. Extracting with ffmpeg...")
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
                    output,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            click.echo(
                _("✅ Subtitles extracted to {output}").format(
                    output=output
                )
            )
            return
        except subprocess.CalledProcessError as e:
            click.echo(
                _(
                    "⚠️ Subtitle extraction failed. Falling back to transcription...{err}"
                ).format(err=e)
            )

    click.echo(
        _(
            "⚠️ No embedded subtitles found. Using Whisper for transcription."
        )
    )
    try:
        transcribe_video(video_path, model, language, output)
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo(_("✅ Fallback transcription complete."))
    click.echo(
        _("Subtitles saved to {output} 📝").format(output=output)
    )


@cli.command(help=_("- Translate subtitles and save to .srt"))
@click.argument(
    "srt_file",
    type=click.Path(
        exists=True, dir_okay=False, readable=True, resolve_path=True
    ),
)
@click.option(
    "--target-lang",
    required=True,
    help=_("Target language (e.g., es, fr, de)"),
)
@click.option(
    "--output",
    default="translated.srt",
    help=_("Translated subtitle output file"),
)
@click.pass_context
def translate(
    ctx: click.Context, srt_file: str, target_lang: str, output: str
):
    _ = ctx.obj["_"]
    click.echo(
        _("Translating {srt_file} to {target_lang} -> {output}").format(
            srt_file=srt_file, target_lang=target_lang, output=output
        )
    )

    translator = GoogleTranslator(source="auto", target=target_lang)
    try:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(srt_file, "r", encoding="utf-8") as infile, open(
            output, "w", encoding="utf-8"
        ) as outfile:
            for line in infile:
                if (
                    ("-->" in line)
                    or line.strip().isdigit()
                    or (line.strip() == "")
                ):
                    outfile.write(line)
                else:
                    translated = translator.translate(line.strip())
                    outfile.write(translated + "\n")
    except Exception as e:
        raise click.ClickException(str(e))


if __name__ == "__main__":
    cli()
