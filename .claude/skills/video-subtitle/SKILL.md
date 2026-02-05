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
│  video만 → 환경 선택 → 자막 생성                     │
│  srt만   → Step 2부터 시작                          │
│  둘 다 없음 → 사용자에게 질문                        │
└────────┬────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────┐
│              환경 선택 (video 있을 때)               │
│  Mac (mlx-whisper) / WSL (openai-whisper) / API     │
└────────┬────────────────────────────────────────────┘
         ▼
┌─────────────────┐
│ subtitle-       │  선택한 환경으로 자막 생성
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
│ corrector       │  → _corrected.srt
└────────┬────────┘  [reference 있을 때만]
         ▼
┌─────────────────┐
│ subtitle-       │  발표자료 기반 품질 검증
│ validator       │  → 추가 수정 제안 (파일 수정 없음)
└────────┬────────┘  [reference 있을 때만]
         ▼
┌─────────────────┐
│ subtitle-       │  validator 결과 반영 (2차 교정)
│ corrector (2차) │  → _corrected.srt 갱신
└────────┬────────┘  [reference 있을 때 항상]
         ▼
┌─────────────────┐
│ subtitle-       │  Claude + Codex 이중 검증
│ qa              │  → 최종 품질 보고서
└────────┬────────┘  [항상 실행]
         ▼
┌─────────────────┐
│ subtitle-       │  QA 결과 반영 (3차 교정)
│ corrector (3차) │  → _corrected.srt 갱신
└────────┬────────┘  [항상 실행]
         ▼
┌─────────────────┐
│ 통합 보고서     │  각 단계 결과 수집
│ 생성            │  → _report.md
└────────┬────────┘
         ▼
┌─────────────────┐
│  최종 자막      │  사람이 검토 후
│                 │  /finalize로 업로드 준비
└─────────────────┘
```

## 필수 실행 규칙

**중요**: 이 스킬은 반드시 모든 해당 단계를 순차적으로 완료해야 합니다. **중간에 멈추지 말 것.**

| 조건 | 필수 실행 단계 |
|------|---------------|
| video O, reference O | 0.5 → 1 → 2 → 3 → 4 → 4.1 → 4.5 → 4.6 → 5 (전체) |
| video O, reference X | 0.5 → 1 → 2 → 4.5 → 4.6 → 5 |
| srt O, reference O | 2 → 3 → 4 → 4.1 → 4.5 → 4.6 → 5 |
| srt O, reference X | 2 → 4.5 → 4.6 → 5 |

**각 단계 완료 시 결과를 표시하고, 허락 없이 바로 다음 단계 진행.**

**각 단계가 완료되면 즉시 다음 단계를 실행할 것. 사용자에게 "완료되었습니다" 같은 중간 보고 없이 다음 단계로 바로 진행.**

### 실행 완료 체크리스트

스킬 종료 전 반드시 확인:
- [ ] Step 2 (cleaner) 완료
- [ ] Step 3 (corrector 1차) 완료 - reference 있을 때
- [ ] Step 4 (validator) 완료 - reference 있을 때
- [ ] Step 4.1 (corrector 2차) 완료 - reference 있을 때
- [ ] Step 4.5 (qa) 완료 - **항상 실행**
- [ ] Step 4.6 (corrector 3차) 완료 - **항상 실행**
- [ ] Step 5 (보고서) 완료

## 실행 단계

### Step 0: 입력 확인 및 사용자 질문

입력에 따라 시작 단계 결정:

| 입력 | 시작 단계 |
|------|----------|
| `--video` 있음 | Step 0.5 (환경 선택) → Step 1 (자막 생성) |
| `--srt` 있음 | Step 2 (중복 정리)부터 |
| 둘 다 없음 | 사용자에게 질문 |

**둘 다 없을 때 질문 예시:**
- "영상 파일에서 새로 자막을 생성할까요, 아니면 기존 SRT 파일을 정리/교정할까요?"
- 사용자 선택에 따라 파일 경로 확인 후 진행

### Step 0.5: 환경 선택 (video 있을 때만)

video 입력이 있으면 사용자에게 **자막 생성 환경을 질문**:

| 옵션 | 환경 | 특징 |
|------|------|------|
| **Mac (mlx-whisper)** | Apple Silicon M1/M2/M3 | 빠름, 무료, Apple Silicon 전용 |
| **WSL2/Linux (openai-whisper)** | CPU 기반 | 느림, 무료, 범용 |
| **OpenAI API** | 클라우드 | 빠름, 유료 ($0.006/분), .env에 API 키 필요 |

**질문 예시:**
```
자막 생성에 사용할 환경을 선택해주세요:
1. Mac (mlx-whisper) - Apple Silicon 전용, 빠름
2. WSL2/Linux (openai-whisper) - CPU 기반, 느림
3. OpenAI API - 클라우드, 빠름, 유료
```

선택된 method를 Step 1로 전달.

### Step 1: 자막 생성 (subtitle-generator) - video 있을 때만

```
Task: video-subtitle:subtitle-generator
Prompt: |
  다음 동영상에서 한국어 자막을 생성해주세요.
  - video_path: $video
  - language: ko
  - model: large-v3
  - method: $method (mlx-whisper | openai-whisper | openai-api)
```

출력: `{video_basename}.srt`

### Step 2: 중복 정리 (subtitle-cleaner)

```
Task: video-subtitle:subtitle-cleaner
Prompt: |
  다음 자막 파일에서 중복과 hallucination을 정리해주세요.
  - srt_path: {$srt 또는 output_from_step1}
```

**완료 후**: reference가 있으면 즉시 Step 3 (subtitle-corrector) 실행. 없으면 Step 4.5로 건너뜀.

### Step 3: STT 교정 (subtitle-corrector) - reference가 있을 때만

```
Task: video-subtitle:subtitle-corrector
Prompt: |
  발표자료를 참조하여 STT 오류를 찾고 수정해주세요.
  - srt_path: {output_from_step2}
  - reference_path: $reference
```

출력: `{basename}_corrected.srt`

**완료 후**: 즉시 Step 4 (subtitle-validator) 실행. reference가 없으면 Step 4.5로 건너뜀.

### Step 4: 품질 검증 (subtitle-validator) - reference가 있을 때만

```
Task: video-subtitle:subtitle-validator
Prompt: |
  다음 자막 파일을 발표자료와 비교하여 검증해주세요.
  - srt_path: {output_from_step3}
  - reference_path: $reference
```

출력: 구조화된 검증 결과 (통합 보고서에 포함)

**완료 후**: 즉시 Step 4.1 (corrector 2차) 실행.

### Step 4.1: 2차 교정 (subtitle-corrector) - reference 있을 때 항상

validator 실행 후 결과를 corrector에 전달하여 2차 교정 수행:

```
Task: video-subtitle:subtitle-corrector
Prompt: |
  validator가 제안한 수정 사항을 반영해주세요.
  - srt_path: {output_from_step3}
  - reference_path: $reference
  - validator_suggestions: {validator_output}
```

출력: `{basename}_corrected.srt` (갱신)

**완료 후**: 즉시 Step 4.5 (subtitle-qa) 실행.

### Step 4.5: 최종 품질 검증 (subtitle-qa) - 항상 실행

```
Task: video-subtitle:subtitle-qa
Prompt: |
  다음 자막 파일의 최종 품질을 검증해주세요.
  - srt_path: {이전 단계 출력 파일}
```

출력: 구조화된 QA 결과 (통합 보고서에 포함)

**검증 항목:**
1. 문맥 이상 - 앞뒤와 맞지 않는 내용
2. 짧은 자막 - 0.5초 미만 부자연스러운 자막
3. 언어 품질 - 단어, 표기, 문장 호응 오류

**검증 방식:**
- Claude 1차 검증 → Codex CLI 2차 검증 → 결과 통합

**완료 후**: 즉시 Step 4.6 (corrector 3차) 실행.

### Step 4.6: 3차 교정 (subtitle-corrector) - 항상 실행

QA 검증 결과를 반영하여 최종 교정 수행:

```
Task: video-subtitle:subtitle-corrector
Prompt: |
  QA 검증에서 발견된 이슈를 반영해주세요.
  - srt_path: {output_from_step4.1 또는 step2}
  - qa_suggestions: {qa_output}
```

출력: `{basename}_corrected.srt` (최종 갱신)

**완료 후**: 즉시 Step 5 (통합 보고서 생성) 실행.

### Step 5: 통합 보고서 생성

각 단계의 결과를 수집하여 하나의 보고서로 통합:

```
Write: {basename}_report.md
```

보고서 구조:
```markdown
# 자막 처리 보고서

## 파일 정보
- 원본: {input_file}
- 최종: {output_file}
- 발표자료: {reference_file}
- 처리일시: {timestamp}

## 요약
| 단계 | 변경 |
|------|------|
| 중복 정리 | 116개 → 81개 (-35) |
| STT 교정 | 23개 수정 |
| 품질 검증 | 3개 제안 |
| QA 검증 | 5개 이슈, 품질 8/10 |

## 1. 중복 정리 (Cleaner)
{cleaner_result}

## 2. STT 교정 (Corrector)
{corrector_result}

## 3. 품질 검증 (Validator)
{validator_result}

## 4. QA 검증 (QA)
{qa_result}
```

출력: `{basename}_report.md`

## 예시

### 예시 1: 영상에서 자막 생성
```
/video-subtitle --video 2-echo-delta/videos/raw/meetup_02_서진님.mov --reference 2-echo-delta/slides/1-김서진-AI-Native.pdf
```

### 예시 2: 기존 SRT 파일 교정
```
/video-subtitle --srt 2-echo-delta/videos/subtitles/raw/meetup_02_서진님.srt --reference 2-echo-delta/slides/1-김서진-AI-Native.pdf
```

### 출력
```
## 자막 처리 완료

### 1. 자막 추출 (video가 있을 때만)
- 입력: meetup_02_서진님.mp4 (9.8분)
- 출력: meetup_02_서진님.srt
- 세그먼트: 116개

### 2. 중복 정리
- 원본: 116개 → 정리 후: 81개
- 제거: 35개 (30%)

### 3. STT 교정 (reference가 있을 때만)
- 발견된 오류: 23개
- 수정 완료: 23개

### 4. 품질 검증 (reference가 있을 때만)
- 추가 제안: 3개 (High: 0, Medium: 2, Low: 1)

### 4.5. QA 검증 (항상 실행)
- Claude 발견: 3개, Codex 발견: 2개
- 문맥 이상: 1개, 짧은 자막: 2개, 언어 품질: 2개
- 품질 점수: 8/10

### 4.6. 3차 교정 (항상 실행)
- QA 이슈 반영: 5개 수정

### 5. 통합 보고서 생성
- 보고서: meetup_02_서진님_report.md

### 최종 파일
- 자막: 2-echo-delta/videos/subtitles/corrected/meetup_02_서진님_corrected.srt
- 보고서: 2-echo-delta/videos/subtitles/meetup_02_서진님_report.md

### 다음 단계
QA 검증 완료 후 사람이 자막을 검토하고, `/finalize` 스킬로 업로드 준비:
- 영어 번역 (subtitle-translator)
- 자막 번인 영상 (subtitle-burnin)
```

## 시스템 요구사항

### 환경별 요구사항

| 환경 | 요구사항 |
|------|----------|
| **Mac (mlx-whisper)** | Apple Silicon M1/M2/M3, 메모리 16GB+, 저장공간 3GB+ |
| **WSL2/Linux (openai-whisper)** | Python 3.10+, 저장공간 3GB+, (CUDA GPU 권장) |
| **OpenAI API** | `.env` 파일에 `OPENAI_API_KEY` 설정, 인터넷 연결 |

### 공통 요구사항
- Python 3.10+
- ffmpeg (오디오 추출용)

## 지원 형식

- 영상 입력: mp4, mov, mkv, webm, avi
- 자막 입력: srt (기존 자막 파일)
- 출력: srt
- 발표자료: pdf
