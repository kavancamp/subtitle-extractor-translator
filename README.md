# 🎬 Subtitle Extractor & Translator CLI  ![dynamic badge](https://github.com/kavancamp/subtitle-extractor-translator/actions/workflows/ci.yaml/badge.svg)

### A powerful command-line tool to **extract**, **transcribe**, and **translate** subtitles from audio and video files using `ffmpeg`, OpenAI's Whisper, and `deep-translator`.


## 🚀 Features

- ✅ Extract embedded subtitle tracks from audio and video files `ffmpeg/ffprobe`  
- 🎙️ Transcribe audio to subtitles if no subtitles are embedded `Whisper`
- 🌍 Translate to over 100+ languages Google Translate via `deep-translator`
- 🧹 Clean `.srt` or `.txt` to plain txt with no timestamps and empty lines removed
- 📦 Outputs standard `.srt` files for use in media players or editors
- 📦 Automatic `.txt` output when using `--clean` alongside `.srt`
- 🗣️ CLI Lang (set with `--lang` or `APP_LANG`)
- 🧪 Solid test suite with coverage (pytest + coverage)


##  Why ⁉️
Have you ever found a fascinating foreign-language video with no subtitles—or worse, with subtitles you can’t translate or reuse? As a software engineer and As a K-drama connoisseur, I got tired of bouncing between tools that only half-solved the problem: one to rip subtitles, another to transcribe audio, and a third to translate the results. They were clunky, inconsistent, or required complex workflows.

I built this project to create a unified, developer-friendly tool that handles all three steps—extract, transcribe, and translate—with a single command-line interface. Whether you're archiving media, studying languages, or supporting accessibility, this tool saves you time by doing the hard parts automatically. And because it uses open-source tools like ffmpeg, OpenAI’s Whisper, and deep-translator under the hood, it remains powerful and adaptable without vendor lock-in.

Now, I can turn any video into a clean .srt subtitle file in my preferred language in seconds—and so can you. Hope it saves you a bunch of time too. 💜


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
- Python 3.8+
- ffmpeg & ffprobe in PATH
    - macOS: brew install ffmpeg
    - Ubuntu/Debian: sudo apt-get install ffmpeg
    - Windows (scoop): scoop install ffmpeg
- For transcription: pip install openai-whisper
- For translation: pip install deep-translator
Note: deep-translator uses Google Translate under the hood and may hit rate limits on large files; batching or caching is recommended for heavier workloads.
#### Testing:
- pytest 
#### Linting & Formatting:
- black 
- flake8
- isort


# 🖥 CLI Usage

## ✒️ Transcribe audio/video → `.srt`
```bash
python cli.py transcribe input.mp4 --language en --model base --output output.srt

```
- Language: language hint for Whisper (e.g., en, es)
- Models: tiny, base (default), small, medium, large, turbo (API only) (default: base)
- Clean: convert .srt to a plain .txt (no indices/timestamps)

## 📺 Extract Embedded Subtitles → `.srt`
```bash
python cli.py extract input.mp4 --output output.srt
```
- Detects embedded subs; extracts first subtitle stream
  (falls back to Whisper for transcription if none are found)
- `--clean` additionally produces a '.txt' with only dialogue lines.

### 🌐 Translate an `.srt`
```bash
python cli.py translate subtitles.srt --target-lang es --output subtitles_es.srt
```
- Preserves indices, timing lines, and blanks; translates only dialogue text lines.
- `--clean` additionally produces a .txt with only dialogue lines.
- Translates using Google-Translator

### 🧹 Clean an existing `.srt` → plain text
```bash
python cli.py clean subtitles.srt --output clean.txt
```
- Removes timestamps, numbering, and empty lines.

---

### Whisper Model Sizes for 
You can specify a model with --model:
 - tiny
- base (default)
- small
- medium
- large
- turbo (OpenAI API required)


### 🌐 Interface Language
Set with --lang or APP_LANG:
Example:
```bash
APP_LANG=es python cli.py --help
python cli.py --lang fr --help
```
--lang currently set up for: bn, de, es, fr, haw, hi, hmn, ko, ru, ur \
APP_LANG=es - a temporary language change for a single run

### 🈳 Updating Translations
After editing CLI strings:
<sub>to cli.py and functions or if more languages are need for cli:</sub>
```bash
    python3 auto_translate.py \
    --source en \
    --langs bn,de,es,fr,haw,hi,ko,ru,ur,hmn
```

## 🧪 Testing, Linting, Formatting:
Run Test with coverage
```bash
pytest --cov=cli --cov=functions --cov-report=term
```
Format and linting:
```bash
black . --line-length=72
isort . --profile black --line-length=72
flake8 . --max-line-length=100 --ignore=E128,W503

```
CI runs on pushes/PRs via GitHub Actions (`.github/workflows/ci.yaml`).




## 📁 Project Structure

```text
subtitle-extractor-translator/
├─ .github/
│  └─ workflows/
│     └─ ci.yaml
├─ cli.py
├─ auto_translate.py              # updates messages.pot + compiles .po -> .mo
├─ clean.py                       # pre-push lint/format helper
├─ locales/
│  ├─ messages.pot
│  ├─ es/LC_MESSAGES/{messages.po,messages.mo}
│  ├─ fr/LC_MESSAGES/{messages.po,messages.mo}
│  ├── ...
├─ functions/
│  ├─ has_subtitles.py
│  ├─ validators.py
│  ├─ format_timestamps.py
│  └─ write.py                    # write_segments, clean_srt_file_to_txt
├─ tests/
│  ├─ test_cli.py
│   └── ...
├─ pyproject.toml                 # black, flake8, pytest config
├─ requirements.txt
└─ README.md
```

## 🔧 Troubleshooting

- **“Whisper is required for transcription…”**  
  Install: `pip install openai-whisper`.
- **“The 'deep-translator' package is required for translation.”**  
  Install: `pip install deep-translator`.
- **ffmpeg/ffprobe not found**  
  Ensure they’re installed and in `PATH` (see System Requirements).
- **Wrong file type (e.g., `.mov` for “saving a transcription”)**  
  The CLI validates input video types and writes outputs you specify. For best results:
  - Use a video input with a common extension (e.g., `.mp4`, `.mov`).
  - Choose output ending with `.srt` (for subtitles) or use `--clean` to additionally generate a `.txt`.




## Demo Commands
```bash
# Help screen in English
python cli.py --help

# Help screen in Spanish
APP_LANG=es python cli.py --help

# Extract embedded subs
python cli.py extract sample.mp4 --output sample.srt

# Fallback transcription if no subs found
python cli.py extract sample.mp4 --clean --output sample.srt

# Transcribe directly
python cli.py transcribe sample.mp4 --language en --model base --output sample.srt

# Translate SRT to Spanish
python cli.py translate sample.srt --target-lang es --output sample_es.srt

# Clean SRT to TXT
python cli.py clean sample.srt --output clean.txt
```

## 🤝 Contributing
<sub> 🗺 Roadmap / Ideas </sub>

- Store metadata + transcripts in SQLite (searchable archive)
- Optional Web UI 
- Smarter language detection & batching for translator
- Robust stream selection (`-map 0:s:?` with interactive/auto disambiguation)

# 📜 License

MIT License © 2025 Keenah VanCampenhout

---