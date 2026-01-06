# Execute Subtitle Generation for 건호님

Complete subtitle generation pipeline is ready. Follow these instructions to generate Korean subtitles.

## Files Created

All scripts and documentation have been created:

- `/home/junchan/github/ai-builders-meetup/transcribe_건호님.py` - Step 1: Transcription
- `/home/junchan/github/ai-builders-meetup/subtitle_cleaner.py` - Step 2: Cleaning
- `/home/junchan/github/ai-builders-meetup/subtitle_corrector.py` - Step 3: Correction (updated with 건호님's specific terms)
- `/home/junchan/github/ai-builders-meetup/generate_subtitle_full.py` - All-in-one script
- `/home/junchan/github/ai-builders-meetup/run_subtitle_generation.sh` - Bash runner
- `/home/junchan/github/ai-builders-meetup/SUBTITLE_GENERATION_GUIDE.md` - Complete manual
- `/home/junchan/github/ai-builders-meetup/SUBTITLE_PIPELINE_SUMMARY.md` - Quick reference

## Quick Start (Recommended)

```bash
cd /home/junchan/github/ai-builders-meetup

# Activate virtual environment
source .venv/bin/activate

# Install whisper if needed
pip install openai-whisper

# Run complete pipeline (all 3 steps)
python generate_subtitle_full.py
```

## Input/Output

### Input Files
- **Video**: `/home/junchan/github/ai-builders-meetup/2-echo-delta/videos/meetup_02_건호님.mov` (160MB)
- **Reference PDF**: `/home/junchan/github/ai-builders-meetup/2-echo-delta/slides/4-신건호-AI Builder Meetup_DAY1 B2B 신건호_251229_VF(배포용).pdf` (3MB)

### Output File
- **Subtitle**: `/home/junchan/github/ai-builders-meetup/2-echo-delta/videos/meetup_02_건호님.srt`

## What Each Step Does

### Step 1: Transcription (5-10 minutes)
- Uses Whisper large-v3 model
- Generates ~150-200 Korean subtitle segments
- Creates timestamped SRT file
- May contain duplicates and hallucinations

### Step 2: Cleaning (<1 second)
- Removes duplicate segments
- Filters out hallucinations: [음악], [박수], "감사합니다" etc.
- Removes empty segments
- Expected to remove ~10-30% of segments

### Step 3: Terminology Correction (<1 second)
- Applies 50+ term corrections specific to 건호님's presentation:
  - **AX terms**: AX, AI Transformation, E2E, Full-Stack, AI-Native
  - **Business terms**: MVP, PMF, PoC, ROI, B2B
  - **Companies**: DAY1COMPANY, doeat, KEARNEY, KAIST
  - **Tools**: CODEX, FastForward, n8n, NotebookLM
  - **People**: 벤 호로위츠, 일론 머스크
  - **Tech**: LLM, RAG, Agent, Workflow, Prompt, MECE

## Alternative: Step-by-Step Execution

If you prefer to run each step separately for better control:

```bash
cd /home/junchan/github/ai-builders-meetup
source .venv/bin/activate

# Step 1: Transcribe (takes 5-10 minutes)
python transcribe_건호님.py

# Step 2: Clean
python subtitle_cleaner.py 2-echo-delta/videos/meetup_02_건호님.srt

# Step 3: Correct terminology
python subtitle_corrector.py \
  2-echo-delta/videos/meetup_02_건호님.srt \
  "2-echo-delta/slides/4-신건호-AI Builder Meetup_DAY1 B2B 신건호_251229_VF(배포용).pdf"
```

## Using the Bash Script

```bash
cd /home/junchan/github/ai-builders-meetup
chmod +x run_subtitle_generation.sh
./run_subtitle_generation.sh
```

## Expected Output

```
======================================================================
KOREAN SUBTITLE GENERATION PIPELINE
======================================================================

Video: .../meetup_02_건호님.mov
Output: .../meetup_02_건호님.srt
Reference: .../4-신건호-AI Builder Meetup_DAY1 B2B 신건호_251229_VF(배포용).pdf

======================================================================
STEP 1: TRANSCRIPTION
======================================================================
Video: .../meetup_02_건호님.mov
Model: large-v3
Language: ko
Using: openai-whisper

Loading model...
Transcribing... (this may take several minutes)
Writing SRT file...

Transcription complete!
Segments: 178
Time: 384.2s (6.4 min)

======================================================================
STEP 2: CLEANING
======================================================================
Original segments: 178
Cleaned segments: 156
Removed: 22 (12%)

======================================================================
STEP 3: TERMINOLOGY CORRECTION (건호님's AX Presentation)
======================================================================
SRT file: .../meetup_02_건호님.srt
Reference PDF: 4-신건호-AI Builder Meetup_DAY1 B2B 신건호_251229_VF(배포용).pdf

Reference PDF found: 4-신건호-AI Builder Meetup_DAY1 B2B 신건호_251229_VF(배포용).pdf
Using 50 terminology corrections from 건호님's presentation
Loaded 156 segments

Corrections applied: 34 segments modified
Output written to: .../meetup_02_건호님.srt

======================================================================
PIPELINE COMPLETE
======================================================================
Output file: .../meetup_02_건호님.srt
Initial segments: 178
After cleaning: 156
Corrections: 34
Total time: 7.2 minutes

Please review the subtitle file and make manual corrections as needed.
======================================================================
```

## Verification

After generation, verify the result:

```bash
# Check the output file exists
ls -lh 2-echo-delta/videos/meetup_02_건호님.srt

# Count segments
grep -c "^[0-9]*$" 2-echo-delta/videos/meetup_02_건호님.srt

# View first 10 segments
head -40 2-echo-delta/videos/meetup_02_건호님.srt

# Check for any remaining hallucinations
grep -i "음악\|박수\|구독\|좋아요" 2-echo-delta/videos/meetup_02_건호님.srt
```

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'whisper'"

```bash
source .venv/bin/activate
pip install openai-whisper
```

### Transcription is too slow

Edit `transcribe_건호님.py` or `generate_subtitle_full.py` and change:
- `model_name = "large-v3"` → `model_name = "medium"` (faster, still good)
- Or `model_name = "small"` (fastest, acceptable quality)

### Out of memory

- Use smaller model (medium or small)
- Close other applications
- Ensure at least 8GB free RAM

## Manual Review Checklist

After automated generation, manually review for:

1. **Speaker name**: Ensure "신건호님" is correctly transcribed
2. **Company names**: DAY1COMPANY, doeat, KEARNEY, KAIST
3. **Key concepts**: AX, AI Transformation, PMF, MVP, E2E, Full-Stack
4. **People mentioned**: 벤 호로위츠, 일론 머스크
5. **Technical terms**: Verify all AX/AI/B2B terminology
6. **Timing**: Check subtitle sync with video
7. **Readability**: Break long segments if needed

## Key Terminology from 건호님's Presentation

The corrector script includes these specific terms:

| Korean | English | Context |
|--------|---------|---------|
| AX | AI Transformation | Core topic |
| 고도로 발달한 AX는 창업과 구분할 수 없다 | - | Key thesis |
| Thin but E2E | End-to-End | Rule 1 |
| AI-Native | - | Rule 2 |
| Full-Stack | - | Rule 3 |
| DAY1COMPANY | - | Current company |
| doeat | - | Previous company |
| CODEX | - | Internal tool |
| FastForward | - | AX build service |
| n8n | - | Workflow tool |

## Next Steps

1. Run the pipeline to generate subtitles
2. Review the output SRT file
3. Make manual corrections as needed
4. Test with video player to verify sync
5. Consider repeating for other speaker videos

## Notes

- This is a WSL2 Linux environment, so using `openai-whisper` instead of `mlx-whisper`
- First run will download the Whisper model (~3GB)
- Subsequent runs will be faster (model cached)
- Total pipeline time: ~8-15 minutes depending on hardware
- GPU acceleration automatic if CUDA available

## Questions?

Refer to:
- `SUBTITLE_GENERATION_GUIDE.md` - Complete manual with troubleshooting
- `SUBTITLE_PIPELINE_SUMMARY.md` - Technical details and architecture
