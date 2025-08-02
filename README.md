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



TODO:
- Store metadata/transcriptions in SQL

- Offer CLI mode and optional Web UI
