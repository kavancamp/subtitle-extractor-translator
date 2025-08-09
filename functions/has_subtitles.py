# functions/has_subtitles.py
# -*- coding: utf-8 -*-
import gettext
import json
import subprocess


def has_subtitles(ctx, file_path: str) -> bool:
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
        print(_("⚠️ ffprobe error: {e}").format(e=e))
        return False
    except json.JSONDecodeError as e:
        print(_("⚠️ JSON decode error: {e}").format(e=e))
        return False
