#!/usr/bin/env python3
"""
Subtitle burn-in using ffmpeg drawtext filter.
Supports multi-line text with a single unified box.

Style specifications: see STYLE_GUIDE.md in this directory.
"""

import re
import sys
import subprocess
import unicodedata
import tempfile
from pathlib import Path


def normalize_path(path_str):
    """NFD/NFC 정규화 불일치 해결을 위한 경로 정규화"""
    path = Path(path_str)
    if path.exists():
        return str(path)

    # NFC/NFD 둘 다 시도
    for form in ['NFC', 'NFD']:
        normalized = Path(unicodedata.normalize(form, str(path)))
        if normalized.exists():
            return str(normalized)

    # 디렉토리 순회로 찾기
    parent = path.parent
    if parent.exists():
        target = unicodedata.normalize('NFC', path.name)
        for item in parent.iterdir():
            if unicodedata.normalize('NFC', item.name) == target:
                return str(item)

    return str(path)  # 찾지 못하면 원본 반환


def parse_srt(srt_path):
    """Parse SRT file and return list of cues"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n\d+\n|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)

    cues = []
    for idx, start, end, text in matches:
        start_sec = timecode_to_seconds(start)
        end_sec = timecode_to_seconds(end)
        text_clean = text.strip().replace('\n', ' ')
        cues.append({
            'index': int(idx),
            'start': start_sec,
            'end': end_sec,
            'text': text_clean
        })

    return cues


def timecode_to_seconds(tc):
    """Convert SRT timecode to seconds: 00:01:23,456 -> 83.456"""
    tc = tc.replace(',', '.')
    parts = tc.split(':')
    h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
    return h * 3600 + m * 60 + s


def escape_drawtext(text):
    """Escape special characters for ffmpeg drawtext filter"""
    # Escape for ffmpeg filter
    text = text.replace('\\', '\\\\')
    text = text.replace("'", "'\\''")
    text = text.replace(':', '\\:')
    text = text.replace('%', '\\%')
    return text


def wrap_text(text, max_chars=40):
    """Wrap text to multiple lines if needed"""
    if len(text) <= max_chars:
        return text

    words = text.split()
    lines = []
    current_line = []
    current_len = 0

    for word in words:
        if current_len + len(word) + 1 <= max_chars:
            current_line.append(word)
            current_len += len(word) + 1
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_len = len(word)

    if current_line:
        lines.append(' '.join(current_line))

    # Limit to 2 lines max
    if len(lines) > 2:
        lines = lines[:2]
        lines[1] = lines[1][:max_chars-3] + '...' if len(lines[1]) > max_chars-3 else lines[1]

    return '\n'.join(lines)


def get_video_info(video_path):
    """Get video width, height, duration"""
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0',
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    width, height = map(int, result.stdout.strip().split(','))
    return width, height


def find_font():
    """Find suitable CJK font"""
    font_paths = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        '/System/Library/Fonts/AppleSDGothicNeo.ttc',
    ]

    for path in font_paths:
        if Path(path).exists():
            return path

    # Try fc-match
    try:
        result = subprocess.run(
            ['fc-match', '-f', '%{file}', 'NotoSansCJK'],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            return result.stdout.strip()
    except:
        pass

    return None


def build_drawtext_filter(cues, width, height, font_path):
    """Build ffmpeg drawtext filter chain"""

    # Calculate sizes based on resolution
    base_height = 1080
    scale = height / base_height

    font_size = int(38 * scale)
    box_padding = int(14 * scale)
    margin_bottom = int(160 * scale)
    max_chars = int(width * 0.8 / (font_size * 0.6))  # Approximate char width

    filters = []

    for cue in cues:
        text = wrap_text(cue['text'], max_chars)
        text_escaped = escape_drawtext(text)

        # drawtext filter with box
        f = (
            f"drawtext="
            f"text='{text_escaped}':"
            f"fontfile='{font_path}':"
            f"fontsize={font_size}:"
            f"fontcolor=white:"
            f"box=1:"
            f"boxcolor=black:"
            f"boxborderw={box_padding}:"
            f"x=(w-text_w)/2:"
            f"y=h-text_h-{margin_bottom}:"
            f"enable='between(t,{cue['start']:.3f},{cue['end']:.3f})'"
        )
        filters.append(f)

    return ','.join(filters)


def main():
    if len(sys.argv) < 3:
        print("Usage: python burnin_drawtext.py <video_path> <srt_path> [output_path]")
        sys.exit(1)

    video_path = normalize_path(sys.argv[1])
    srt_path = normalize_path(sys.argv[2])
    output_path = sys.argv[3] if len(sys.argv) > 3 else None

    if not Path(video_path).exists():
        print(f"Error: Video not found: {video_path}")
        sys.exit(1)

    if not Path(srt_path).exists():
        print(f"Error: SRT not found: {srt_path}")
        sys.exit(1)

    print(f"\n=== Drawtext Burn-in ===")
    print(f"Video: {video_path}")
    print(f"Subtitle: {srt_path}")

    # Get video info
    width, height = get_video_info(video_path)
    print(f"Resolution: {width}x{height}")

    # Find font
    font_path = find_font()
    if not font_path:
        print("Error: No CJK font found")
        sys.exit(1)
    print(f"Font: {font_path}")

    # Parse SRT
    cues = parse_srt(srt_path)
    print(f"Subtitles: {len(cues)} cues")

    # Build filter
    vf = build_drawtext_filter(cues, width, height, font_path)

    # Set output path
    if not output_path:
        video_file = Path(video_path)
        output_dir = Path("burnin_output")
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{video_file.stem}_burnin.mp4")
    else:
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"Output: {output_path}")
    print(f"\nProcessing...")

    # Use filter_complex_script for large filters (avoid argument list too long)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        # Write filter as filter_complex format
        f.write(f"[0:v]{vf}[out]")
        filter_script = f.name

    try:
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-filter_complex_script', filter_script,
            '-map', '[out]',
            '-map', '0:a?',
            '-c:a', 'copy',
            output_path
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        print(f"\n=== Complete ===")
        print(f"Output: {output_path}")
        print(f"Size: {size_mb:.1f} MB")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr.decode()}")
        sys.exit(1)
    finally:
        # Clean up temp file
        Path(filter_script).unlink(missing_ok=True)


if __name__ == '__main__':
    main()
