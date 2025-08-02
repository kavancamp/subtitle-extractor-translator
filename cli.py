# import os
# import subprocess
# from pathlib import Path
import click
import whisper
from deep_translator import GoogleTranslator


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    ms = int((s - int(s)) * 1000)
    return f"{h:02}:{m:02}:{int(s):02},{ms:03}"


@click.group()
def cli():
    """Welcome to Subtitle Extractor & Translator CLI"""
    pass


# extract subcommand
@cli.command()
@click.argument(
    "video_path",
    type=click.Path(exists=False),
)
@click.option(
    "--output",
    default="subtitles.srt",
    help="Output subtitle file name",
)
def extract(
    video_path,
    output,
):
    """Extract subtitles from a video file."""
    click.echo(f"Extracting subtitles from {video_path} to {output}")
    click.echo(
        "python cli.py extract sample.mp4 --output subtitles.srt"
    )


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
    # load whisper model
    audio = whisper.load_model(model)
    # transcribe file - returns a dictionary with segments key
    script = audio.transcribe(video_path, language=language)
    # save script to SRT file
    with open(output, "w", encoding="utf-8") as f:
        # i = subtitle number
        # SRT files number each subtitle block starting at 1
        for i, segment in enumerate(script["segments"], start=1):
            f.write(f"{i}\n")
            f.write(
                f"{format_timestamp(segment['start'])} --> {format_timestamp(segment['end'])}\n"
            )
            f.write(f"{segment['text'].strip()}\n\n")
            print(f"Subtitle {i}: {segment['text'].strip()}")
    # print completion message
    click.echo("Transcription complete.")
    click.echo(f"Subtitles saved to {output}")


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
