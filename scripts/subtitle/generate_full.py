#!/usr/bin/env python3
"""
Full Subtitle Generation Pipeline
Runs all 3 steps: Transcribe -> Clean -> Correct
"""
import time
import os
import sys
import re

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def parse_srt(content):
    """Parse SRT content into list of segments"""
    blocks = content.strip().split("\n\n")
    segments = []

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            try:
                index = int(lines[0])
                timestamp = lines[1]
                text = "\n".join(lines[2:])
                segments.append({
                    'index': index,
                    'timestamp': timestamp,
                    'text': text
                })
            except (ValueError, IndexError):
                continue

    return segments

def write_srt(segments, output_path):
    """Write segments to SRT file"""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n")
            f.write(f"{seg['timestamp']}\n")
            f.write(f"{seg['text']}\n\n")

# ==============================================================================
# STEP 1: TRANSCRIPTION
# ==============================================================================

def step1_transcribe(video_path, output_path, model_name="large-v3"):
    """Step 1: Generate subtitles using Whisper"""
    print("\n" + "=" * 70)
    print("STEP 1: TRANSCRIPTION")
    print("=" * 70)
    print(f"Video: {video_path}")
    print(f"Model: {model_name}")

    # Try to import whisper
    try:
        import whisper
        use_mlx = False
    except ImportError:
        try:
            import mlx_whisper as whisper
            use_mlx = True
        except ImportError:
            print("\nError: Neither openai-whisper nor mlx-whisper is installed")
            print("Please install: pip install openai-whisper")
            return None

    print(f"Using: {'mlx-whisper' if use_mlx else 'openai-whisper'}")

    start_time = time.time()

    # Load and transcribe
    print("Loading model...")
    if use_mlx:
        result = whisper.transcribe(
            video_path,
            path_or_hf_repo=f"mlx-community/whisper-{model_name}-mlx",
            language="ko",
            verbose=False
        )
    else:
        model = whisper.load_model(model_name.replace("-v3", ".v3") if "v3" in model_name else model_name)
        print("Transcribing... (this may take several minutes)")
        result = model.transcribe(video_path, language="ko", verbose=False)

    elapsed = time.time() - start_time

    # Write SRT
    print("Writing SRT file...")
    with open(output_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"], 1):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    segment_count = len(result['segments'])
    print(f"\nTranscription complete!")
    print(f"Segments: {segment_count}")
    print(f"Time: {elapsed:.1f}s ({elapsed/60:.1f} min)")

    return segment_count

# ==============================================================================
# STEP 2: CLEANING
# ==============================================================================

def step2_clean(srt_path):
    """Step 2: Clean duplicates and hallucinations"""
    print("\n" + "=" * 70)
    print("STEP 2: CLEANING")
    print("=" * 70)

    # Read SRT
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    segments = parse_srt(content)
    original_count = len(segments)
    print(f"Original segments: {original_count}")

    # Clean
    cleaned = []
    seen_texts = set()

    hallucination_patterns = [
        r"^감사합니다\.?$",
        r"^구독$",
        r"^좋아요$",
        r"^알림$",
        r"^\.\.\.+$",
        r"^\[?음악\]?$",
        r"^\[?박수\]?$",
        r"^\[?웃음\]?$",
        r"^$",
    ]

    for seg in segments:
        text = seg['text'].strip()

        if not text or text in seen_texts:
            continue

        is_hallucination = any(re.match(p, text, re.IGNORECASE) for p in hallucination_patterns)

        if not is_hallucination:
            cleaned.append(seg)
            seen_texts.add(text)

    # Write cleaned SRT
    write_srt(cleaned, srt_path)

    cleaned_count = len(cleaned)
    removed = original_count - cleaned_count

    print(f"Cleaned segments: {cleaned_count}")
    print(f"Removed: {removed} ({removed*100//original_count if original_count > 0 else 0}%)")

    return cleaned_count

# ==============================================================================
# STEP 3: CORRECTION
# ==============================================================================

def step3_correct(srt_path, pdf_path=None):
    """Step 3: Correct terminology"""
    print("\n" + "=" * 70)
    print("STEP 3: TERMINOLOGY CORRECTION")
    print("=" * 70)

    # Common corrections
    corrections = {
        "AI": ["에이아이", "에이 아이"],
        "B2B": ["비투비", "비 투 비"],
        "API": ["에이피아이", "에피아이"],
        "LLM": ["엘엘엠", "엘 엘 엠"],
        "RAG": ["래그", "랙"],
        "SaaS": ["사스", "싸스"],
        "SDK": ["에스디케이", "에스디 케이"],
        "GPT": ["지피티", "지 피 티"],
        "Claude": ["클로우드"],
        "OpenAI": ["오픈에이아이", "오픈 에이아이"],
    }

    if pdf_path and os.path.exists(pdf_path):
        print(f"Reference PDF: {os.path.basename(pdf_path)}")

    # Read SRT
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    segments = parse_srt(content)
    print(f"Segments to process: {len(segments)}")

    # Apply corrections
    corrected_count = 0
    for seg in segments:
        original = seg['text']
        text = original

        for correct, variations in corrections.items():
            for var in variations:
                pattern = re.compile(re.escape(var), re.IGNORECASE)
                text = pattern.sub(correct, text)

        if text != original:
            seg['text'] = text
            corrected_count += 1

    # Write corrected SRT
    write_srt(segments, srt_path)

    print(f"Corrections applied: {corrected_count} segments")

    return corrected_count

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("=" * 70)
    print("KOREAN SUBTITLE GENERATION PIPELINE")
    print("=" * 70)

    # Configuration
    VIDEO_PATH = "/home/junchan/github/ai-builders-meetup/2-echo-delta/videos/meetup_02_건호님.mov"
    OUTPUT_PATH = "/home/junchan/github/ai-builders-meetup/2-echo-delta/videos/meetup_02_건호님.srt"
    PDF_PATH = "/home/junchan/github/ai-builders-meetup/2-echo-delta/slides/4-신건호-AI Builder Meetup_DAY1 B2B 신건호_251229_VF(배포용).pdf"

    # Allow overrides from command line
    if len(sys.argv) >= 2:
        VIDEO_PATH = sys.argv[1]
        OUTPUT_PATH = os.path.splitext(VIDEO_PATH)[0] + ".srt"
    if len(sys.argv) >= 3:
        PDF_PATH = sys.argv[2]

    print(f"\nVideo: {VIDEO_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    if PDF_PATH:
        print(f"Reference: {PDF_PATH}")

    # Check video exists
    if not os.path.exists(VIDEO_PATH):
        print(f"\nError: Video not found: {VIDEO_PATH}")
        sys.exit(1)

    overall_start = time.time()

    # Step 1: Transcribe
    segment_count = step1_transcribe(VIDEO_PATH, OUTPUT_PATH)
    if segment_count is None:
        sys.exit(1)

    # Step 2: Clean
    cleaned_count = step2_clean(OUTPUT_PATH)

    # Step 3: Correct
    corrected_count = step3_correct(OUTPUT_PATH, PDF_PATH)

    overall_elapsed = time.time() - overall_start

    # Summary
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"Output file: {OUTPUT_PATH}")
    print(f"Initial segments: {segment_count}")
    print(f"After cleaning: {cleaned_count}")
    print(f"Corrections: {corrected_count}")
    print(f"Total time: {overall_elapsed/60:.1f} minutes")
    print("\nPlease review the subtitle file and make manual corrections as needed.")
    print("=" * 70)

if __name__ == "__main__":
    main()
