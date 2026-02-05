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
/finalize --srt 2-echo-delta/videos/subtitles/corrected/meetup_02_*_corrected.srt

# Interactive mode - search and confirm files
/finalize
```

## Workflow

```
+-----------------------------------------------------+
|              Step 1: Search Files                    |
|  - Glob: subtitles/corrected/*_corrected.srt        |
|  - Glob: cropped/*.mov or raw/*.mov                 |
+--------+--------------------------------------------+
         v
+-----------------------------------------------------+
|              Step 2: Confirm Selection               |
|  AskUserQuestion:                                   |
|  - SRT: {found_srt_file}                            |
|  - Video: {matched_video_file}                      |
|  - "Proceed with these files?"                      |
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
_en.srt      {video}_burnin.mp4
    +----+----+
         v
+-----------------------------------------------------+
|              Step 3: Report Results                  |
|  - English subtitle: en/...                         |
|  - Burn-in video: burnin_output/...                 |
+-----------------------------------------------------+
```

## Steps

### Step 1: Search Files

#### 1.1 Find SRT files

If `--srt` provided, use that file directly.

Otherwise, search for corrected SRT files:

```bash
ls 2-echo-delta/videos/subtitles/corrected/*_corrected.srt
```

#### 1.2 Find Video files

For each SRT, infer matching video:

```python
# From: meetup_02_건호님_corrected.srt
# Extract: meetup_02_건호님

srt_name = "meetup_02_건호님_corrected.srt"
video_stem = srt_name.replace("_corrected.srt", "")  # meetup_02_건호님

# Search order:
# 1st: cropped/{video_stem}_cropped.mov
# 2nd: raw/{video_stem}.mov
```

```bash
ls 2-echo-delta/videos/cropped/
ls 2-echo-delta/videos/raw/
```

### Step 2: Confirm Selection (AskUserQuestion)

**IMPORTANT**: Always confirm with user before proceeding.

Show found files and ask for confirmation:

```
Task: AskUserQuestion
Question: "Proceed with these files for finalize?"

Display:
  SRT file: subtitles/corrected/meetup_02_건호님_corrected.srt
  Video file: cropped/meetup_02_건호님_cropped.mov

  Output will be:
  - English subtitle: subtitles/en/meetup_02_건호님_corrected_en.srt
  - Burn-in video: burnin_output/meetup_02_건호님_cropped_burnin.mp4

Options:
  - Proceed
  - Select different SRT
  - Cancel
```

If user selects "Select different SRT":
- Show list of available SRT files from corrected/
- Let user choose
- Re-match video file
- Confirm again

### Step 3: Parallel Execution

Run both agents **simultaneously** in a single message:

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
```

**IMPORTANT**: Call both Tasks in parallel in the same message.

### Step 4: Report Results

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
- Style: drawtext single box (Noto Sans CJK KR 38px)

### Upload Checklist
- [ ] Review English subtitles
- [ ] Verify burn-in video playback
- [ ] Upload to YouTube/platform
```

## Output Paths

| Output | Path |
|--------|------|
| English subtitle | `subtitles/en/{srt_basename}_en.srt` |
| Burn-in video | `burnin_output/{video_stem}_burnin.mp4` |

## Example

```
> /finalize

Claude: Searching for files...
  Found SRT: subtitles/corrected/meetup_02_건호님_corrected.srt
  Matched video: cropped/meetup_02_건호님_cropped.mov

Claude: [AskUserQuestion]
  Proceed with these files for finalize?
  - SRT: meetup_02_건호님_corrected.srt
  - Video: meetup_02_건호님_cropped.mov

  [Proceed] [Select different SRT] [Cancel]

User: Proceed

Claude: Starting parallel execution...
  - Translator: translating 245 segments...
  - Burnin: encoding video with subtitles...

Claude: Upload Ready!
  - English subtitle: subtitles/en/meetup_02_건호님_corrected_en.srt
  - Burn-in video: burnin_output/meetup_02_건호님_cropped_burnin.mp4
```

## Notes

1. **Prerequisite**: Corrected SRT from `/video-subtitle` must exist
2. **Video matching**: Prefers cropped/ over raw/
3. **Font**: `Noto Sans CJK KR` font required for burn-in
4. **Processing time**: Burn-in depends on video length (~2-5 min for 10min video)
