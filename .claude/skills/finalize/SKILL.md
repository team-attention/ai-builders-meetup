---
name: finalize
description: |
  Finalize upload assets from corrected subtitles.
  Runs English translation + subtitle burn-in in parallel.
  Invoke with /finalize or "prepare for upload", "translate and burnin".
arguments:
  - name: srt
    description: Corrected SRT file path (if not specified, select from corrected/ list)
    required: false
---

# Finalize - Prepare Upload Assets

Generate upload assets (English subtitles + burn-in video) from corrected Korean subtitles.

## Usage

```bash
# Specify SRT file directly
/finalize --srt 2-echo-delta/videos/subtitles/corrected/meetup_02_*.srt

# If SRT not specified, select from corrected/ list
/finalize
```

## Workflow

```
+-----------------------------------------------------+
|                    Input Check                       |
|  --srt provided -> use that file                    |
|  --srt missing  -> show corrected/ list and ask     |
+--------+--------------------------------------------+
         v
+-----------------------------------------------------+
|                  Infer Video File                    |
|  corrected/meetup_02_*_corrected.srt                |
|      -> 1st: cropped/meetup_02_*_cropped.mov        |
|      -> 2nd: raw/meetup_02_*.mov                    |
|  (if no match, ask user)                            |
+--------+--------------------------------------------+
         v
+-----------------------------------------------------+
|               Confirm Before Running                 |
|  - SRT: {srt_path}                                  |
|  - Video: {video_path}                              |
|  - Proceed?                                         |
+--------+--------------------------------------------+
         v
    +----+----+
    v         v
+--------+ +--------+
|subtitle| |subtitle|  (parallel)
|-trans- | |-burnin |
|lator   | |        |
+---+----+ +---+----+
    v         v
en/{name}    burnin_output/
_en.srt      {video_name}_burnin.mp4
    +----+----+
         v
+-----------------------------------------------------+
|                    Report Results                    |
|  - English subtitle: en/...                         |
|  - Burn-in video: burnin_output/...                 |
|  -> Ready for upload!                               |
+-----------------------------------------------------+
```

## Steps

### Step 1: Input Check and SRT Selection

If `--srt` not provided, ask user to select:

```
Task: AskUserQuestion
Question: Which subtitle file to use?
Options:
  - meetup_02_*_corrected.srt (list from corrected/)
```

Get `*_corrected.srt` file list from corrected/ directory.

### Step 2: Infer Video File

Infer video path from SRT filename (prefer cropped, fallback to raw):

```python
srt_name = "meetup_02_*_corrected.srt"
base_name = srt_name.replace("_corrected", "")  # meetup_02_*.srt
video_stem = base_name.replace(".srt", "")      # meetup_02_*

# 1st: cropped video
cropped_path = f"cropped/{video_stem}_cropped.mov"
# 2nd: raw video
raw_path = f"raw/{video_stem}.mov"

if exists(cropped_path):
    video_path = cropped_path
elif exists(raw_path):
    video_path = raw_path
else:
    # No match -> ask user
```

If no match:
```
Task: AskUserQuestion
Question: Video file not found. Please enter path.
```

### Step 3: Confirm Before Running

Ask user to confirm:

```
Task: AskUserQuestion
Question: Proceed with these settings?
Content:
  - SRT: subtitles/corrected/meetup_02_*_corrected.srt
  - Video: cropped/meetup_02_*_cropped.mov (or raw/...)
  - Output:
    - English subtitle: subtitles/en/meetup_02_*_corrected_en.srt
    - Burn-in video: burnin_output/meetup_02_*_cropped_burnin.mp4
Options:
  - Proceed
  - Cancel
```

### Step 4: Parallel Execution

Run both agents **simultaneously**:

```
Task A: video-subtitle:subtitle-translator
Prompt: |
  Translate the following Korean subtitle to English.
  - srt_path: {srt_path}

Task B: video-subtitle:subtitle-burnin
Prompt: |
  Burn subtitles into video.
  - video_path: {video_path}
  - srt_path: {srt_path}
  - output_path: burnin_output/{video_name}_burnin.mp4
```

**IMPORTANT**: Call both Tasks in parallel in the same message.

### Step 5: Report Results

After both complete, summarize:

```markdown
## Upload Ready!

### Generated Files
| Type | Path |
|------|------|
| English subtitle | subtitles/en/meetup_02_*_corrected_en.srt |
| Burn-in video | burnin_output/meetup_02_*_cropped_burnin.mp4 |

### Translator Result
- Translated segments: {count}
- Preserved terms: RAG, MCP, LangChain, etc.

### Burnin Result
- Resolution: {width}x{height}
- Subtitle count: {count}
- Style: drawtext single box (Noto Sans CJK KR)

### Upload Checklist
- [ ] Review English subtitles
- [ ] Verify burn-in video playback
- [ ] Upload to YouTube/platform
```

## Output Paths

- `{basename}`: SRT filename without extension (e.g., `meetup_02_*_corrected`)
- `{video_name}`: Video filename without extension (e.g., `meetup_02_*_cropped`)

| Output | Path |
|--------|------|
| English subtitle | `subtitles/en/{basename}_en.srt` |
| Burn-in video | `burnin_output/{video_name}_burnin.mp4` |

## Example

### Example 1: Specify SRT directly
```
/finalize --srt 2-echo-delta/videos/subtitles/corrected/meetup_02_*_corrected.srt
```

### Example 2: Interactive selection
```
> /finalize
Claude: Which subtitle file to use?
  1. meetup_02_*_corrected.srt
  2. ...
User: 1
Claude: Proceed with these settings?
  - SRT: .../meetup_02_*_corrected.srt
  - Video: cropped/meetup_02_*_cropped.mov
User: Proceed
(translator + burnin run in parallel)
Claude: Upload Ready!
```

## Notes

1. **Prerequisite**: Corrected SRT from `/video-subtitle` must exist
2. **Video file**: Must exist in cropped/ or raw/ for burn-in (prefers cropped)
3. **Font**: `Noto Sans CJK KR` font required for burn-in
4. **Processing time**: Burn-in time depends on video length
