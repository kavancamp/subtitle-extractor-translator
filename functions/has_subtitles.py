import gettext
import json
import subprocess

_ = gettext.gettext


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
        print(_(f"⚠️ ffprobe error: {e}"))
        return False
    except json.JSONDecodeError as e:
        print(_(f"⚠️ JSON decode error: {e}"))
        return False
