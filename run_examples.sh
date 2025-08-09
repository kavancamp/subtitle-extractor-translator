#!/usr/bin/env bash
set -euo pipefail

# --- Config ---
VENV_DIR="${VENV_DIR:-venv}"     # your venv dir; change if needed
PY="${PY:-python}"               # or python3
APP="${APP:-cli.py}"             # entrypoint script

# --- Bootstrap ---
if [[ -d "$VENV_DIR" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
fi

export APP_LANG="${APP_LANG:-en}"

# temp file to capture output for assertions
OUT="$(mktemp)"
trap 'rm -f "$OUT"' EXIT

# --- Helpers ---
press_enter() {
  read -r -p "Press Enter to continue..."
  echo
}

assert_contains() {
  # $1 = expected text, $2 = filename with output
  if ! grep -qE "$1" "$2"; then
    echo "❌ Assertion failed: expected output to contain: $1"
    echo "---- output ----"
    cat "$2" || true
    echo "----------------"
    exit 1
  fi
  echo "✅ Found: $1"
}

hr() { printf "\n%s\n\n" "──────────────────────────────────────────────"; }

# ------------------------------------------------------------------------------
# 1) English help (default)
# ------------------------------------------------------------------------------
echo "=== 1) English Help Screen ==="
set +e
"$PY" "$APP" --help | tee "$OUT"
set -e
assert_contains "Usage:" "$OUT"
assert_contains "Commands:" "$OUT"
hr
press_enter

# ------------------------------------------------------------------------------
# 2) Spanish help (env APP_LANG=es)
# ------------------------------------------------------------------------------
echo "=== 2) Spanish Help Screen (via env var) ==="
set +e
APP_LANG=es "$PY" "$APP" --help | tee "$OUT"
set -e
# Adjust the check to a Spanish word that exists in your .po/.mo
# "Transcripción" is shown in your earlier output
assert_contains "Transcripción" "$OUT"
hr
press_enter

# ------------------------------------------------------------------------------
# 3) Invalid Video for Transcription
# ------------------------------------------------------------------------------
echo "=== 3) Invalid Video for Transcription (Expect error) ==="
set +e
"$PY" "$APP" transcribe nonexistent.mp4 2>&1 | tee "$OUT"
set -e
assert_contains "Invalid value for 'VIDEO_PATH'" "$OUT"
hr
press_enter

# ------------------------------------------------------------------------------
# 4) Invalid Video for Extraction
# ------------------------------------------------------------------------------
echo "=== 4) Invalid Video for Extraction (Expect error) ==="
set +e
"$PY" "$APP" extract nonexistent.mp4 2>&1 | tee "$OUT"
set -e
assert_contains "Invalid value for 'VIDEO_PATH'" "$OUT"
hr
press_enter

# ------------------------------------------------------------------------------
# 5) Invalid SRT for Translation
# ------------------------------------------------------------------------------
echo "=== 5) Invalid SRT for Translation (Expect error) ==="
set +e
"$PY" "$APP" translate missing.srt --target-lang fr 2>&1 | tee "$OUT"
set -e
assert_contains "Invalid value for 'SRT_FILE'" "$OUT"
hr
press_enter

# Create a valid 2s MP4 with silent audio (if ffmpeg is available)
if command -v ffmpeg >/dev/null 2>&1; then
  TEST_MP4="tests/test_valid.mp4"
  echo "=== Creating a valid test MP4 ==="
  ffmpeg -hide_banner -loglevel error \
    -f lavfi -i color=c=black:s=320x240:d=2 \
    -f lavfi -i anullsrc=r=44100:cl=stereo \
    -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest \
    -y "$TEST_MP4"
  echo "Created: $TEST_MP4"
else
  echo "ffmpeg not found; skipping media synthesis."
  TEST_MP4="tests/test.mp4"  # fallback to whatever is there
fi


# ------------------------------------------------------------------------------
# 7) Fallback Transcription path (no embedded subs)
#     – This will likely error unless whisper is installed & model is available.
#     – We still run it and don’t fail the script (|| true).
# ------------------------------------------------------------------------------
echo "=== 7) Fallback Transcription (no subtitles) ==="
set +e
python cli.py extract "$TEST_MP4" --output out.srt --model tiny --language en || true
set -e
# Don't assert success here; environment may not have whisper installed.
echo "ℹ️  Ran extract for fallback path (may fail without whisper)."
hr
press_enter

# ------------------------------------------------------------------------------
# 8) Transcription with model=base (may fail if whisper missing)
# ------------------------------------------------------------------------------
echo "=== 8) Transcription with model=base ==="
set +e
"$PY" "$APP" transcribe "$TEST_MP4" --model base --language en --output transcribed.srt 2>&1 | tee "$OUT"
set -e
echo "ℹ️  Ran transcribe (may fail without whisper)."
hr
press_enter

# ------------------------------------------------------------------------------
# 9) Translation of a sample SRT
# ------------------------------------------------------------------------------
echo "=== 9) Translation of sample SRT ==="
cat > sample.srt <<'SRT'
1
00:00:01,000 --> 00:00:02,000
Hello world

SRT
set +e
"$PY" "$APP" translate sample.srt --target-lang es --output sample_es.srt 2>&1 | tee "$OUT"
set -e
# deep-translator may not be installed locally; don't assert success
echo "ℹ️  Ran translate (may fail without deep-translator)."
hr
press_enter

# ------------------------------------------------------------------------------
# 10) Interactive REPL basic: open, 'help', exit
# ------------------------------------------------------------------------------
echo "=== 10) Interactive: open, show help, exit ==="
set +e
timeout 8s "$PY" "$APP" <<'EOF' | tee "$OUT"
help
exit
EOF
set -e
assert_contains "Usage:" "$OUT"
assert_contains ">> " "$OUT"
hr
press_enter

# ------------------------------------------------------------------------------
# 11) Interactive: command help
# ------------------------------------------------------------------------------
echo "=== 11) Interactive: help for a command ==="
set +e
timeout 8s "$PY" "$APP" <<'EOF' | tee "$OUT"
help transcribe
exit
EOF
set -e
assert_contains "Transcribe subtitles" "$OUT"
assert_contains ">> " "$OUT"
hr
press_enter

# ------------------------------------------------------------------------------
# 12) Interactive: invalid subcommand; remain in REPL
# ------------------------------------------------------------------------------
echo "=== 12) Interactive: invalid subcommand error ==="
set +e
timeout 8s "$PY" "$APP" <<'EOF' | tee "$OUT"
wat
exit
EOF
set -e
# we at least want to see the prompt again:
assert_contains ">> " "$OUT"
hr
press_enter

# ------------------------------------------------------------------------------
# 13) Interactive: failing command then recover with 'help'
#     (This uses Click's error formatting if you implemented Option A)
# ------------------------------------------------------------------------------
echo "=== 13) Interactive: failing command then recover ==="
set +e
timeout 8s "$PY" "$APP" <<'EOF' | tee "$OUT"
transcribe nofile.mp4
help
exit
EOF
set -e
# Accept either Click-lingo or generic error message
if grep -q "Invalid value for 'VIDEO_PATH'" "$OUT"; then
  echo "✅ Found: Invalid value for 'VIDEO_PATH'"
elif grep -q "Error: File 'nofile.mp4' does not exist." "$OUT"; then
  echo "✅ Found: generic error message"
else
  echo "❌ Expected an error about VIDEO_PATH or missing file."
  cat "$OUT"
  exit 1
fi
assert_contains "Usage:" "$OUT"
assert_contains ">> " "$OUT"
hr
press_enter

echo "=== Done! Check generated files if present: out.srt, transcribed.srt, sample_es.srt ==="
