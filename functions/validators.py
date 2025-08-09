# functions/validators.py
import gettext
from pathlib import Path

import click

VALID_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".flv",
}


def validate_video_extension(ctx, param, value):
    _ = gettext.gettext
    ext = Path(value).suffix.lower()
    if ext not in VALID_VIDEO_EXTENSIONS:
        raise click.BadParameter(
            _(
                f"Invalid video format: '{ext}'. Must be one of: "
                "{', '.join(sorted(VALID_VIDEO_EXTENSIONS))}"
            )
        )
    return value
