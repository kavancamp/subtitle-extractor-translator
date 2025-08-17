import json
import subprocess

from functions.i18n import _

FFPROBE = "ffprobe"


def has_subtitles(ctx, file_path: str) -> bool:
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-of",
                "json",
                "-show_streams",
                file_path,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if not proc.stdout.strip():
            if proc.stderr:
                print("⚠️ ffprobe stderr: " + proc.stderr.strip())
            return False

        data = json.loads(proc.stdout)
        streams = data.get("streams", [])
        return any(s.get("codec_type") == "subtitle" for s in streams)
    except FileNotFoundError:
        print("⚠️ {ffprobe}" + _(" not found in PATH"))
        return False
    except Exception as e:
        print("⚠️ ffprobe error: " + str(e))
        return False
