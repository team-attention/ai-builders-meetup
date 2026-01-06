#!/usr/bin/env python3
"""
Subtitle Cleaner - Step 2 of subtitle generation pipeline
Removes duplicates and common hallucinations from SRT files
"""
import sys
import os
import re

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

def clean_segments(segments):
    """Remove duplicates and hallucinations"""
    cleaned = []
    seen_texts = set()

    # Common hallucination patterns
    hallucination_patterns = [
        r"^감사합니다\.?$",
        r"^구독$",
        r"^좋아요$",
        r"^알림$",
        r"^\.\.\.+$",
        r"^\[?음악\]?$",
        r"^\[?박수\]?$",
        r"^\[?웃음\]?$",
        r"^$",  # empty
        r"^자막\s*제작",
        r"^번역.*subtitle",
    ]

    for seg in segments:
        text = seg['text'].strip()

        # Skip empty
        if not text:
            continue

        # Skip if duplicate
        if text in seen_texts:
            continue

        # Skip if hallucination
        is_hallucination = False
        for pattern in hallucination_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                is_hallucination = True
                break

        # Skip very short repeated segments (likely noise)
        if len(text) < 5 and list(seen_texts).count(text) > 0:
            continue

        if not is_hallucination:
            cleaned.append(seg)
            seen_texts.add(text)

    return cleaned

def write_srt(segments, output_path):
    """Write segments to SRT file"""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n")
            f.write(f"{seg['timestamp']}\n")
            f.write(f"{seg['text']}\n\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python subtitle_cleaner.py <srt_file> [output_file]")
        print("If output_file is not specified, will overwrite input file")
        sys.exit(1)

    input_path = sys.argv[1]

    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    output_path = sys.argv[2] if len(sys.argv) >= 3 else input_path

    print("=" * 70)
    print("STEP 2: Subtitle Cleaning")
    print("=" * 70)
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print()

    # Read and parse
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    segments = parse_srt(content)
    original_count = len(segments)

    # Clean
    cleaned = clean_segments(segments)
    cleaned_count = len(cleaned)
    removed = original_count - cleaned_count

    # Write
    write_srt(cleaned, output_path)

    print(f"Original segments: {original_count}")
    print(f"Cleaned segments: {cleaned_count}")
    print(f"Removed: {removed} ({removed*100//original_count if original_count > 0 else 0}%)")
    print()
    print("Cleaning complete!")
    print()
    print("Next step: Run subtitle_corrector.py to fix terminology using PDF reference")

if __name__ == "__main__":
    main()
