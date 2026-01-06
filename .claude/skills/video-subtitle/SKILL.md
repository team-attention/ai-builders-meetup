---
name: video-subtitle
description: |
  동영상에서 자막을 자동 생성하고 발표자료 기반으로 교정하는 스킬.
  "자막 생성", "영상 자막", "STT", "subtitle" 요청에 사용.
  mlx-whisper로 추출 → 중복 정리 → 발표자료 기반 교정까지 자동화.
  기존 SRT 파일이 있으면 생성 단계를 스킵하고 정리/교정부터 시작 가능.
arguments:
  - name: video
    description: 동영상 파일 경로 (srt가 없을 때 필수)
    required: false
  - name: srt
    description: 기존 자막 파일 경로 (있으면 생성 단계 스킵)
    required: false
  - name: reference
    description: 발표자료(PDF) 경로 (선택, 교정 시 필요)
    required: false
---

# Video Subtitle Generator

동영상에서 자막을 생성하고 발표자료 기반으로 교정하는 스킬.
기존 SRT 파일이 있으면 정리/교정 단계부터 시작할 수 있음.

## 사용법

```bash
# 영상에서 자막 생성
/video-subtitle --video /path/to/video.mp4

# 영상에서 자막 생성 + 발표자료 기반 교정
/video-subtitle --video /path/to/video.mp4 --reference /path/to/slides.pdf

# 기존 자막 파일 정리/교정 (생성 단계 스킵)
/video-subtitle --srt /path/to/existing.srt

# 기존 자막 + 발표자료 기반 교정
/video-subtitle --srt /path/to/existing.srt --reference /path/to/slides.pdf
```

## 워크플로우

```
┌─────────────────────────────────────────────────────┐
│                    입력 확인                         │
│  video만 → 전체 워크플로우                           │
│  srt만   → Step 2부터 시작                          │
│  둘 다 없음 → 사용자에게 질문                        │
└────────┬────────────────────────────────────────────┘
         ▼
┌─────────────────┐
│ subtitle-       │  mlx-whisper (large-v3)
│ generator       │  → SRT 파일 생성
└────────┬────────┘  [video 있을 때만]
         ▼
┌─────────────────┐
│ subtitle-       │  중복/hallucination 제거
│ cleaner         │  → 정리된 SRT
└────────┬────────┘
         ▼
┌─────────────────┐
│ subtitle-       │  발표자료 기반 STT 오류 교정
│ corrector       │  → 최종 SRT
└────────┬────────┘  [reference 있을 때만]
         ▼
┌─────────────────┐
│  최종 자막      │
└─────────────────┘
```

## 실행 단계

### Step 1: 자막 생성 (subtitle-generator)

```
Task: video-subtitle:subtitle-generator
Prompt: |
  다음 동영상에서 한국어 자막을 생성해주세요.
  - video_path: $video
  - language: ko
  - model: large-v3
```

출력: `{video_basename}.srt`

### Step 2: 중복 정리 (subtitle-cleaner)

```
Task: video-subtitle:subtitle-cleaner
Prompt: |
  다음 자막 파일에서 중복과 hallucination을 정리해주세요.
  - srt_path: {output_from_step1}
```

### Step 3: STT 교정 (subtitle-corrector) - reference가 있을 때만

```
Task: video-subtitle:subtitle-corrector
Prompt: |
  발표자료를 참조하여 STT 오류를 찾고 수정해주세요.
  - srt_path: {output_from_step2}
  - reference_path: $reference
```

## 예시

### 입력
```
/video-subtitle --video community/ai-builders-meetup/2-echo-delta/videos/meetup_02_서진님.mp4 --reference community/ai-builders-meetup/2-echo-delta/slides/1-김서진-AI-Native.pdf
```

### 출력
```
## 자막 생성 완료

### 1. 자막 추출
- 입력: meetup_02_서진님.mp4 (9.8분)
- 출력: meetup_02_서진님.srt
- 세그먼트: 116개
- 소요: 4분 30초

### 2. 중복 정리
- 원본: 116개 → 정리 후: 81개
- 제거: 35개 (30%)

### 3. STT 교정
- 발견된 오류: 23개
- 수정 완료: 23개

### 최종 파일
community/ai-builders-meetup/2-echo-delta/videos/meetup_02_서진님.srt
```

## 시스템 요구사항

- Apple Silicon Mac (M1/M2/M3)
- Python 3.10+
- 메모리: 16GB+ (large-v3 모델용)
- 저장공간: 3GB+ (모델 다운로드)

## 지원 형식

- 입력: mp4, mov, mkv, webm, avi
- 출력: srt
- 발표자료: pdf
