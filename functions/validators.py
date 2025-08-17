from pathlib import Path

import click

from functions.i18n import _

VALID_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".flv",
}


def validate_video_extension(ctx, param, value):
    ext = Path(value).suffix.lower()
    if ext not in VALID_VIDEO_EXTENSIONS:
        kinds = ", ".join(sorted(VALID_VIDEO_EXTENSIONS))
        raise click.BadParameter(
            _("Invalid video format: '")
            + ext
            + _("'. Must be one of: ")
            + kinds
        )
    return value


def validate_extension(
    ctx, param, value, allowed_exts=(".srt", ".txt")
):
    if value:
        ext = Path(value).suffix.lower()
        if ext not in allowed_exts:
            allowed = ", ".join(allowed_exts)
            raise click.BadParameter(
                _("File must end with: ") + allowed
            )
    return value


def validate_srt(ctx, param, value):
    return validate_extension(ctx, param, value, (".srt",))


def validate_txt(ctx, param, value):
    return validate_extension(ctx, param, value, (".txt",))
