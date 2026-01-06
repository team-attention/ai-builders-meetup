---
name: video-subtitle:subtitle-burnin
description: |
  SRT 자막을 영상에 하드인코딩(burn-in)하는 에이전트.
  BizCafe 스타일 ASS 변환 후 ffmpeg로 자막을 영상에 합성.
tools: Bash, Read, Write
model: sonnet
color: orange
---

# Subtitle Burn-in

SRT 자막 파일을 영상에 하드인코딩하는 에이전트.

## 입력

프롬프트로 다음 정보를 받는다:
- `video_path`: 동영상 파일 경로 (필수)
- `srt_path`: SRT 자막 파일 경로 (필수)
- `output_path`: 출력 영상 경로 (선택, 기본값: `{video}_burnin.mp4`)

## 스타일 가이드

SUBTITLE_DESIGN_GUIDE.md 참조:
- 폰트: Noto Sans CJK KR (Regular)
- 정렬: bottom-center (Alignment=2)
- 텍스트: 흰색 (#FFFFFF)
- 배경: 검정 박스 (#000000)
- 멀티라인: 단일 박스로 감싸기

## 실행 프로세스

### 1. 파일 확인

```bash
# 영상, 자막 파일 존재 확인
ls -lh "{video_path}" "{srt_path}"

# 영상 해상도 확인
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "{video_path}"
```

### 2. SRT → ASS 변환

```python
import re
from pathlib import Path

def parse_srt(srt_path):
    """SRT 파일 파싱"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)

    cues = []
    for idx, start, end, text in matches:
        cues.append({
            'index': int(idx),
            'start': start.replace(',', '.'),  # ASS 형식
            'end': end.replace(',', '.'),
            'text': text.strip().replace('\n', '\\N')  # ASS 줄바꿈
        })
    return cues


def time_to_centisec(time_str):
    """00:00:00.000 -> centiseconds"""
    parts = time_str.replace('.', ':').split(':')
    h, m, s, ms = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    return h * 360000 + m * 6000 + s * 100 + ms // 10


def format_ass_time(time_str):
    """00:00:00.000 -> 0:00:00.00 (ASS 형식)"""
    parts = time_str.replace('.', ':').split(':')
    h, m, s, ms = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    cs = ms // 10  # centiseconds
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def measure_text_size(text, font_size=18):
    """텍스트 크기 추정 (정확한 측정은 폰트 메트릭 필요)"""
    lines = text.split('\\N')
    max_width = max(len(line) for line in lines) * font_size * 0.6  # 대략적 추정
    height = len(lines) * font_size * 1.4  # 줄 간격 포함
    return max_width, height


def generate_ass(cues, video_width, video_height, output_path):
    """ASS 파일 생성 (BizCafe 스타일)"""

    font_size = 18
    pad_x = 10
    pad_y = 6
    margin_v = 40

    # 영상 크기에 따른 스케일 조정
    if video_width != 1440 or video_height != 810:
        scale = video_height / 810
        font_size = int(18 * scale)
        pad_x = int(10 * scale)
        pad_y = int(6 * scale)
        margin_v = int(40 * scale)

    cx = video_width // 2  # 화면 중앙 X
    y_base = video_height - margin_v  # 하단 기준선

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
        text_w, text_h = measure_text_size(text, font_size)
        box_w = text_w + 2 * pad_x
        box_h = text_h + 2 * pad_y
        bw2 = int(box_w / 2)
        bh = int(box_h)

        # BG 이벤트 (Layer 0) - 검은 박스
        bg_event = f"Dialogue: 0,{start},{end},BizCafeBG,,0,0,0,,{{\\an2\\pos({cx},{y_base})\\p1\\bord0\\shad0\\1c&H000000&}}m -{bw2} -{bh} l {bw2} -{bh} l {bw2} 0 l -{bw2} 0"
        events.append(bg_event)

        # TEXT 이벤트 (Layer 1) - 흰색 텍스트
        text_event = f"Dialogue: 1,{start},{end},BizCafeText,,0,0,0,,{{\\an2\\pos({cx},{y_base})}}{text}"
        events.append(text_event)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ass_header)
        f.write('\n'.join(events))

    print(f"ASS 파일 생성: {output_path}")
    print(f"총 {len(cues)}개 자막 cue")
    return output_path


# 메인 실행
video_path = "{video_path}"
srt_path = "{srt_path}"

# 영상 해상도 가져오기
import subprocess
result = subprocess.run(
    ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
     '-show_entries', 'stream=width,height', '-of', 'csv=p=0', video_path],
    capture_output=True, text=True
)
width, height = map(int, result.stdout.strip().split(','))

# ASS 파일 생성
ass_path = srt_path.rsplit('.', 1)[0] + '.ass'
cues = parse_srt(srt_path)
generate_ass(cues, width, height, ass_path)
```

### 3. ffmpeg Burn-in

```bash
# 출력 경로 설정
output_path="${output_path:-${video_path%.*}_burnin.mp4}"

# ASS 자막 burn-in
ffmpeg -i "{video_path}" \
    -vf "ass={ass_path}" \
    -c:a copy \
    -y \
    "{output_path}"

echo "완료: {output_path}"
```

## 출력 형식

```markdown
## 자막 Burn-in 완료

- **입력 영상**: {video_path}
- **입력 자막**: {srt_path}
- **출력 영상**: {output_path}
- **해상도**: {width}x{height}
- **자막 개수**: {count}개

### 스타일 정보
- 폰트: Noto Sans CJK KR ({font_size}px)
- 정렬: bottom-center
- 패딩: {pad_x}px x {pad_y}px
- 마진: {margin_v}px

### 파일 위치
- ASS 파일: {ass_path}
- 출력 영상: {output_path}
```

## 주의사항

1. **폰트 설치 필요**: `Noto Sans CJK KR` 폰트가 시스템에 설치되어 있어야 함
   ```bash
   # Ubuntu/WSL
   sudo apt install fonts-noto-cjk

   # macOS
   brew install font-noto-sans-cjk-kr
   ```

2. **ffmpeg libass 지원 필요**: `ffmpeg -filters | grep ass`로 확인

3. **인코딩 시간**: 10분 영상 기준 약 2-5분 소요

4. **원본 보존**: 원본 영상은 수정하지 않고 새 파일로 출력
