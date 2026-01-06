# Subtitle Burn-in Style Guide (drawtext)

Burn Korean subtitles into video using ffmpeg drawtext filter with single unified box.

## Style Specifications

| Property | Value (at 1080p) | Notes |
|----------|------------------|-------|
| Font | Noto Sans CJK KR | Regular weight |
| Font size | 38px | Scales with resolution |
| Text color | white (#FFFFFF) | |
| Box color | black (#000000) | Opaque |
| Box padding | 14px | Around text |
| Bottom margin | 160px | From bottom edge |
| Alignment | bottom-center | |
| Max lines | 2 | Longer text truncated |

## Implementation

### Script

```bash
python scripts/subtitle/burnin.py <video_path> <srt_path> [output_path]
```

### How it works

1. Parse SRT file into cues (start, end, text)
2. Wrap long text to max 2 lines (~40 chars/line)
3. Build ffmpeg drawtext filter chain
4. Render with single box per cue

### Scaling

All sizes scale proportionally with video height:

```python
base_height = 1080
scale = actual_height / base_height

font_size = int(38 * scale)
box_padding = int(14 * scale)
margin_bottom = int(160 * scale)
```

## ffmpeg Filter

```
drawtext=text='subtitle text':
  fontfile='/path/to/NotoSansCJK-Regular.ttc':
  fontsize=38:
  fontcolor=white:
  box=1:
  boxcolor=black:
  boxborderw=14:
  x=(w-text_w)/2:
  y=h-text_h-160:
  enable='between(t,start,end)'
```

## Multi-line Handling

- Long text auto-wrapped at ~40 characters
- `\n` in drawtext creates new line
- **Single box wraps all lines** (unlike ASS BorderStyle=3)

## Requirements

- ffmpeg with drawtext filter
- Noto Sans CJK KR font installed
- Input: SRT format subtitles
- Output: MP4 with burned subtitles
