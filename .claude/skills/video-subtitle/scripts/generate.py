#!/usr/bin/env python3
"""
Video Subtitle Generator
Generates Korean subtitles from video using Whisper AI
"""

import os
import sys
import time
from datetime import timedelta

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def generate_srt(video_path, output_path, language="ko", model="large-v3"):
    """Generate SRT subtitle file from video using Whisper"""
    try:
        import whisper
    except ImportError:
        print("Error: openai-whisper not installed")
        print("Please install: pip install openai-whisper")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("Step 1: Generating Subtitles with Whisper")
    print(f"{'='*60}")
    print(f"Video: {video_path}")
    print(f"Model: {model}")
    print(f"Language: {language}")

    # Load model
    print(f"\nLoading Whisper model '{model}'...")
    start_time = time.time()

    # Map model names
    model_name = model.replace("-v3", ".v3") if "v3" in model else model
    model_obj = whisper.load_model(model_name)

    # Transcribe
    print("Transcribing video (this may take several minutes)...")
    result = model_obj.transcribe(
        video_path,
        language=language,
        verbose=False
    )

    elapsed = time.time() - start_time

    # Generate SRT
    print(f"\nGenerating SRT file...")
    with open(output_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"], 1):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    print(f"\n{'='*60}")
    print(f"Subtitle generation complete!")
    print(f"{'='*60}")
    print(f"Output: {output_path}")
    print(f"Segments: {len(result['segments'])}")
    print(f"Duration: {elapsed/60:.1f} minutes")

    return len(result['segments'])

def clean_subtitles(srt_path):
    """Clean duplicates and hallucinations from SRT file"""
    print(f"\n{'='*60}")
    print("Step 2: Cleaning Subtitles")
    print(f"{'='*60}")

    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse SRT
    blocks = content.strip().split("\n\n")
    segments = []

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            try:
                index = int(lines[0])
                timestamp = lines[1]
                text = "\n".join(lines[2:])
                segments.append((index, timestamp, text))
            except ValueError:
                continue

    original_count = len(segments)

    # Remove duplicates and common hallucinations
    cleaned_segments = []
    seen_texts = set()
    hallucination_patterns = [
        "감사합니다",
        "구독",
        "좋아요",
        "알림",
        "...",
        "음악",
        "[음악]",
        "[박수]",
    ]

    for idx, timestamp, text in segments:
        # Skip if duplicate
        if text in seen_texts:
            continue

        # Skip if hallucination
        is_hallucination = False
        for pattern in hallucination_patterns:
            if text.strip() == pattern:
                is_hallucination = True
                break

        if not is_hallucination:
            cleaned_segments.append((idx, timestamp, text))
            seen_texts.add(text)

    # Rewrite SRT with cleaned segments
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (_, timestamp, text) in enumerate(cleaned_segments, 1):
            f.write(f"{i}\n{timestamp}\n{text}\n\n")

    removed = original_count - len(cleaned_segments)
    print(f"Original segments: {original_count}")
    print(f"Cleaned segments: {len(cleaned_segments)}")
    print(f"Removed: {removed} ({removed*100//original_count if original_count > 0 else 0}%)")

    return len(cleaned_segments)

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_subtitle.py <video_path> [output_path]")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    # Determine output path
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        # videos/raw/ → subtitles/raw/
        video_dir = os.path.dirname(video_path)
        video_basename = os.path.splitext(os.path.basename(video_path))[0]
        subtitles_dir = os.path.join(os.path.dirname(video_dir), 'subtitles', 'raw')
        os.makedirs(subtitles_dir, exist_ok=True)
        output_path = os.path.join(subtitles_dir, f"{video_basename}.srt")

    # Step 1: Generate subtitles
    segment_count = generate_srt(video_path, output_path, language="ko", model="large-v3")

    # Step 2: Clean subtitles
    cleaned_count = clean_subtitles(output_path)

    print(f"\n{'='*60}")
    print("All steps completed!")
    print(f"{'='*60}")
    print(f"Final file: {output_path}")
    print(f"Final segment count: {cleaned_count}")
    print("\nNext step: Review and manually correct technical terms")
    print("You can use the reference PDF to identify corrections needed.")

if __name__ == "__main__":
    main()
