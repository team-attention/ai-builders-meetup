# BizCafe 자막 하드인코딩 가이드 (SRT→ASS 방식)

목표: 입력 영상이 1920×1080이 아니거나 크롭되어 있어도, **화면 하단 중앙 기준(bottom-center)**으로 BizCafe 스타일 자막을 하드인코딩한다. **멀티라인 자막도 단일 검은 박스**로 감싼다.

## 핵심 변경사항
- ~~`BorderStyle=3` (opaque box)~~ **사용 금지** → 줄마다 박스가 분리되는 원인
- **SRT → ASS 변환** 후 burn-in
- 각 자막 cue마다 **이벤트 2개** 생성:
  1. **BG 이벤트(Layer 0)**: 벡터 드로잉(`\p1`)으로 검은 직사각형 1개
  2. **TEXT 이벤트(Layer 1)**: 흰색 텍스트 (박스 없음)

## 렌더링 규칙

### 기본 설정
- 렌더러: ffmpeg + libass (subtitles 필터)
- 입력: video + SRT → ASS 변환
- 출력: burn-in mp4 (오디오는 copy)
- 폰트: Noto Sans CJK KR (Regular, Bold 아님)
- FontSize: **18** (1440x810 기준)

### 정렬/위치
- **Alignment=2 (bottom-center)**
- MarginV: **40** (하단에서 위로 올리는 거리)

### 스타일
- 텍스트 색: 흰색 (#FFFFFF)
- 박스 색: 검정 (#000000), 불투명
- Shadow: 0
- 줄바꿈: `\N`으로 처리 (최대 2줄)

## cue별 박스 크기 계산

cue 텍스트 전체(멀티라인 포함)의 bbox를 폰트로 측정:
- `box_w = text_w + 2 * pad_x`
- `box_h = text_h + 2 * pad_y`

BG 드로잉은 bottom-center 기준:
```
m -box_w/2 -box_h l box_w/2 -box_h l box_w/2 0 l -box_w/2 0
```

## ASS 스타일 정의

```ass
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: BizCafeBG,Noto Sans CJK KR,18,&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,0,0,40,1
Style: BizCafeText,Noto Sans CJK KR,18,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,0,0,40,1
```

## ASS 이벤트 템플릿

### BG (Layer 0)
```ass
Dialogue: 0,<START>,<END>,BizCafeBG,,0,0,0,,{\an2\pos(<cx>,<y_box_bottom>)\p1\bord0\shad0\1c&H000000&}m -<bw2> -<bh> l <bw2> -<bh> l <bw2> 0 l -<bw2> 0
```

### TEXT (Layer 1)
```ass
Dialogue: 1,<START>,<END>,BizCafeText,,0,0,0,,{\an2\pos(<cx>,<y_text_bottom>)}<LINE1>\N<LINE2>
```

## burn-in 커맨드

```bash
ffmpeg -i "INPUT.mp4" -vf "ass=OUTPUT.ass" -c:a copy "OUTPUT_burnin.mp4"
```

## 파라미터 (1440x810 기준)
| 항목 | 값 |
|------|-----|
| FontSize | 18 |
| FontWeight | Regular (Bold 아님) |
| pad_x | 10px |
| pad_y | 6px |
| MarginV | 40px |
| 영상 중앙 X | 720 |
