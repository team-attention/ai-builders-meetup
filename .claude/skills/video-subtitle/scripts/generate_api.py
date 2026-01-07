#!/usr/bin/env python3
"""
Video Subtitle Generator using OpenAI Whisper API
Generates Korean subtitles from video using OpenAI's cloud-based Whisper API

Features:
- Handles large files by splitting audio into chunks
- Automatic retry with exponential backoff
- Timestamp merging with overlap handling
- Auto-loads OPENAI_API_KEY from .env file
"""

import os
import sys
import time
import subprocess
import tempfile
import unicodedata
import glob
from datetime import timedelta
from pathlib import Path

# Load .env file if exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use environment variables directly

def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def extract_audio(video_path: str, output_path: str) -> str:
    """
    Extract audio from video using ffmpeg
    - 16kHz mono MP3 for Whisper optimization + size reduction
    """
    print(f"  Input: {video_path}")

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn",                    # No video
        "-acodec", "libmp3lame",  # MP3 codec
        "-ar", "16000",           # 16kHz (Whisper recommended)
        "-ac", "1",               # Mono
        "-b:a", "64k",            # Bitrate for size optimization
        "-y",                     # Overwrite
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ffmpeg error: {result.stderr}")
        raise RuntimeError("Failed to extract audio")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Output: {output_path} ({size_mb:.1f}MB)")

    return output_path


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def split_audio(audio_path: str, chunk_size_mb: int = 24) -> list:
    """
    Split audio into chunks smaller than API limit (25MB)
    Uses time-based splitting with 5-second overlap

    Returns:
        list of dict: [{"path": str, "start_time": float, "duration": float}, ...]
    """
    file_size = os.path.getsize(audio_path)
    file_size_mb = file_size / (1024 * 1024)

    # If file is small enough, no splitting needed
    if file_size_mb <= chunk_size_mb:
        duration = get_audio_duration(audio_path)
        return [{"path": audio_path, "start_time": 0.0, "duration": duration, "index": 0}]

    # Calculate chunk duration based on file size ratio
    total_duration = get_audio_duration(audio_path)
    bytes_per_second = file_size / total_duration
    chunk_duration = (chunk_size_mb * 1024 * 1024) / bytes_per_second

    # Split with overlap
    overlap = 5.0  # 5 seconds overlap
    chunks = []
    start_time = 0.0
    chunk_idx = 0
    temp_dir = tempfile.gettempdir()

    while start_time < total_duration:
        end_time = min(start_time + chunk_duration, total_duration)
        actual_duration = end_time - start_time

        chunk_path = os.path.join(temp_dir, f"whisper_chunk_{chunk_idx}.mp3")

        # Extract chunk using ffmpeg
        cmd = [
            "ffmpeg", "-i", audio_path,
            "-ss", str(start_time),
            "-t", str(actual_duration),
            "-acodec", "libmp3lame",
            "-ar", "16000",
            "-ac", "1",
            "-b:a", "64k",
            "-y",
            chunk_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        chunks.append({
            "path": chunk_path,
            "start_time": start_time,
            "duration": actual_duration,
            "index": chunk_idx
        })

        # Next chunk starts with overlap
        if end_time < total_duration:
            start_time = end_time - overlap
        else:
            break
        chunk_idx += 1

    return chunks


def transcribe_chunk(client, chunk_info: dict, max_retries: int = 3) -> dict:
    """
    Transcribe a single chunk using OpenAI Whisper API

    Returns:
        dict: {"segments": [...], "text": str, "chunk_info": dict}
    """
    for attempt in range(max_retries):
        try:
            with open(chunk_info["path"], "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ko",
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )

            # Handle response format
            if hasattr(response, 'segments'):
                segments = response.segments
            elif hasattr(response, 'model_dump'):
                data = response.model_dump()
                segments = data.get('segments', [])
            else:
                segments = []

            text = response.text if hasattr(response, 'text') else ""

            return {
                "segments": segments,
                "text": text,
                "chunk_info": chunk_info
            }

        except Exception as e:
            print(f"    Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"    Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise


def is_duplicate(seg1: dict, seg2: dict, time_threshold: float = 3.0) -> bool:
    """Check if two segments are duplicates (from overlap region)"""
    # Check time overlap
    if seg1["end"] <= seg2["start"] - time_threshold:
        return False

    # Check text similarity
    text1 = seg1["text"].replace(" ", "").strip()
    text2 = seg2["text"].replace(" ", "").strip()

    if not text1 or not text2:
        return False

    return text1 in text2 or text2 in text1 or text1 == text2


def merge_transcriptions(results: list) -> list:
    """
    Merge chunk results and apply timestamp offsets
    Removes duplicate segments from overlap regions
    """
    merged_segments = []

    for result in results:
        offset = result["chunk_info"]["start_time"]
        segments = result["segments"]

        for seg in segments:
            # Handle different segment formats
            if isinstance(seg, dict):
                start = seg.get("start", 0)
                end = seg.get("end", 0)
                text = seg.get("text", "").strip()
            else:
                start = getattr(seg, "start", 0)
                end = getattr(seg, "end", 0)
                text = getattr(seg, "text", "").strip()

            if not text:
                continue

            adjusted_segment = {
                "start": start + offset,
                "end": end + offset,
                "text": text
            }

            # Check for duplicates (from overlap region)
            if merged_segments:
                last_seg = merged_segments[-1]
                if is_duplicate(last_seg, adjusted_segment):
                    continue

            merged_segments.append(adjusted_segment)

    return merged_segments


def write_srt(segments: list, output_path: str) -> int:
    """Write segments to SRT file"""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = seg["text"]
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    return len(segments)


def main():
    """
    Main function for subtitle generation using OpenAI Whisper API

    Usage:
        python generate_subtitle_api.py <video_path> [output_path]

    Environment:
        OPENAI_API_KEY: OpenAI API key (or enter interactively)
    """
    if len(sys.argv) < 2:
        print("Usage: python generate_subtitle_api.py <video_path> [output_path]")
        sys.exit(1)

    video_path = sys.argv[1]

    # Handle NFD/NFC unicode normalization for Korean filenames
    if not os.path.exists(video_path):
        # Try to find file with glob pattern
        dir_path = os.path.dirname(video_path) or "."
        base_name = os.path.basename(video_path)
        # Normalize to NFC
        nfc_path = unicodedata.normalize('NFC', video_path)
        nfd_path = unicodedata.normalize('NFD', video_path)

        if os.path.exists(nfc_path):
            video_path = nfc_path
        elif os.path.exists(nfd_path):
            video_path = nfd_path
        else:
            # Try glob matching
            matches = glob.glob(os.path.join(dir_path, "*패널*"))
            if matches:
                video_path = matches[0]
                print(f"  Found file via glob: {video_path}")
            else:
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

    # Get API key
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: openai package not installed")
        print("Please install: pip install openai")
        sys.exit(1)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = input("Enter OpenAI API Key: ").strip()
        if not api_key:
            print("Error: API key is required")
            sys.exit(1)

    client = OpenAI(api_key=api_key)

    print(f"\n{'='*60}")
    print("OpenAI Whisper API Subtitle Generator")
    print(f"{'='*60}")
    print(f"Video: {video_path}")
    print(f"Output: {output_path}")

    start_time = time.time()

    # Create temporary directory for audio files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Step 1: Extract audio
        print(f"\n[Step 1/5] Extracting audio from video...")
        audio_path = os.path.join(temp_dir, "audio.mp3")
        extract_audio(video_path, audio_path)

        # Step 2: Split audio
        print(f"\n[Step 2/5] Splitting audio into chunks...")
        chunks = split_audio(audio_path)
        print(f"  Split into {len(chunks)} chunk(s)")

        # Step 3: Transcribe each chunk
        print(f"\n[Step 3/5] Transcribing with OpenAI Whisper API...")
        results = []
        for chunk in chunks:
            print(f"  Processing chunk {chunk['index']+1}/{len(chunks)} "
                  f"(starts at {chunk['start_time']:.1f}s)...")
            result = transcribe_chunk(client, chunk)
            results.append(result)

            # Clean up chunk file (except if it's the original audio)
            if chunk["path"] != audio_path and os.path.exists(chunk["path"]):
                os.remove(chunk["path"])

        # Step 4: Merge results
        print(f"\n[Step 4/5] Merging transcriptions...")
        merged = merge_transcriptions(results)
        print(f"  Total segments: {len(merged)}")

        # Step 5: Write SRT
        print(f"\n[Step 5/5] Writing SRT file...")
        count = write_srt(merged, output_path)

    elapsed = time.time() - start_time

    # Calculate estimated cost
    total_duration = sum(r["chunk_info"]["duration"] for r in results)
    estimated_cost = (total_duration / 60) * 0.006

    print(f"\n{'='*60}")
    print("Complete!")
    print(f"{'='*60}")
    print(f"Output: {output_path}")
    print(f"Segments: {count}")
    print(f"Processing time: {elapsed/60:.1f} minutes")
    print(f"Audio duration: {total_duration/60:.1f} minutes")
    print(f"Estimated cost: ${estimated_cost:.2f}")
    print(f"\nNext steps:")
    print(f"  1. Review: python subtitle_cleaner.py \"{output_path}\"")
    print(f"  2. Correct: python subtitle_corrector.py \"{output_path}\"")


if __name__ == "__main__":
    main()
