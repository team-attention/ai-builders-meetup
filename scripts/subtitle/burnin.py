#!/usr/bin/env python3
"""
SRT 자막을 ASS 형식으로 변환하고 ffmpeg으로 burn-in 하는 스크립트
BizCafe 스타일 가이드 기반: SUBTITLE_DESIGN_GUIDE.md
"""

import re
import sys
import subprocess
import unicodedata
from pathlib import Path


def parse_srt(srt_path):
    """SRT 파일 파싱"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # SRT 패턴: 번호, 시간, 텍스트
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n\d+\n|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)

    cues = []
    for idx, start, end, text in matches:
        # ASS 형식으로 변환: , -> .
        start_ass = start.replace(',', '.')
        end_ass = end.replace(',', '.')
        # 줄바꿈을 ASS 형식으로
        text_ass = text.strip().replace('\n', '\\N')

        cues.append({
            'index': int(idx),
            'start': start_ass,
            'end': end_ass,
            'text': text_ass
        })

    return cues


def format_ass_time(time_str):
    """00:00:00.000 -> 0:00:00.00 (ASS 형식)"""
    parts = time_str.replace('.', ':').split(':')
    h, m, s, ms = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    cs = ms // 10  # centiseconds
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def estimate_text_size(text, font_size=18):
    """
    텍스트 크기 추정 (대략적)
    실제로는 폰트 메트릭을 사용해야 정확하지만, 근사치로 계산
    """
    lines = text.split('\\N')

    # 한글/영문 혼합 고려
    max_chars = 0
    for line in lines:
        # 대략적으로 한글은 1.5배, 영문은 0.6배 너비
        char_count = 0
        for char in line:
            if ord(char) > 127:  # 한글/한자 등
                char_count += 1.5
            else:
                char_count += 0.6
        max_chars = max(max_chars, char_count)

    text_width = max_chars * font_size * 0.6
    text_height = len(lines) * font_size * 1.4  # 줄 간격 포함

    return text_width, text_height


def generate_ass(cues, video_width, video_height, output_path):
    """
    ASS 파일 생성 (BizCafe 스타일)
    - 멀티라인 자막을 단일 검은 박스로 감싸기
    - bottom-center 정렬 (Alignment=2)
    """

    # 기본 설정 (1440x810 기준)
    base_width = 1440
    base_height = 810

    # 스케일 계산
    scale_x = video_width / base_width
    scale_y = video_height / base_height
    scale = min(scale_x, scale_y)  # 더 작은 축 기준

    font_size = int(18 * scale)
    pad_x = int(10 * scale)
    pad_y = int(6 * scale)
    margin_v = int(40 * scale)

    # 화면 중앙 X, 하단 기준 Y
    cx = video_width // 2
    y_base = video_height - margin_v

    # ASS 헤더
    ass_header = f"""[Script Info]
Title: BizCafe Subtitles
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: BizCafeBG,Noto Sans CJK KR,{font_size},&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,0,0,{margin_v},1
Style: BizCafeText,Noto Sans CJK KR,{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,0,0,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []

    for cue in cues:
        start = format_ass_time(cue['start'])
        end = format_ass_time(cue['end'])
        text = cue['text']

        # 텍스트 크기 측정
        text_w, text_h = estimate_text_size(text, font_size)

        # 박스 크기 계산
        box_w = text_w + 2 * pad_x
        box_h = text_h + 2 * pad_y
        bw2 = int(box_w / 2)  # 반 너비
        bh = int(box_h)       # 전체 높이

        # BG 이벤트 (Layer 0) - 검은 박스
        # 벡터 드로잉으로 직사각형 그리기
        bg_event = (
            f"Dialogue: 0,{start},{end},BizCafeBG,,0,0,0,,"
            f"{{\\an2\\pos({cx},{y_base})\\p1\\bord0\\shad0\\1c&H000000&}}"
            f"m -{bw2} -{bh} l {bw2} -{bh} l {bw2} 0 l -{bw2} 0"
        )
        events.append(bg_event)

        # TEXT 이벤트 (Layer 1) - 흰색 텍스트
        text_event = (
            f"Dialogue: 1,{start},{end},BizCafeText,,0,0,0,,"
            f"{{\\an2\\pos({cx},{y_base})}}{text}"
        )
        events.append(text_event)

    # 파일 쓰기
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ass_header)
        f.write('\n'.join(events))

    print(f"ASS 파일 생성 완료: {output_path}")
    print(f"  - 해상도: {video_width}x{video_height}")
    print(f"  - 자막 개수: {len(cues)}개")
    print(f"  - 폰트 크기: {font_size}px")
    print(f"  - 패딩: {pad_x}px x {pad_y}px")
    print(f"  - 하단 마진: {margin_v}px")

    return output_path


def main():
    if len(sys.argv) < 3:
        print("Usage: python burnin_subtitle.py <video_path> <srt_path> [output_path]")
        sys.exit(1)

    video_path = sys.argv[1]
    srt_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None

    # 파일명 NFC 정규화
    video_path = unicodedata.normalize('NFC', video_path)
    srt_path = unicodedata.normalize('NFC', srt_path)

    # 파일 존재 확인
    if not Path(video_path).exists():
        print(f"Error: 영상 파일을 찾을 수 없습니다: {video_path}")
        sys.exit(1)

    if not Path(srt_path).exists():
        print(f"Error: 자막 파일을 찾을 수 없습니다: {srt_path}")
        sys.exit(1)

    print(f"\n=== 자막 Burn-in 시작 ===")
    print(f"입력 영상: {video_path}")
    print(f"입력 자막: {srt_path}")

    # 영상 해상도 가져오기
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height', '-of', 'csv=p=0', video_path],
            capture_output=True, text=True, check=True
        )
        width, height = map(int, result.stdout.strip().split(','))
    except Exception as e:
        print(f"Error: 영상 정보를 가져올 수 없습니다: {e}")
        sys.exit(1)

    print(f"영상 해상도: {width}x{height}")

    # ASS 파일 생성
    ass_path = str(Path(srt_path).with_suffix('.ass'))
    print(f"\n=== SRT -> ASS 변환 중 ===")

    try:
        cues = parse_srt(srt_path)
        generate_ass(cues, width, height, ass_path)
    except Exception as e:
        print(f"Error: ASS 파일 생성 실패: {e}")
        sys.exit(1)

    # 출력 경로 설정
    if not output_path:
        video_stem = Path(video_path).stem
        output_dir = Path(video_path).parent / "burnin_output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{video_stem}_burnin.mp4")

    print(f"\n=== ffmpeg Burn-in 시작 ===")
    print(f"출력 경로: {output_path}")

    # ffmpeg 명령 실행
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f"ass={ass_path}",
            '-c:a', 'copy',
            '-y',
            output_path
        ]

        subprocess.run(cmd, check=True)

        print(f"\n=== 완료 ===")
        print(f"출력 파일: {output_path}")

        # 파일 크기 확인
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        print(f"파일 크기: {size_mb:.1f} MB")

    except subprocess.CalledProcessError as e:
        print(f"Error: ffmpeg 실행 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
