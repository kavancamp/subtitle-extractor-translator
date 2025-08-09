#!/usr/bin/env bash
set -euo pipefail

# Activate virtual environment
source venv/bin/activate

export APP_LANG="${APP_LANG:-en}"

echo "=== 1. English Help Screen ==="
python cli.py --help || true
echo " "
read -p "Press Enter to continue..."
echo " "
echo "=== 2. Spanish Help Screen (via env var) ==="
APP_LANG=es python cli.py --help || true
echo " "
read -p "Press Enter to continue..."
echo " "
echo "=== 3. Invalid Video for Transcription (Expect error) ==="
python cli.py transcribe nonexistent.mp4 || true
echo " "
read -p "Press Enter to continue..."
echo " "
echo "=== 4. Invalid Video for Extraction (Expect error) ==="
python cli.py extract nonexistent.mp4 || true
echo " "
read -p "Press Enter to continue..."
echo " "
echo "=== 5. Invalid SRT for Translation (Expect error) ==="
python cli.py translate missing.srt --target-lang fr || true
echo " "
read -p "Press Enter to continue..."

# Prepare a dummy video file for testing
echo " "
echo "=== 6. Creating dummy MP4 for testing ==="
TEMP_VIDEO="dummy.mp4"
dd if=/dev/zero bs=1 count=1000 of="$TEMP_VIDEO" 2>/dev/null
echo " "
read -p "Press Enter to continue..."
echo " "
echo "=== 7. Fallback Transcription (no subtitles) ==="
python cli.py extract "$TEMP_VIDEO" --output out.srt --model tiny --language en || true
echo " "
read -p "Press Enter to continue..."
echo " "
echo "=== 8. Transcription with model=base ==="
echo " "
python cli.py transcribe "$TEMP_VIDEO" --model base --language en --output transcribed.srt || true
echo " "
read -p "Press Enter to continue..."
echo " "
echo "=== 9. Translation of sample SRT ==="
echo -e "1\n00:00:01,000 --> 00:00:02,000\nHello world\n" > sample.srt
python cli.py translate sample.srt --target-lang es --output sample_es.srt || true
echo " "
read -p "Press Enter to finish."
echo " "
echo "=== Done! Check generated files: out.srt, transcribed.srt, sample_es.srt ==="

