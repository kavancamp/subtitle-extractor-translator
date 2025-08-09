# 🎬 Subtitle Extractor & Translator CLI  ![dynamic badge](https://github.com/kavancamp/subtitle-extractor-translator/actions/workflows/ci.yaml/badge.svg)

### A powerful command-line tool to extract, transcribe, and translate subtitles from video files using `ffmpeg`, OpenAI's Whisper, and `deep-translator`.


## 🚀 Features

- ✅ Extract embedded subtitle tracks from video files (ffmpeg/ffprobe)
- 🎙️ Transcribe audio to subtitles if no subtitles are embedded (Whisper)
- 🌍 Translate subtitles to over 100+ languages Google Translate via deep-translator
- 📦 Outputs standard `.srt` files for use in media players or editors
- 🧪 Solid test suite with coverage (pytest + coverage)
- 🗣️ Internationalized CLI (set with --lang or APP_LANG)
- 💬 Interactive shell (shell command or launch with no args)
- 🧾 --no-timestamps option for clean, text-only .srt output

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
- ffmpeg (must be installed and available in your PATH)
- ffprobe (usually included with ffmpeg)
- openai-whisper
- deep-translator
#### Testing:
- pytest 
- Linting & Formatting:
- black 
- flake8
- isort



# 📦 CLI Usage
Transcribe audio from a video file to .srt subtitles:
```bash
python cli.py transcribe input.mp4 --language en --output output.srt
```
# 📺 Extract Embedded Subtitles
Extract subtitle tracks if embedded in the video:
```bash
python cli.py extract input.mp4 --output output.srt
```
# 🌐 Translate Subtitles
Translate an .srt subtitle file into another language:
```bash
python cli.py translate subtitles.srt --target-lang es --output subtitles_es.srt
```
### Whisper Model Sizes for 
You can specify a model with --model:
 - tiny
- base (default)
- small
- medium
- large
- turbo (OpenAI API required)

### Remove Timestamps
```bash
python cli.py transcribe input.mp4 --no-timestamps --output text_only.srt
python cli.py extract    input.mp4 --no-timestamps --output text_only.srt
```

### Language / i18n
Runtime language for messages:
CLI option: --lang es
or environment variable: APP_LANG=es
Example:
```bash
APP_LANG=es python cli.py --help
python cli.py --lang fr --help
```
### Updating CLI after changes to cli.py or functions
```bash
    python3 auto_translate.py --source en --langs bn,de,es,fr,haw,hi,ko,ru,ur,hmn

```

# 📁 Project Structure
```bash
subtitle-extractor-translator/
.
├── .github/     
│   ├── workflows/ 
│   │   └── ci.yaml       # CI github workflow
├── cli.py                
├── clean.py              # Pre-push linting and formatting script
├── README.md             # Project documentation
├── requirements.txt
├── pyproject.toml        # Setup for black flake8 pytest
├── auto_translate.py     # Script to update messages.pot and translations
├── locales/  
│   ├──messages.pot       # Translation content
│   ├── es/
│   │   └── LC_MESSAGES/
│   │        ├── messages.po
│   │        └── messages.mo
│   └── fr/
│        └── LC_MESSAGES/
│             ├── messages.po
│             └── messages.mo
├── tests/
│    ├── test_cli.py
│    ├── test_i18n.py
│    ├── test_subtitled.mov
│    └── test_valid.py
├── functions/
│    ├── has_subtitles.py
│    └── validators.py
└── run_examples.py         # extra testing
```



## 🤝 Contributing

#### Ideas:
- Store metadata/transcriptions in SQL
- Offer CLI mode and optional Web UI

MIT License © 2025 Keenah VanCampenhout
