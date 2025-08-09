# -*- coding: utf-8 -*-
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


def validate_video_extension_cb(ctx, param, value: str) -> str:
    """Click callback: validate video extension and return the original value."""
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


def validate_video_extension(value: str) -> None:
    """Helper to call from non-Click code (raises BadParameter on error)."""
    validate_video_extension_cb(None, None, value)
