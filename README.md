# ** in progress **

# 🎬 Subtitle Extractor & Translator CLI

A powerful command-line tool to extract, transcribe, and translate subtitles from video files using `ffmpeg`, OpenAI's Whisper, and `deep-translator`.

---

## 🚀 Features

- ✅ Extract embedded subtitle tracks from video files (`ffmpeg`)
- 🎙️ Transcribe audio to subtitles if no subtitles are embedded (Whisper)
- 🌍 Translate subtitles to over 100+ languages using Google Translate
- 📁 Outputs standard `.srt` files for use in media players or editors

---

## 🛠 Installation

Clone the repository and install dependencies in a virtual environment:

```bash
git clone https://github.com/kavancamp/subtitle-extractor-translator
cd subtitle-extractor-translator

python -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```
## ⚙️ Requirements
Python 3.8+
ffmpeg (must be installed and available in your PATH)
ffprobe (usually included with ffmpeg)
Whisper model (downloaded automatically by the whisper library)

Testing:
pytest 
Linting & Formatting:
black 
flake8
isort

## 📦 CLI Usage
Transcribe audio from a video file to .srt subtitles:
```bash
python cli.py transcribe input.mp4 --language en --output output.srt
```
## 📺 Extract Embedded Subtitles
Extract subtitle tracks if embedded in the video:
```bash
python cli.py extract input.mp4 --output output.srt
```

## 🌐 Translate Subtitles
Translate an .srt subtitle file into another language:
```bash
python cli.py translate subtitles.srt --target-lang es --output subtitles_es.srt
```

### Whisper Model Sizes
You can specify a model with --model:
tiny
base (default)
small
medium
large
turbo (OpenAI API required)

### TODO:
- Store metadata/transcriptions in SQL
- Offer CLI mode and optional Web UI

MIT License © 2025 Keenah VanCampenhout
