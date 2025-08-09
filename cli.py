import gettext
import os
import subprocess

import click
import whisper  # noqa: F401
from deep_translator import GoogleTranslator

from functions.has_subtitles import has_subtitles
from functions.validators import validate_video_extension_cb


# Placeholder _ so module imports don't crash before --lang processed
def _(x):
    return x


def set_language(lang):
    global _
    localedir = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "locales"
    )
    try:
        trans = gettext.translation(
            domain="messages",
            localedir=localedir,
            languages=[lang],
            fallback=True,
        )
        _ = trans.gettext
    except Exception:
        click.echo(
            f"⚠️ Translation for '{lang}' not found. Falling back to English."
        )
        _ = gettext.gettext


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    ms = int((s - int(s)) * 1000)
    return f"{h:02}:{m:02}:{int(s):02},{ms:03}"


def transcribe_video(
    video_path: str, model: str, language: str, output: str
) -> None:
    model_instance = whisper.load_model(model)
    result = model_instance.transcribe(video_path, language=language)

    try:
        with open(output, "w", encoding="utf-8") as f:
            for i, seg in enumerate(result["segments"], start=1):
                f.write(f"{i}\n")
                f.write(
                    f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}\n"
                )
                f.write(f"{seg['text'].strip()}\n\n")
    except Exception as e:
        # Bubble up a Click-friendly error the tests can assert on
        raise click.ClickException(
            _(f"❌ Failed to write transcription to {output}: {e}")
        )


@click.group(invoke_without_command=True)
@click.option(
    "--lang",
    default="en",
    help=_(
        "currently available for the base cli language: "
        "bn, de, es, fr, haw, hi, hmn, ko, ru, ur "
        "Defaults to English."
    ),
)
@click.pass_context
def cli(ctx, lang):
    set_language(lang)
    if ctx.invoked_subcommand is None:
        click.echo(
            _("\n**Welcome to Subtitle Extractor & Translator CLI**\n")
        )
        click.echo(ctx.get_help())
        click.echo("\n")


# **********  transcribe subcommand ************************
@cli.command(help=_("- Transcribe subtitles from video or audio"))
@click.argument(
    "video_path",
    type=click.Path(
        exists=True, dir_okay=False, readable=True, resolve_path=True
    ),
    callback=validate_video_extension_cb,
)
@click.option(
    "--language",
    default="en",
    help=_(
        "Language model to use for transcription (e.g., bn, en, es,)"
    ),
)
@click.option(
    "--output",
    default="transcription.srt",
    help=_("output SRT file"),
)
@click.option(
    "--model",
    default="base",
    help=_(
        "Whisper model size to use - tiny, base, small, medium, large, turbo"
    ),
)
def transcribe(
    video_path: str, model: str, language: str, output: str
) -> None:
    click.echo(
        _(
            "Transcribing {video_path} with language {language} to {output}"
        ).format(
            video_path=video_path, language=language, output=output
        )
    )
    transcribe_video(video_path, model, language, output)
    click.echo(_("Transcription complete."))
    click.echo(
        _("Subtitles saved to {output} 📝").format(output=output)
    )


# **************** extract subcommand ************************
@cli.command(
    help=_(
        "- Extract subtitles from video, fallback to transcribe if not"
    )
)
@click.argument(
    "video_path",
    type=click.Path(
        exists=True, dir_okay=False, readable=True, resolve_path=True
    ),
    callback=validate_video_extension_cb,
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
def extract(
    video_path: str, output: str, language: str, model: str
) -> None:
    click.echo(
        _("🎬 Extracting subtitles from {video_path}...").format(
            video_path=video_path
        )
    )
    if has_subtitles(video_path):
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
    else:
        click.echo(
            _(
                "⚠️ No embedded subtitles found. Using Whisper for transcription."
            )
        )

    # fallback to Whisper
    transcribe_video(video_path, model, language, output)
    click.echo(_("✅ Fallback transcription complete."))
    click.echo(
        _("Subtitles saved to {output} 📝").format(output=output)
    )


# *************** translate subcommand *********************
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
    help=_("Target language to translate to (e.g., es, fr, de)"),
)
@click.option(
    "--output",
    default="translated.srt",
    help=_("Translated subtitle output file"),
)
def translate(srt_file: str, target_lang: str, output: str) -> None:
    click.echo(
        _("Translating {srt_file} to {target_lang} -> {output}").format(
            srt_file=srt_file, target_lang=target_lang, output=output
        )
    )

    translator = GoogleTranslator(source="auto", target=target_lang)
    try:
        with open(srt_file, "r", encoding="utf-8") as infile, open(
            output, "w", encoding="utf-8"
        ) as outfile:
            for line in infile:
                if (
                    "-->" in line
                    or line.strip().isdigit()
                    or line.strip() == ""
                ):
                    outfile.write(line)
                else:
                    translated = translator.translate(line.strip())
                    outfile.write(translated + "\n")
    except Exception as e:
        raise click.ClickException(_(f"❌ Failed to translate: {e}"))

    click.echo(_("✅ Translation complete."))
    click.echo(
        _("Subtitles saved to {output} 📝").format(output=output)
    )


if __name__ == "__main__":
    cli()
