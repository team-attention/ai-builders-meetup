# Subtitle Generation Guide

Complete guide for generating Korean subtitles from video files.

## Overview

This guide covers the 3-step pipeline for generating high-quality Korean subtitles:

1. **Transcription** - Extract speech to text using Whisper AI
2. **Cleaning** - Remove duplicates and hallucinations
3. **Correction** - Fix terminology using reference materials

## Target Video

- **File**: `/home/junchan/github/ai-builders-meetup/2-echo-delta/videos/meetup_02_건호님.mov`
- **Size**: 160MB
- **Speaker**: 신건호
- **Reference PDF**: `/home/junchan/github/ai-builders-meetup/2-echo-delta/slides/4-신건호-AI Builder Meetup_DAY1 B2B 신건호_251229_VF(배포용).pdf`
- **Output**: `/home/junchan/github/ai-builders-meetup/2-echo-delta/videos/meetup_02_건호님.srt`

## Prerequisites

### System Requirements

Since this is a WSL2/Linux environment (not Apple Silicon), we need to use `openai-whisper` instead of `mlx-whisper`.

### Installation

```bash
cd /home/junchan/github/ai-builders-meetup

# Activate virtual environment
source .venv/bin/activate

# Install whisper (if not already installed)
pip install openai-whisper

# Optional: Install PDF processing (for better term extraction)
pip install PyPDF2 pdfplumber
```

## Step-by-Step Instructions

### Step 1: Transcription

Generate initial subtitles from video using Whisper AI.

```bash
# Make script executable
chmod +x transcribe_건호님.py

# Run transcription (will take 5-10 minutes for 160MB file)
python transcribe_건호님.py
```

**Expected output:**
- File: `2-echo-delta/videos/meetup_02_건호님.srt`
- Segments: ~150-200 (depending on video length)
- Time: 5-10 minutes on CPU, 2-3 minutes on GPU

**What this does:**
- Loads Whisper large-v3 model
- Transcribes audio to Korean text
- Generates timestamped SRT file
- May contain duplicates and hallucinations

### Step 2: Cleaning

Remove duplicates and common hallucinations.

```bash
# Make script executable
chmod +x subtitle_cleaner.py

# Clean the generated SRT
python subtitle_cleaner.py 2-echo-delta/videos/meetup_02_건호님.srt
```

**Expected output:**
- Overwrites the SRT file with cleaned version
- Removes: ~10-30% of segments
- Removes: "감사합니다", "[음악]", duplicates, etc.

**What this does:**
- Removes exact duplicate segments
- Filters out common hallucination patterns
- Removes empty or near-empty segments
- Maintains proper SRT indexing

### Step 3: Terminology Correction

Fix technical terms using reference PDF.

```bash
# Make script executable
chmod +x subtitle_corrector.py

# Correct terminology
python subtitle_corrector.py \
  2-echo-delta/videos/meetup_02_건호님.srt \
  "2-echo-delta/slides/4-신건호-AI Builder Meetup_DAY1 B2B 신건호_251229_VF(배포용).pdf"
```

**Expected output:**
- Overwrites SRT with corrected version
- Fixes: Common AI/B2B term mistranscriptions
- Example corrections:
  - "에이아이" → "AI"
  - "비투비" → "B2B"
  - "엘엘엠" → "LLM"

**What this does:**
- Applies common technical term corrections
- Uses reference PDF for context (if PDF parser installed)
- Standardizes terminology across the subtitle

## Quick Run (All Steps)

```bash
cd /home/junchan/github/ai-builders-meetup
source .venv/bin/activate

# Step 1: Transcribe
python transcribe_건호님.py

# Step 2: Clean
python subtitle_cleaner.py 2-echo-delta/videos/meetup_02_건호님.srt

# Step 3: Correct
python subtitle_corrector.py \
  2-echo-delta/videos/meetup_02_건호님.srt \
  "2-echo-delta/slides/4-신건호-AI Builder Meetup_DAY1 B2B 신건호_251229_VF(배포용).pdf"

# Done! Final file is at:
# 2-echo-delta/videos/meetup_02_건호님.srt
```

## Verification

After generation, verify the subtitle quality:

```bash
# Check segment count
grep -c "^[0-9]*$" 2-echo-delta/videos/meetup_02_건호님.srt

# View first few segments
head -20 2-echo-delta/videos/meetup_02_건호님.srt

# Search for potential issues
grep -i "음악\|박수\|감사합니다" 2-echo-delta/videos/meetup_02_건호님.srt
```

## Manual Review

After automated processing, manually review for:

1. **Name corrections**: Speaker names, company names
2. **Product names**: Specific tools, services mentioned
3. **Domain terms**: Industry-specific jargon
4. **Numbers**: Dates, statistics, percentages
5. **Timing**: Ensure segments don't overlap or have gaps

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'whisper'"

```bash
source .venv/bin/activate
pip install openai-whisper
```

### Issue: Transcription is very slow

- Use smaller model: Edit `transcribe_건호님.py` and change `model_name = "medium"` or `"small"`
- Expected times:
  - large-v3: 5-10 min (best quality)
  - medium: 3-5 min (good quality)
  - small: 1-2 min (acceptable quality)

### Issue: PDF terms not being extracted

- Install PDF library: `pip install PyPDF2 pdfplumber`
- Check PDF path is correct
- Alternatively, manually add terms to `subtitle_corrector.py`

### Issue: Too many segments removed in cleaning

- Edit `subtitle_cleaner.py` and adjust `hallucination_patterns`
- Review removed content before cleaning

## Files Generated

| File | Purpose | Size |
|------|---------|------|
| `transcribe_건호님.py` | Step 1 script | ~4KB |
| `subtitle_cleaner.py` | Step 2 script | ~3KB |
| `subtitle_corrector.py` | Step 3 script | ~5KB |
| `meetup_02_건호님.srt` | Final subtitle | ~20-40KB |

## Next Steps

After completing subtitle generation for 건호님:

1. Generate subtitles for remaining videos:
   - 서진님: `meetup_02_서진님.mov` (68MB)
   - 동훈님: `meetup_02_동훈님.mov` (153MB)
   - 동운님: `meetup_02_동운님.mov` (64MB)
   - 패널: `meetup_02_패널.mov` (542MB)

2. Consider English translation (future)

3. Upload to video hosting platform with subtitles

## Reference

- Whisper documentation: https://github.com/openai/whisper
- SRT format spec: https://en.wikipedia.org/wiki/SubRip
- Project structure: See `CLAUDE.md` in repository root
