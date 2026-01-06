# AI Builders Meetup

## 현재 작업 계획: 영상 자막 생성

### 요구사항
- **작업**: 2-5개 영상에서 한국어 자막 생성
- **방식**: Whisper (openai-whisper large-v3) - WSL2 환경
- **교정**: 발표자료(PDF) 기반 전문용어 교정
- **출력**: SRT 형식
- **언어**: 한국어 (추후 영어 번역 고려)
- **진행**: 구체화 필요한 부분은 유저에게 질문

### 진행 단계

| 단계 | 작업 | 상태 |
|------|------|------|
| 1 | 영상 파일 준비 (`2-echo-delta/videos/`에 배치) | 완료 |
| 2 | 각 영상별 자막 생성 | 진행중 |
| 3 | 결과 확인 및 수동 교정 | 대기 |
| 4 | (향후) 영어 번역 | 미정 |

### 자막 생성 현황

| 영상 | 최종 SRT 파일 | 상태 |
|------|--------------|------|
| 건호님 | `meetup_02_건호님_corrected.srt` | 완료 |
| 동훈님 | `meetup_02_동훈님_corrected.srt` | 완료 |
| 동운님 | `meetup_02_동운님_corrected.srt` | 완료 |
| 서진님 | `meetup_02_서진님_cropped_corrected.srt` | 완료 |
| 패널 | - | 대기 |

### 영상-PDF 매칭

| 영상 | 발표자료 |
|------|----------|
| 서진님 발표 | `slides/1-김서진-[251230] AI-Native Company.pdf` |
| 동훈님 발표 | `slides/2-이동훈-myrealtrip-donghoon-ailab.pdf` |
| 동운님 발표 | `slides/3-최동운-계산기 압수 당해서...pdf` |
| 건호님 발표 | `slides/4-신건호-AI Builder Meetup...pdf` |
| 키노트 | `slides/0-정구봉-echo-delta-keynote.pdf` |

### 자막 생성 명령어

```bash
# WSL2 환경에서 venv 활성화 후 실행
source .venv/bin/activate

# 자막 생성 (openai-whisper 사용)
python generate_subtitle.py "2-echo-delta/videos/{영상파일}.mov"


### 환경 설정

- **환경**: WSL2 (Ubuntu on Windows)
- **Python**: .venv 가상환경
- **패키지**:
  - `openai-whisper` (Whisper AI)
  - `torch` (PyTorch)
  - `ffmpeg` (오디오 처리)

### 주의사항

1. **한글 파일명**: macOS/WSL에서 NFD 형식으로 저장됨. 반드시 NFC 정규화 후 비교:
   ```python
   import unicodedata
   filename = unicodedata.normalize('NFC', filename)
   ```
2. **처리 시간**: 10분 영상당 약 15-20분 소요 (large-v3 모델)
3. **메모리**: large-v3 모델은 약 10GB VRAM 필요
4. **다음 단계**:
   - `subtitle_cleaner.py`로 중복/hallucination 제거
   - PDF 참조하여 전문용어 교정

---

## 프로젝트 구조

```
ai-builders-meetup/
├── 2-echo-delta/           # 2회차 밋업
│   ├── slides/             # 발표자료 PDF
│   ├── videos/             # 영상 파일 및 SRT 자막
│   └── speakers/           # 스피커 정보
├── .venv/                  # Python 가상환경
├── generate_subtitle.py    # 자막 생성 스크립트
├── subtitle_cleaner.py     # 자막 정리 스크립트
├── SUBTITLE_DESIGN_GUIDE.md # 자막 하드코딩 ffmpeg/ASS 스타일 가이드
└── .claude/
    └── skills/             # Claude Code Skills
        ├── video-subtitle/ # 자막 생성 스킬
        ├── speaker-guide/  # 스피커 가이드 생성
        ├── clarify/        # 요구사항 구체화
        └── panel-talk-questions/
```

## Skills 사용법

- `/video-subtitle` - 영상 자막 생성 및 교정
- `/speaker-guide` - 스피커 가이드 문서 생성
- `/clarify` - 요구사항 구체화 (질문을 통해 정리)
