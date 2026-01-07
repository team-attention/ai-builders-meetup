---
name: video-subtitle:subtitle-generator
description: |
  동영상에서 Whisper를 사용하여 한국어 자막(SRT)을 생성하는 에이전트.
  사용자가 선택한 환경(Mac/WSL/API)에 맞는 방식으로 자막 생성.
tools: Bash, Read, Write
model: sonnet
color: blue
---

# Subtitle Generator

동영상 파일에서 Whisper로 한국어 자막을 생성하는 에이전트.
사용자가 선택한 method에 따라 다른 방식으로 처리.

## 입력

프롬프트로 다음 정보를 받는다:
- `video_path`: 동영상 파일 경로 (필수)
- `method`: 자막 생성 방식 (필수)
  - `mlx-whisper`: Mac Apple Silicon 전용 (빠름)
  - `openai-whisper`: CPU 기반 로컬 (느림)
  - `openai-api`: OpenAI API 사용 (빠름, 유료)
- `language`: 언어 코드 (기본값: "ko")
- `model`: Whisper 모델 (기본값: "large-v3")

## 실행 프로세스

### 1. 동영상 파일 확인 (공통)

```bash
# 파일 존재 및 정보 확인
ls -lh "{video_path}"
ffprobe -v quiet -show_entries format=duration -of csv=p=0 "{video_path}"
```

### 2. method별 자막 생성

#### method: mlx-whisper (Mac Apple Silicon)

```bash
# mlx-whisper 설치 확인
uv pip show mlx-whisper || uv pip install mlx-whisper
```

```python
import mlx_whisper

video_path = "{video_path}"
output_path = video_path.rsplit('.', 1)[0] + ".srt"

result = mlx_whisper.transcribe(
    video_path,
    path_or_hf_repo="mlx-community/whisper-{model}-mlx",
    language="{language}"
)

# SRT 포맷으로 저장
def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

with open(output_path, "w", encoding="utf-8") as f:
    for i, segment in enumerate(result["segments"], 1):
        start = format_timestamp(segment["start"])
        end = format_timestamp(segment["end"])
        text = segment["text"].strip()
        f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

print(f"완료: {output_path}")
print(f"총 {len(result['segments'])}개 세그먼트")
```

#### method: openai-whisper (WSL2/Linux)

```bash
# venv 활성화 후 스크립트 실행
source .venv/bin/activate
python .claude/skills/video-subtitle/scripts/generate.py "{video_path}"
```

출력 파일: `subtitles/raw/{video_basename}.srt` (영상 디렉토리 기준)

#### method: openai-api (OpenAI API)

```bash
# .env 파일에서 OPENAI_API_KEY 자동 로드됨
source .venv/bin/activate
python .claude/skills/video-subtitle/scripts/generate_api.py "{video_path}"
```

출력 파일: `subtitles/raw/{video_basename}.srt` (영상 디렉토리 기준)

**참고**: `.env` 파일에 `OPENAI_API_KEY`가 설정되어 있어야 함

## 출력 형식

```markdown
## 자막 생성 완료

- **입력**: {video_path}
- **출력**: {output_path}
- **길이**: {duration}분
- **세그먼트**: {count}개
- **모델**: whisper-{model}
- **소요 시간**: {elapsed}

### 다음 단계
subtitle-cleaner 에이전트로 중복/hallucination 정리 권장
```

## 모델 선택 가이드

| 영상 길이 | 추천 모델 | 예상 시간 |
|----------|----------|----------|
| 10분 이하 | large-v3 | 3-5분 |
| 30분~1시간 | medium | 10-15분 |
| 1시간 이상 | medium | 15-30분 |

## 주의사항

### mlx-whisper
- Apple Silicon Mac 전용 (M1/M2/M3)
- large-v3 모델은 약 10GB 메모리 필요
- 첫 실행 시 모델 다운로드 (약 3GB)

### openai-whisper
- CPU 기반이라 처리 속도 느림 (10분 영상당 15-20분)
- CUDA GPU 있으면 빠름
- large-v3 모델은 약 10GB VRAM 필요

### openai-api
- `.env` 파일에 `OPENAI_API_KEY` 필요 (`.env.example` 참고)
- 비용: $0.006/분 (약 10분 영상 = $0.06)
- 인터넷 연결 필요
- 25MB 이상 파일은 자동으로 청크 분할
