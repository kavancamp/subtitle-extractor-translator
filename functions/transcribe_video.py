import whisper


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    ms = int((s - int(s)) * 1000)
    return f"{h:02}:{m:02}:{int(s):02},{ms:03}"


def transcribe_video(video_path, model, language, output):
    """Run Whisper transcription and save output as SRT."""
    model_instance = whisper.load_model(model)
    result = model_instance.transcribe(video_path, language=language)

    with open(output, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"], start=1):
            f.write(f"{i}\n")
            f.write(
                f"{format_timestamp(segment['start'])} --> {format_timestamp(segment['end'])}\n"
            )
            f.write(f"{segment['text'].strip()}\n\n")
