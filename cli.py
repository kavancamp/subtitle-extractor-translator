import json
import subprocess

import click
import whisper  # noqa: F401
from deep_translator import GoogleTranslator

from functions.transcribe_video import transcribe_video


def has_subtitles(file_path: str) -> bool:
    # Check if video file has embedded subtitle tracks using ffprobe.
    try:
        # Run ffprobe - list all streams
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_streams",
                "-select_streams",
                "s",  # 's' = subtitle
                file_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)

        # Check if any subtitle streams are present
        return bool(data.get("streams"))
    except subprocess.CalledProcessError as e:
        print(f"⚠️ ffprobe error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON decode error: {e}")
        return False


@click.group()
def cli():
    """Welcome to Subtitle Extractor & Translator CLI"""
    pass


# extract subcommand
@cli.command()
@click.argument(
    "video_path",
    type=click.Path(exists=True),
)
@click.option(
    "--output",
    default="subtitles.srt",
    help="Output subtitle file name",
)
@click.option(
    "--language",
    default="en",
    help="Language for fallback transcription",
)
@click.option(
    "--model", default="base", help="Whisper model size to use"
)
def extract(video_path, output, language, model):
    """Extract embedded subtitles, or fallback to Whisper transcription."""
    click.echo(f"🎬 Extracting subtitles from {video_path}...")

    if has_subtitles(video_path):
        click.echo(
            "📺 Embedded subtitles found. Extracting with ffmpeg..."
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
            click.echo(f"✅ Subtitles extracted to {output}")
            return
        except subprocess.CalledProcessError as e:
            click.echo(
                f"⚠️ Subtitle extraction failed. Falling back to transcription...{e}"
            )

    click.echo(
        "⚠️ No embedded subtitles found. Using Whisper for transcription."
    )
    transcribe_video(video_path, model, language, output)
    click.echo("✅ Fallback transcription complete.")
    click.echo(f"Subtitles saved to {output} 📝")


# transcribe subcommand
@cli.command()
@click.argument(
    "video_path",
    type=click.Path(exists=True),
)
@click.option(
    "--language",
    default="en",
    help="Language model to use for transcription (e.g., en, es, zh)",
)
@click.option(
    "--output",
    default="transcription.srt",
    help="output SRT file",
)
@click.option(
    "--model",
    default="base",
    help="Whisper model size to use - tiny, base, small, medium, large, turbo",
)
def transcribe(
    video_path,
    model,
    language,
    output,
):
    """Transcribe audio from video using Whisper"""

    click.echo(
        f"Transcribing {video_path} with language {language} to {output}"
    )
    click.echo(
        f"Transcribing {video_path} with language {language} to {output}"
    )
    transcribe_video(video_path, model, language, output)

    click.echo("Transcription complete.")
    click.echo(f"Subtitles saved to {output} 📝")


# translate subcommand
@cli.command()
@click.argument(
    "srt_file",
    type=click.Path(exists=True),
)
@click.option(
    "--target-lang",
    required=True,
    help="Target language to translate to (e.g., es, fr, de)",
)
@click.option(
    "--output",
    default="translated.srt",
    help="Translated subtitle output file",
)
def translate(
    srt_file,
    target_lang,
    output,
):
    """Translate an SRT file to a target language."""

    click.echo(f"Translating {srt_file} to {target_lang} -> {output}")
    # translation logic

    translator = GoogleTranslator(source="auto", target=target_lang)

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


if __name__ == "__main__":
    cli()
