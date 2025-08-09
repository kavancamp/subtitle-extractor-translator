# -*- coding: utf-8 -*-
import gettext
import json
import subprocess


def has_subtitles(file_path: str) -> bool:
    """Return True if the video contains any embedded subtitle streams."""
    _ = gettext.gettext
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_streams",
                "-select_streams",
                "s",
                file_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        return bool(data.get("streams"))
    except subprocess.CalledProcessError as e:
        print(_(f"⚠️ ffprobe error: {e}"))
        return False
    except json.JSONDecodeError as e:
        print(_(f"⚠️ JSON decode error: {e}"))
        return False
